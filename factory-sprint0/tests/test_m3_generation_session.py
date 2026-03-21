"""
Tests M3 — GenerationSessionWorkflow
Vérifie :
1. Sérialisation/désérialisation de GenerationSessionState (survie à continue_as_new)
2. Logique du seuil continue_as_new (CONTINUE_AS_NEW_THRESHOLD)
3. Signal handlers : batch_ready, abort_generation
4. Query handler : state_snapshot
5. Logique aggregate_corrections_activity (seuils confidence)
6. Logique generate_batch_activity (no_more_files, batch_cursor)
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workflows.generation_session_workflow import (
    CONTINUE_AS_NEW_THRESHOLD,
    GenerationSessionState,
    GenerationSessionWorkflow,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_state(**kwargs) -> GenerationSessionState:
    defaults = dict(
        run_id="run_test_001",
        stack_id="nextjs-clerk-prisma",
        project_name="test-app",
        batch_cursor=0,
        completed_files=[],
        corrections_applied=0,
        iteration=0,
        requirements_ref="/tmp/req.json",
        plan_ref="/tmp/plan.json",
    )
    defaults.update(kwargs)
    return GenerationSessionState(**defaults)


def _mk_local_tmpdir() -> str:
    """
    Crée un tmpdir sous le workspace (plus fiable sous Windows CI/local
    que le TMP système qui peut être verrouillé).
    """
    base = os.path.join(os.getcwd(), "tests_tmp")
    os.makedirs(base, exist_ok=True)
    return tempfile.mkdtemp(prefix="m3_", dir=base)


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 1 — Sérialisation GenerationSessionState (continue_as_new)
# ─────────────────────────────────────────────────────────────────────────────

def test_state_roundtrip_empty():
    """Un état vierge survit à asdict() → reconstruit."""
    state = _make_state()
    d = asdict(state)
    restored = GenerationSessionState(
        run_id=d["run_id"],
        stack_id=d["stack_id"],
        project_name=d["project_name"],
        batch_cursor=d["batch_cursor"],
        completed_files=d["completed_files"],
        corrections_applied=d["corrections_applied"],
        iteration=d["iteration"],
        requirements_ref=d["requirements_ref"],
        plan_ref=d["plan_ref"],
    )
    assert restored.run_id == state.run_id
    assert restored.batch_cursor == 0
    assert restored.completed_files == []


def test_state_roundtrip_with_files():
    """completed_files et batch_cursor survivent à asdict() → reconstruit."""
    state = _make_state(
        batch_cursor=7,
        completed_files=["app/page.tsx", "app/api/products/route.ts", "prisma/schema.prisma"],
        corrections_applied=12,
        iteration=7,
    )
    d = asdict(state)
    assert d["batch_cursor"] == 7
    assert len(d["completed_files"]) == 3
    assert d["corrections_applied"] == 12
    assert d["iteration"] == 7

    # Reconstruit depuis le dict (pattern continue_as_new)
    restored = GenerationSessionState(**d)
    assert restored.batch_cursor == 7
    assert restored.completed_files == ["app/page.tsx", "app/api/products/route.ts", "prisma/schema.prisma"]
    assert restored.corrections_applied == 12


def test_state_roundtrip_json_serializable():
    """asdict(state) doit être JSON-sérialisable (Temporal le sérialise en JSON)."""
    state = _make_state(
        batch_cursor=3,
        completed_files=["app/page.tsx", "app/dashboard/page.tsx"],
        corrections_applied=5,
        iteration=3,
    )
    d = asdict(state)
    raw = json.dumps(d)  # ne doit pas lever
    restored = json.loads(raw)
    assert restored["batch_cursor"] == 3
    assert restored["completed_files"][0] == "app/page.tsx"


def test_state_completed_files_no_duplicates_after_roundtrip():
    """Les fichiers dédupliqués restent dédupliqués après sérialisation."""
    files = ["app/page.tsx", "app/api/users/route.ts"]
    state = _make_state(completed_files=files)
    d = asdict(state)
    restored = GenerationSessionState(**d)
    assert len(restored.completed_files) == len(set(restored.completed_files))


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 2 — Logique seuil continue_as_new
# ─────────────────────────────────────────────────────────────────────────────

def test_continue_as_new_threshold_value():
    """CONTINUE_AS_NEW_THRESHOLD doit être > 0 et raisonnable."""
    assert CONTINUE_AS_NEW_THRESHOLD > 0
    assert CONTINUE_AS_NEW_THRESHOLD <= 50  # au-delà → risque historique Temporal


def test_continue_as_new_trigger_logic():
    """La condition iteration % threshold == 0 se déclenche aux bons moments."""
    threshold = CONTINUE_AS_NEW_THRESHOLD
    triggered = [i for i in range(1, threshold * 3 + 1) if i % threshold == 0]
    assert triggered == [threshold, threshold * 2, threshold * 3]
    # Ne se déclenche PAS à iteration=0 (range commence à 1)
    assert 0 not in triggered


def test_continue_as_new_preserves_cursor_increment():
    """Après continue_as_new, le nouveau workflow repart au bon batch_cursor."""
    state = _make_state(batch_cursor=9, iteration=9)
    # Simule l'incrément juste avant le continue_as_new
    state.batch_cursor += 1
    state.iteration += 1
    d = asdict(state)
    restored = GenerationSessionState(**d)
    assert restored.batch_cursor == 10
    assert restored.iteration == 10
    # Devrait déclencher continue_as_new si threshold=10
    if CONTINUE_AS_NEW_THRESHOLD == 10:
        assert restored.iteration % CONTINUE_AS_NEW_THRESHOLD == 0


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 3 — Signal handlers (test unitaire sans Temporal runtime)
# ─────────────────────────────────────────────────────────────────────────────

def test_signal_batch_ready_stores_payload():
    """batch_ready stocke le payload dans _pending_batch."""
    wf = GenerationSessionWorkflow()
    payload = {
        "run_id": "run_001",
        "batch_id": "batch_000",
        "files_count": 3,
        "no_more_files": False,
        "artifact_ref": {"path": "/tmp/files.json"},
    }
    import asyncio
    asyncio.run(wf.batch_ready(payload))
    assert wf._pending_batch == payload
    assert wf._status == "supervising"


def test_signal_batch_ready_empty_payload():
    """batch_ready avec payload None/vide ne crashe pas."""
    wf = GenerationSessionWorkflow()
    import asyncio
    asyncio.run(wf.batch_ready({}))
    assert wf._pending_batch == {}


def test_signal_abort_generation_sets_flag():
    """abort_generation met _abort_requested à True."""
    wf = GenerationSessionWorkflow()
    import asyncio
    asyncio.run(wf.abort_generation("test reason"))
    assert wf._abort_requested is True
    assert wf._status == "aborted"


def test_signal_abort_generation_no_reason():
    """abort_generation sans raison ne crashe pas."""
    wf = GenerationSessionWorkflow()
    import asyncio
    asyncio.run(wf.abort_generation())
    assert wf._abort_requested is True


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 4 — Query handler state_snapshot
# ─────────────────────────────────────────────────────────────────────────────

def test_query_state_snapshot_before_run():
    """state_snapshot sans _state retourne un dict valide avec valeurs par défaut."""
    wf = GenerationSessionWorkflow()
    snap = wf.state_snapshot()
    assert snap["run_id"] == ""
    assert snap["batch_cursor"] == 0
    assert snap["completed_files"] == []
    assert snap["status"] == "waiting_batch"
    assert "pending_corrections" in snap


def test_query_state_snapshot_with_state():
    """state_snapshot avec _state injecté reflète l'état courant."""
    wf = GenerationSessionWorkflow()
    wf._state = _make_state(
        batch_cursor=4,
        completed_files=["app/page.tsx"],
        corrections_applied=7,
        iteration=4,
    )
    wf._status = "supervising"
    wf._pending_corrections = {"must_fix": [], "should_fix": [], "total_fixes": 0}

    snap = wf.state_snapshot()
    assert snap["batch_cursor"] == 4
    assert snap["completed_files"] == ["app/page.tsx"]
    assert snap["corrections_applied"] == 7
    assert snap["status"] == "supervising"
    assert snap["pending_corrections"]["total_fixes"] == 0


