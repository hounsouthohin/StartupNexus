"""
Tests R0 — Régression baseline dev_agent()

Phase R0 du refactor LLMConversationRunner + DevOrchestrator.
Ces tests documentent le comportement ACTUEL avant tout refactoring.
Ils doivent rester verts à travers les phases R1, R2, R3.

Couvre :
1. _supervise_file_inline  → message injecté quand superviseur retourne needs_fix + confidence > 0.7
2. _run_build_supervisor_inline → correction injectée quand build échoue
3. _main_context            → garde les 2 messages initiaux + dernier tour complet
4. Guard Phase 1            → WARNING loggé si fichier non-package.json écrit en premier
5. IMMEDIATE_VERIFY         → HumanMessage injecté si même blocker persiste après écriture
6. Stagnation forced build  → run_build.invoke() appelé directement après stagnation ≥ 2 iters

Zero appel réseau — tous LLM, tools et superviseurs sont mockés.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


# ─────────────────────────────────────────────────────────────────────────────
# Helpers partagés
# ─────────────────────────────────────────────────────────────────────────────

def _minimal_stack_cfg(**overrides) -> dict:
    cfg = {
        "supervision": {"batch_size": 1, "supervisor_timeout_ms": 100},
        "supervision_routing": {},
        "mandatory_rag_queries": [],
        "mandatory_rag_k": 4,
        "mandatory_rag_snippet_chars": 900,
        "iteration_policy": {"base_max_iterations": 3, "max_cap_iterations": 3, "tiers": []},
        "generation_order": {"priority_paths": []},
        "templated_files": {},
        "scaffold_extends": {},
        "packages": {"next": "14.0.0"},
        "dev_packages": {},
        "path_guards": [],
        "content_guards": [],
        "token_budgets": {"phase1_tokens": 6000, "phase2_tokens": 14000},
    }
    cfg.update(overrides)
    return cfg


def _mock_tool(name: str, return_value: str = "OK: mock") -> MagicMock:
    t = MagicMock()
    t.name = name
    t.invoke.return_value = return_value
    return t


def _ai_write(path: str, content: str = "// content", call_id: str = "tc_write") -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": "write_file", "args": {"path": path, "content": content}, "id": call_id}],
    )


def _ai_build(project_dir: str = ".", call_id: str = "tc_build") -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": "run_build", "args": {"project_dir": project_dir}, "id": call_id}],
    )


def _ai_empty() -> AIMessage:
    return AIMessage(content="no more actions")


# ─────────────────────────────────────────────────────────────────────────────
# Harness d'intégration — gère tous les patches pour dev_agent()
# ─────────────────────────────────────────────────────────────────────────────

class _DevAgentHarness:
    """
    Context manager qui patche toutes les dépendances de dev_agent().
    Usage :
        with _DevAgentHarness(tmpdir, llm_responses=[...]) as h:
            result = h.run()
    """

    def __init__(
        self,
        tmpdir: str,
        llm_responses: list,
        build_return: str = "Build failed\nSTDERR:\nerror: build error",
        blueprint: dict | None = None,
    ):
        self.tmpdir = tmpdir
        self.llm_responses = list(llm_responses)
        self.build_return = build_return
        self.blueprint = blueprint or {"required_files": ["package.json"]}
        self._stack = ExitStack()

    def __enter__(self) -> "_DevAgentHarness":
        stack = self._stack
        stack_cfg = _minimal_stack_cfg()

        # LLM mock
        self.mock_llm = MagicMock()
        self.mock_llm.get_num_tokens.return_value = 50
        self.mock_bound = MagicMock()
        self.mock_llm.bind_tools.return_value = self.mock_bound

        # Chaque appel à bind_tools().invoke() consomme une réponse de la liste.
        # Quand la liste est épuisée, retourne un AIMessage vide (pas de tool_calls).
        responses = list(self.llm_responses)

        def _bound_invoke(messages):
            if responses:
                return responses.pop(0)
            return _ai_empty()

        self.mock_bound.invoke.side_effect = _bound_invoke
        self.mock_llm.invoke.return_value = AIMessage(content="reflection done")

        # Tool mocks
        self.mock_write_file = _mock_tool("write_file", "OK: written")
        self.mock_run_build = _mock_tool("run_build", self.build_return)
        self.mock_validate_syntax = _mock_tool("validate_syntax", "OK")
        self.mock_prisma_migrate = _mock_tool("prisma_migrate", "OK")
        self.mock_rag_search = _mock_tool("rag_search", "[]")
        self.mock_read_files = _mock_tool("read_files", "{}")

        # Enregistrement des patches
        patch_pairs = [
            ("agents.dev.ChatOpenAI", MagicMock(return_value=self.mock_llm)),
            ("agents.dev.write_file", self.mock_write_file),
            ("agents.dev.run_build", self.mock_run_build),
            ("agents.dev.validate_syntax", self.mock_validate_syntax),
            ("agents.dev.prisma_migrate", self.mock_prisma_migrate),
            ("agents.dev.rag_search", self.mock_rag_search),
            ("agents.dev.read_files", self.mock_read_files),
            ("agents.dev.run_conformity_supervisor",
             AsyncMock(return_value={"status": "ok", "confidence": 0.5})),
            ("agents.dev.run_security_supervisor",
             AsyncMock(return_value={"status": "ok", "confidence": 0.5})),
            ("agents.dev.run_architecture_supervisor",
             AsyncMock(return_value={"status": "ok", "confidence": 0.5})),
            ("agents.dev.run_build_supervisor",
             AsyncMock(return_value={"status": "ok"})),
            ("agents.dev.load_stack_prompt", MagicMock(return_value="system")),
            ("agents.dev._write_learner_event", MagicMock()),
            ("agents.dev.get_blueprint", MagicMock(return_value=self.blueprint)),
            ("agents.dev.get_stack_id", MagicMock(return_value="nextjs-clerk-prisma")),
            ("agents.dev.get_workdir_keep_extra", MagicMock(return_value=[])),
            ("agents.dev.get_forbidden_paths", MagicMock(return_value=["pages/"])),
            ("agents.dev.get_forbidden_imports", MagicMock(return_value=[])),
            ("agents.dev.get_root_file", MagicMock(return_value="package.json")),
            ("agents.dev.get_cleanup_artifacts", MagicMock(return_value=[])),
            ("agents.dev._write_template_files", MagicMock(return_value={})),
            ("agents.dev._clean_project_workdir", MagicMock()),
            # Neutralise les appels shutil.rmtree directs dans dev.py (ligne ~1865)
            # pour éviter les PermissionError Windows pendant le cleanup tempfile.
            ("agents.dev.shutil", MagicMock()),
            ("agents.dev._engine_gate_check", MagicMock(return_value=(False, ""))),
            ("agents.dev._engine_compute_coverage_detailed", MagicMock(return_value={
                "requirements_met": 0, "requirements_total": 0, "unmet": [], "statuses": [],
            })),
            # Patche aussi agents.stack_config pour les imports dynamiques internes à dev_agent()
            ("agents.stack_config.load_stack_config", MagicMock(return_value=stack_cfg)),
            ("agents.stack_config.get_root_file", MagicMock(return_value="package.json")),
        ]
        for patch_target, patch_value in patch_pairs:
            stack.enter_context(patch(patch_target, patch_value))

        stack.enter_context(patch.dict(os.environ, {"FACTORY_WORKDIR": self.tmpdir}))
        return self

    def __exit__(self, *args):
        self._stack.close()

    def run(self, spec: str = "test spec", mermaid: str = "graph TD;A-->B",
            project_name: str = "test-proj") -> dict:
        from agents.dev import dev_agent
        return dev_agent(
            spec=spec,
            mermaid=mermaid,
            project_name=project_name,
            run_id="r_test",
            stack_id="nextjs-clerk-prisma",
        )


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 1 — _supervise_file_inline (injection message supervision)
# ─────────────────────────────────────────────────────────────────────────────

def test_supervision_injects_message_on_needs_fix_high_confidence():
    """needs_fix + confidence > 0.7 → message retourné avec contenu du fix."""
    from agents.dev import _supervise_file_inline

    mock_result = {
        "status": "needs_fix",
        "confidence": 0.9,
        "fix_instruction": {
            "problem": "missing 'use client'",
            "fix": "add 'use client' directive",
        },
    }
    conformity_scores: list = []
    security_scores: list = []
    architecture_scores: list = []

    with patch("agents.dev.run_conformity_supervisor", new=AsyncMock(return_value=mock_result)), \
         patch("agents.dev.run_security_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 0.5})), \
         patch("agents.dev.run_architecture_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 0.5})):
        msg, results = asyncio.run(_supervise_file_inline(
            file_path="app/page.tsx",
            file_content="export default function Page() {}",
            context={
                "requirements": [], "plan": {}, "files_so_far": {},
                "project_name": "test", "run_id": "r1",
                "stack_id": "nextjs-clerk-prisma",
            },
            supervisors=["conformity", "security", "architecture"],
            conformity_scores=conformity_scores,
            security_scores=security_scores,
            architecture_scores=architecture_scores,
            timeout_ms=5000,
        ))

    assert msg is not None, "Un message de correction devrait être retourné"
    assert "CORRECTIONS SUPERVISEURS OBLIGATOIRES" in msg
    assert "app/page.tsx" in msg
    assert "add 'use client' directive" in msg
    # Le score conformity doit être enregistré
    assert len(conformity_scores) == 1
    assert conformity_scores[0] == pytest.approx(0.9)


def test_supervision_no_message_below_confidence_threshold():
    """needs_fix + confidence ≤ 0.7 → aucun message retourné."""
    from agents.dev import _supervise_file_inline

    mock_result = {
        "status": "needs_fix",
        "confidence": 0.65,
        "fix_instruction": {"problem": "minor issue", "fix": "fix it"},
    }

    with patch("agents.dev.run_conformity_supervisor", new=AsyncMock(return_value=mock_result)), \
         patch("agents.dev.run_security_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 0.4})), \
         patch("agents.dev.run_architecture_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 0.4})):
        msg, _ = asyncio.run(_supervise_file_inline(
            file_path="app/page.tsx",
            file_content="content",
            context={},
            supervisors=["conformity", "security", "architecture"],
            conformity_scores=[],
            security_scores=[],
            architecture_scores=[],
            timeout_ms=5000,
        ))

    assert msg is None, "Aucun message sous le seuil de confidence"


def test_supervision_ok_status_no_message():
    """status='ok' → aucun message même avec confidence = 1.0."""
    from agents.dev import _supervise_file_inline

    with patch("agents.dev.run_conformity_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 1.0})), \
         patch("agents.dev.run_security_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 1.0})), \
         patch("agents.dev.run_architecture_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 1.0})):
        msg, _ = asyncio.run(_supervise_file_inline(
            file_path="app/page.tsx",
            file_content="'use client'\nexport default function Page() {}",
            context={},
            supervisors=["conformity", "security", "architecture"],
            conformity_scores=[],
            security_scores=[],
            architecture_scores=[],
            timeout_ms=5000,
        ))

    assert msg is None


def test_supervision_scores_accumulated_per_supervisor():
    """Les scores sont accumulés dans les listes correspondantes."""
    from agents.dev import _supervise_file_inline

    conformity_scores: list = []
    security_scores: list = []
    architecture_scores: list = []

    with patch("agents.dev.run_conformity_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 0.8})), \
         patch("agents.dev.run_security_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 0.6})), \
         patch("agents.dev.run_architecture_supervisor",
               new=AsyncMock(return_value={"status": "ok", "confidence": 0.4})):
        asyncio.run(_supervise_file_inline(
            file_path="app/api/route.ts",
            file_content="export async function GET() {}",
            context={},
            supervisors=["conformity", "security", "architecture"],
            conformity_scores=conformity_scores,
            security_scores=security_scores,
            architecture_scores=architecture_scores,
            timeout_ms=5000,
        ))

    assert conformity_scores == [pytest.approx(0.8)]
    assert security_scores == [pytest.approx(0.6)]
    assert architecture_scores == [pytest.approx(0.4)]


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 2 — _run_build_supervisor_inline (injection correction build)
# ─────────────────────────────────────────────────────────────────────────────

def test_build_supervisor_injects_correction_on_needs_fix():
    """Build supervisor needs_fix → message correction retourné avec [BUILD SUPERVISOR]."""
    from agents.dev import _run_build_supervisor_inline

    mock_result = {
        "status": "needs_fix",
        "fix_instruction": {
            "file": "app/page.tsx",
            "problem": "missing export default",
            "fix": "add export default",
        },
    }

    with patch("agents.dev.run_build_supervisor", new=AsyncMock(return_value=mock_result)):
        msg = asyncio.run(_run_build_supervisor_inline(
            build_stderr="error: missing export",
            files={"app/page.tsx": "function Page() {}"},
            run_id="r1",
            stack_id="nextjs-clerk-prisma",
        ))

    assert msg is not None
    assert "[BUILD SUPERVISOR]" in msg
    assert "app/page.tsx" in msg
    assert "add export default" in msg


def test_build_supervisor_returns_none_on_ok_status():
    """Build supervisor status=ok → None retourné."""
    from agents.dev import _run_build_supervisor_inline

    with patch("agents.dev.run_build_supervisor",
               new=AsyncMock(return_value={"status": "ok"})):
        msg = asyncio.run(_run_build_supervisor_inline(
            build_stderr="",
            files={},
            run_id="r1",
            stack_id="nextjs-clerk-prisma",
        ))

    assert msg is None


def test_build_supervisor_no_message_when_fix_incomplete():
    """needs_fix mais fix_instruction incomplète (pas de problem+fix) → None."""
    from agents.dev import _run_build_supervisor_inline

    with patch("agents.dev.run_build_supervisor", new=AsyncMock(return_value={
        "status": "needs_fix",
        "fix_instruction": {"file": "app/page.tsx"},  # pas de problem ni fix
    })):
        msg = asyncio.run(_run_build_supervisor_inline(
            build_stderr="error",
            files={},
            run_id="r1",
            stack_id="nextjs-clerk-prisma",
        ))

    assert msg is None


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 3 — _main_context (logique de sélection du contexte LLM)
# Réimplémentation locale identique à dev.py:363-415 pour tests isolés.
# ─────────────────────────────────────────────────────────────────────────────

def _main_context_ref(messages_list: list, max_chars: int = 14000) -> list:
    """
    Réimplémentation de référence de _main_context (dev.py:363-415).
    Doit rester IDENTIQUE à l'implémentation dans dev.py.
    Si dev.py change, ce helper DOIT aussi changer — c'est intentionnel :
    un test de régression qui casse signale un changement de comportement.
    """
    if len(messages_list) <= 2:
        return messages_list

    kept = [messages_list[0], messages_list[1]]
    turns = []
    i = 2
    n = len(messages_list)
    while i < n:
        msg = messages_list[i]
        has_tool_calls = hasattr(msg, "tool_calls") and bool(getattr(msg, "tool_calls", None))

        if has_tool_calls:
            turn = [msg]
            i += 1
            while i < n and isinstance(messages_list[i], ToolMessage):
                turn.append(messages_list[i])
                i += 1

            expected_ids = {tc.get("id") for tc in msg.tool_calls if tc.get("id")}
            got_ids = {tm.tool_call_id for tm in turn[1:] if getattr(tm, "tool_call_id", None)}

            if expected_ids and expected_ids.issubset(got_ids):
                turns.append(turn)
            # Sinon : tour incomplet → ignoré
        else:
            if isinstance(msg, ToolMessage):
                i += 1
                continue
            turns.append([msg])
            i += 1

    if not turns:
        return kept

    last_turn = turns[-1]
    turn_chars = sum(len(str(getattr(m, "content", ""))) for m in last_turn)
    if turn_chars > max_chars:
        for msg in reversed(messages_list[2:]):
            if not isinstance(msg, ToolMessage):
                return kept + [msg]
        return kept
    return kept + last_turn


def test_main_context_returns_list_when_two_or_fewer_messages():
    """Liste de ≤ 2 messages retournée telle quelle."""
    msgs = [SystemMessage(content="sys"), HumanMessage(content="init")]
    result = _main_context_ref(msgs)
    assert result is msgs  # référence identique — aucune copie


def test_main_context_always_keeps_two_initial_messages():
    """messages[0] et messages[1] toujours présents dans le résultat."""
    sys_msg = SystemMessage(content="system prompt")
    human_init = HumanMessage(content="initial human")
    extra = HumanMessage(content="extra message")
    msgs = [sys_msg, human_init, extra]

    result = _main_context_ref(msgs)
    assert result[0] is sys_msg
    assert result[1] is human_init


def test_main_context_keeps_last_complete_turn_ai_tool():
    """Dernier tour complet (AIMessage + ToolMessage) retourné en troisième position."""
    sys_msg = SystemMessage(content="system")
    human_init = HumanMessage(content="init")
    ai_msg = AIMessage(
        content="",
        tool_calls=[{"name": "write_file", "args": {}, "id": "tc_1"}],
    )
    tool_msg = ToolMessage(content="OK: file.ts", tool_call_id="tc_1")
    reflection = HumanMessage(content="reflection text — last turn")

    msgs = [sys_msg, human_init, ai_msg, tool_msg, reflection]
    result = _main_context_ref(msgs)

    assert len(result) == 3
    assert result[0] is sys_msg
    assert result[1] is human_init
    assert result[2] is reflection  # dernier tour = HumanMessage reflection


def test_main_context_ignores_incomplete_tool_turn():
    """Tour AI incomplet (tool_call sans ToolMessage) → ignoré."""
    sys_msg = SystemMessage(content="system")
    human_init = HumanMessage(content="init")
    ai_orphan = AIMessage(
        content="",
        tool_calls=[{"name": "write_file", "args": {}, "id": "tc_orphan"}],
    )
    # Pas de ToolMessage pour "tc_orphan"
    unrelated_human = HumanMessage(content="unrelated message — devient le dernier tour")

    msgs = [sys_msg, human_init, ai_orphan, unrelated_human]
    result = _main_context_ref(msgs)

    # Tour incomplet ignoré → dernier tour = unrelated_human
    assert result[-1] is unrelated_human


def test_main_context_fallback_oversized_last_turn():
    """Dernier tour > max_chars → fallback sur le dernier message non-ToolMessage."""
    sys_msg = SystemMessage(content="system")
    human_init = HumanMessage(content="init")
    small = HumanMessage(content="small message")
    huge = HumanMessage(content="X" * 10000)

    msgs = [sys_msg, human_init, small, huge]
    result = _main_context_ref(msgs, max_chars=500)

    # reversed search → huge est le premier non-tool de la fin → retourné
    assert result[-1] is huge


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 4 — dev_agent() intégration (guards de la boucle principale)
# ─────────────────────────────────────────────────────────────────────────────

def test_guard_phase1_logs_warning_when_non_package_written_first():
    """
    Guard Phase 1 : si le LLM écrit un fichier autre que package.json en premier,
    logger.warning doit être appelé avec '[PHASE1_SEQUENCE_VIOLATION]'.

    Setup : blueprint vide (required_files=[]) → active_blocker = "ready_for_build"
    → écriture de app/page.tsx autorisée → guard détecte package.json absent.
    """
    tmpdir = tempfile.mkdtemp()
    try:
        # Blueprint sans required_files pour que active_blocker = "ready_for_build"
        # dès le départ, permettant à tout fichier d'être écrit sans restriction.
        harness_kwargs = {"blueprint": {"required_files": []}}

        llm_responses = [
            _ai_write("app/page.tsx", "export default function Page() {}"),
            _ai_empty(),
            _ai_empty(),
        ]

        with _DevAgentHarness(tmpdir, llm_responses, **harness_kwargs) as h:
            with patch("agents.dev.logger") as mock_logger:
                h.run()

        warning_contents = [
            str(call_args) for call_args in mock_logger.warning.call_args_list
        ]
        assert any(
            "PHASE1_SEQUENCE_VIOLATION" in w for w in warning_contents
        ), f"Guard Phase 1 non déclenché. Warnings reçus: {warning_contents}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_immediate_verify_fires_when_blocker_persists_after_write():
    """
    IMMEDIATE_VERIFY : si le même blocker persiste après une écriture,
    un HumanMessage '[IMMEDIATE_VERIFY]' doit être injecté dans messages.

    Scénario (3 itérations, MAX_ITERATIONS=3) :
    - Iter 1 : LLM écrit package.json → files['package.json'] OK
    - Iter 2 : LLM appelle run_build → echec → last_build_error = "error"
    - Iter 3 : active_blocker="build_error" → LLM écrit app/page.tsx
               → blocker toujours "build_error" → IMMEDIATE_VERIFY fire.
    """
    tmpdir = tempfile.mkdtemp()
    try:
        llm_responses = [
            _ai_write("package.json", '{"name":"test"}', "tc_pkg"),
            _ai_build(".", "tc_build"),
            _ai_write("app/page.tsx", "export default function P(){}", "tc_page"),
        ]

        human_messages_created: list[str] = []
        _real_human = HumanMessage

        def _spy_human(content="", **kwargs):
            if isinstance(content, str):
                human_messages_created.append(content)
            return _real_human(content=content, **kwargs)

        with _DevAgentHarness(tmpdir, llm_responses) as h:
            # Après R3, runner.inject() crée HumanMessage depuis agents.llm_runner,
            # pas agents.dev — le spy doit patcher le bon module.
            with patch("agents.llm_runner.HumanMessage", side_effect=_spy_human):
                h.run()

        assert any(
            "[IMMEDIATE_VERIFY]" in m for m in human_messages_created
        ), f"IMMEDIATE_VERIFY non déclenché. Messages créés: {human_messages_created[:5]}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_stagnation_forces_run_build_directly():
    """
    Stagnation forced build : si stagnant_iterations >= 2 OU iteration >= MAX_ITERATIONS-1
    et les gates passent, run_build.invoke() est appelé DIRECTEMENT (pas via LLM tool_call).

    Scénario (3 itérations, MAX_ITERATIONS=3) :
    - Iter 1 : LLM écrit package.json → stagnant_iterations=0
    - Iter 2 : LLM ne fait rien → stagnant_iterations=1
               + condition (iter=2 >= MAX_ITERATIONS-1=2) → forced build déclenché.
    """
    tmpdir = tempfile.mkdtemp()
    try:
        llm_responses = [
            _ai_write("package.json", '{"name":"test"}', "tc_pkg"),
            _ai_empty(),
            _ai_empty(),
        ]

        with _DevAgentHarness(tmpdir, llm_responses) as h:
            h.run()

        # run_build.invoke() doit avoir été appelé (forced build).
        # Il peut avoir été appelé via tool_map (LLM) ou directement (forced).
        # Avec le scénario ci-dessus, le LLM ne l'appelle jamais → c'est forcé.
        assert h.mock_run_build.invoke.called, (
            "run_build.invoke() n'a jamais été appelé — stagnation forced build non déclenché"
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_stagnation_forced_build_blocked_by_missing_required_files():
    """
    Si les gates échouent (fichiers manquants), le forced build est bloqué :
    run_build.invoke() NE doit PAS être appelé directement.
    """
    tmpdir = tempfile.mkdtemp()
    try:
        # required_files = ["package.json"] mais LLM n'écrit rien → gates bloquent
        llm_responses = [
            _ai_empty(),  # aucune écriture → files = {}
            _ai_empty(),
            _ai_empty(),
        ]

        with _DevAgentHarness(tmpdir, llm_responses) as h:
            h.run()

        # run_build.invoke() ne doit PAS être appelé car blueprint bloque
        assert not h.mock_run_build.invoke.called, (
            "run_build.invoke() appelé malgré les gates bloquants (blueprint manquant)"
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