def test_query_state_snapshot_is_json_serializable():
    """state_snapshot doit être JSON-sérialisable (Temporal query protocol)."""
    wf = GenerationSessionWorkflow()
    wf._state = _make_state(batch_cursor=2, completed_files=["app/page.tsx"])
    wf._pending_corrections = {"must_fix": [{"file": "app/page.tsx", "fix": "add 'use client'"}]}
    snap = wf.state_snapshot()
    raw = json.dumps(snap)  # ne doit pas lever
    assert json.loads(raw)["batch_cursor"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 5 — aggregate_corrections_activity (logique confidence)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_aggregate_must_fix_threshold(monkeypatch):
    """confidence >= 0.8 → must_fix."""
    from workflows.activities.generation_session_activities import aggregate_corrections_activity

    from workflows.activities import generation_session_activities as gsa
    monkeypatch.setattr(gsa, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(gsa, "_workdir", lambda: ".")
    result = await aggregate_corrections_activity({
        "run_id": "run_001",
        "batch_id": "batch_000",
        "supervisor_results": [
            {
                "supervisor": "conformity",
                "status": "needs_fix",
                "confidence": 0.9,
                "fixes": [{"file": "app/page.tsx", "fix": "add 'use client'"}],
            }
        ],
        "artifact_ref": {},
        "stack_id": "nextjs-clerk-prisma",
    })
    assert len(result["must_fix"]) == 1
    assert len(result["should_fix"]) == 0
    assert result["total_fixes"] == 1


@pytest.mark.asyncio
async def test_aggregate_should_fix_threshold(monkeypatch):
    """0.5 <= confidence < 0.8 → should_fix."""
    from workflows.activities.generation_session_activities import aggregate_corrections_activity

    from workflows.activities import generation_session_activities as gsa
    monkeypatch.setattr(gsa, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(gsa, "_workdir", lambda: ".")
    result = await aggregate_corrections_activity({
        "run_id": "run_001",
        "batch_id": "batch_001",
        "supervisor_results": [
            {
                "supervisor": "security",
                "status": "needs_fix",
                "confidence": 0.65,
                "fixes": [{"file": "app/api/users/route.ts", "fix": "add auth check"}],
            }
        ],
        "artifact_ref": {},
        "stack_id": "nextjs-clerk-prisma",
    })
    assert len(result["must_fix"]) == 0
    assert len(result["should_fix"]) == 1


@pytest.mark.asyncio
async def test_aggregate_below_threshold_ignored(monkeypatch):
    """confidence < 0.5 → ignoré."""
    from workflows.activities.generation_session_activities import aggregate_corrections_activity

    from workflows.activities import generation_session_activities as gsa
    monkeypatch.setattr(gsa, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(gsa, "_workdir", lambda: ".")
    result = await aggregate_corrections_activity({
        "run_id": "run_001",
        "batch_id": "batch_002",
        "supervisor_results": [
            {
                "supervisor": "architecture",
                "status": "needs_fix",
                "confidence": 0.3,
                "fixes": [{"file": "app/page.tsx", "fix": "some minor fix"}],
            }
        ],
        "artifact_ref": {},
        "stack_id": "nextjs-clerk-prisma",
    })
    assert result["total_fixes"] == 0
    assert result["must_fix"] == []
    assert result["should_fix"] == []


@pytest.mark.asyncio
async def test_aggregate_ok_status_ignored(monkeypatch):
    """status='ok' → aucune correction extraite même avec confidence élevée."""
    from workflows.activities.generation_session_activities import aggregate_corrections_activity

    from workflows.activities import generation_session_activities as gsa
    monkeypatch.setattr(gsa, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(gsa, "_workdir", lambda: ".")
    result = await aggregate_corrections_activity({
        "run_id": "run_001",
        "batch_id": "batch_003",
        "supervisor_results": [
            {
                "supervisor": "conformity",
                "status": "ok",
                "confidence": 0.95,
                "fixes": [{"file": "app/page.tsx", "fix": "add 'use client'"}],
            }
        ],
        "artifact_ref": {},
        "stack_id": "nextjs-clerk-prisma",
    })
    assert result["total_fixes"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# BLOC 6 — generate_batch_activity (no_more_files, batch_cursor)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_batch_no_more_files_when_empty_plan(monkeypatch):
    """Plan vide → no_more_files=True dès le premier batch."""
    from workflows.activities.generation_session_activities import generate_batch_activity

    from workflows.activities import generation_session_activities as gsa
    monkeypatch.setattr(gsa, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(gsa, "_workdir", lambda: ".")
    result = await generate_batch_activity({
        "run_id": "run_001",
        "stack_id": "nextjs-clerk-prisma",
        "batch_cursor": 0,
        "completed_files": [],
        "requirements_ref": "",
        "plan_ref": "",
    })
    assert result["no_more_files"] is True
    assert result["files_count"] == 0


@pytest.mark.asyncio
async def test_generate_batch_returns_batch_ready_contract(monkeypatch):
    """Retourne les champs du contrat BatchReady (section 4.1 du doc)."""
    from workflows.activities.generation_session_activities import generate_batch_activity

    from workflows.activities import generation_session_activities as gsa
    plan = {"pages": ["/", "/dashboard"], "api_routes": [], "data_models": []}
    monkeypatch.setattr(gsa, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(gsa, "_workdir", lambda: ".")
    monkeypatch.setattr(gsa, "_read_json", lambda path_value, default: plan if str(path_value) == "plan.json" else default)
    result = await generate_batch_activity({
        "run_id": "run_001",
        "stack_id": "nextjs-clerk-prisma",
        "batch_cursor": 0,
        "completed_files": [],
        "requirements_ref": "",
        "plan_ref": "plan.json",
    })

    required_keys = {"run_id", "batch_id", "artifact_ref", "stack_id",
                     "requirements_ref", "plan_ref", "files_count", "batch_index", "no_more_files"}
    assert required_keys.issubset(result.keys()), f"Clés manquantes: {required_keys - result.keys()}"
    assert result["run_id"] == "run_001"
    assert result["batch_index"] == 0
    assert isinstance(result["artifact_ref"], dict)
    assert "path" in result["artifact_ref"]


@pytest.mark.asyncio
async def test_generate_batch_completed_files_excluded(monkeypatch):
    """Les fichiers déjà dans completed_files ne sont pas reproposés."""
    from workflows.activities.generation_session_activities import generate_batch_activity

    from workflows.activities import generation_session_activities as gsa
    plan = {"pages": ["/", "/dashboard", "/profile"], "api_routes": [], "data_models": []}
    monkeypatch.setattr(gsa, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(gsa, "_workdir", lambda: ".")
    monkeypatch.setattr(gsa, "_read_json", lambda path_value, default: plan if str(path_value) == "plan.json" else default)
    # Premier batch : 3 pages disponibles
    await generate_batch_activity({
        "run_id": "run_001",
        "stack_id": "nextjs-clerk-prisma",
        "batch_cursor": 0,
        "completed_files": [],
        "requirements_ref": "",
        "plan_ref": "plan.json",
    })
    # Deuxième batch : les fichiers du premier sont marqués completed
    # Simuler que tous les fichiers du premier batch sont complétés
    result_2 = await generate_batch_activity({
        "run_id": "run_001",
        "stack_id": "nextjs-clerk-prisma",
        "batch_cursor": 1,
        "completed_files": ["app/page.tsx", "app/dashboard/page.tsx", "app/profile/page.tsx"],
        "requirements_ref": "",
        "plan_ref": "plan.json",
    })

    # Après que tous les fichiers sont completed, no_more_files doit être True
    assert result_2["no_more_files"] is True
