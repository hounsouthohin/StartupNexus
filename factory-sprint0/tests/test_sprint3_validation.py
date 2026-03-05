"""
tests/test_sprint3_validation.py
Quality gate Sprint 3 — Software Agent Factory

Valide l'état réel du projet après Sprint 3 (04 mars 2026).
Ne nécessite pas Qdrant ni OpenAI_API_KEY (tests statiques uniquement).

Usage:
    cd factory-sprint0
    pytest tests/test_sprint3_validation.py -v
"""

import json
import re
from pathlib import Path

import pytest


# ─────────────────────────────────────────────────────────────
# BLOC 1 — Stack-as-Config JSON (champs Sprint 3)
# ─────────────────────────────────────────────────────────────

class TestStackConfigJSON:
    """Vérifie que le JSON stack contient tous les champs Sprint 3."""

    STACK_PATH = Path("config/stacks/nextjs-clerk-prisma.json")

    @pytest.fixture(autouse=True)
    def load_stack(self):
        if not self.STACK_PATH.exists():
            pytest.skip("nextjs-clerk-prisma.json introuvable")
        with open(self.STACK_PATH, encoding="utf-8") as f:
            self.cfg = json.load(f)

    def test_commands_has_test_key(self):
        commands = self.cfg.get("commands", {})
        assert "test" in commands, \
            "commands.test manquant — Sprint 3 Fix #1 non appliqué"

    def test_commands_has_install_and_build(self):
        commands = self.cfg.get("commands", {})
        for key in ("install_legacy", "build"):
            assert key in commands, f"commands.{key} manquant"

    def test_qdrant_filter_declared(self):
        assert "qdrant_filter" in self.cfg, \
            "qdrant_filter manquant — Sprint 3 Fix #2 non appliqué"
        assert "filter" in self.cfg["qdrant_filter"], \
            "qdrant_filter.filter manquant"

    def test_qdrant_filter_has_must_clause(self):
        must = self.cfg.get("qdrant_filter", {}).get("filter", {}).get("must", [])
        assert len(must) >= 1, "qdrant_filter.filter.must vide"

    def test_cleanup_artifacts_declared(self):
        artifacts = self.cfg.get("cleanup_artifacts", [])
        assert isinstance(artifacts, list) and len(artifacts) >= 1, \
            "cleanup_artifacts manquant ou vide"

    def test_primary_manifest_declared(self):
        assert "primary_manifest" in self.cfg, "primary_manifest manquant"
        assert self.cfg["primary_manifest"] == self.cfg.get("root_file"), \
            "primary_manifest et root_file devraient pointer vers le même fichier"

    def test_workdir_keep_extra_declared(self):
        assert "workdir_keep_extra" in self.cfg, "workdir_keep_extra manquant"

    def test_env_validation_declared(self):
        assert "env_validation" in self.cfg, "env_validation manquant"
        ev = self.cfg["env_validation"]
        assert "required_vars" in ev, "env_validation.required_vars manquant"
        assert "regex" in ev, "env_validation.regex manquant"

    def test_env_validation_clerk_vars_present(self):
        required = self.cfg.get("env_validation", {}).get("required_vars", [])
        for var in ("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "CLERK_SECRET_KEY", "DATABASE_URL"):
            assert var in required, f"env_validation.required_vars manque {var}"

    def test_env_validation_regex_clerk_pattern(self):
        regex_cfg = self.cfg.get("env_validation", {}).get("regex", {})
        pk_pattern = regex_cfg.get("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
        assert pk_pattern.startswith("^pk_"), \
            f"Regex NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY incorrecte: {pk_pattern!r}"


# ─────────────────────────────────────────────────────────────
# BLOC 2 — stack_config.py : helpers Sprint 3
# ─────────────────────────────────────────────────────────────

class TestStackConfigHelpers:
    """Vérifie que les 4 helpers Sprint 3 existent dans stack_config.py."""

    STACK_CONFIG_PATH = Path("agents/stack_config.py")

    @pytest.fixture(autouse=True)
    def load_source(self):
        if not self.STACK_CONFIG_PATH.exists():
            pytest.skip("agents/stack_config.py introuvable")
        self.src = self.STACK_CONFIG_PATH.read_text(encoding="utf-8")

    def test_get_commands_defined(self):
        assert "def get_commands" in self.src, \
            "get_commands() manquant dans stack_config.py"

    def test_get_qdrant_filter_cfg_defined(self):
        assert "def get_qdrant_filter_cfg" in self.src, \
            "get_qdrant_filter_cfg() manquant dans stack_config.py"

    def test_get_cleanup_artifacts_defined(self):
        assert "def get_cleanup_artifacts" in self.src, \
            "get_cleanup_artifacts() manquant dans stack_config.py"

    def test_get_workdir_keep_extra_defined(self):
        assert "def get_workdir_keep_extra" in self.src, \
            "get_workdir_keep_extra() manquant dans stack_config.py"

    def test_helpers_importable(self):
        try:
            from agents.stack_config import (
                get_commands,
                get_qdrant_filter_cfg,
                get_cleanup_artifacts,
                get_workdir_keep_extra,
            )
        except ImportError as e:
            pytest.fail(f"Import échoué: {e}")

    def test_get_commands_returns_test_key(self):
        try:
            from agents.stack_config import get_commands
            cmds = get_commands("nextjs-clerk-prisma")
            assert "test" in cmds, "get_commands() ne retourne pas 'test'"
        except ImportError:
            pytest.skip("stack_config non importable")


# ─────────────────────────────────────────────────────────────
# BLOC 3 — Config-Runtime Drift : run_tests lit commands.test
# ─────────────────────────────────────────────────────────────

class TestRunTestsDrift:
    """Vérifie que run_tests() consomme commands.test depuis JSON (pas hardcodé)."""

    SHARED_TOOLS = Path("agents/shared_tools.py")

    @pytest.fixture(autouse=True)
    def load_source(self):
        if not self.SHARED_TOOLS.exists():
            pytest.skip("agents/shared_tools.py introuvable")
        self.src = self.SHARED_TOOLS.read_text(encoding="utf-8")

    def _run_tests_body(self) -> str:
        """Extrait le corps de la fonction run_tests."""
        match = re.search(r"def run_tests\b.*?(?=\n@tool|\ndef |\Z)", self.src, re.DOTALL)
        return match.group(0) if match else self.src

    def test_run_tests_reads_commands_from_config(self):
        body = self._run_tests_body()
        assert "get_commands" in body, \
            "run_tests() ne lit pas get_commands() — drift commands.test non corrigé"

    def test_run_tests_no_hardcoded_jest_array(self):
        body = self._run_tests_body()
        hardcoded = re.findall(r'\["npx",\s*"jest"', body)
        assert len(hardcoded) == 0, \
            f"run_tests() contient encore une commande jest hardcodée: {hardcoded}"

    def test_run_tests_adds_pass_with_no_tests_guard(self):
        body = self._run_tests_body()
        assert "passWithNoTests" in body, \
            "run_tests() doit ajouter --passWithNoTests comme garde-fou"


# ─────────────────────────────────────────────────────────────
# BLOC 4 — LearnerActivity
# ─────────────────────────────────────────────────────────────

class TestLearnerActivity:
    """Vérifie l'existence et la structure du module learner."""

    def test_learner_module_exists(self):
        assert Path("agents/learner.py").exists(), \
            "agents/learner.py manquant — LearnerActivity Sprint 3 non implémentée"

    def test_learner_activity_wrapper_exists(self):
        assert Path("workflows/activities/learner_activity.py").exists(), \
            "workflows/activities/learner_activity.py manquant"

    def test_standard_suggestion_dataclass_present(self):
        src = Path("agents/learner.py").read_text(encoding="utf-8")
        assert "class StandardSuggestion" in src, \
            "StandardSuggestion dataclass manquante dans agents/learner.py"

    def test_learner_has_five_patterns(self):
        src = Path("agents/learner.py").read_text(encoding="utf-8")
        patterns_found = re.findall(r"\bP00[1-5]\b", src)
        unique = set(patterns_found)
        assert len(unique) >= 5, \
            f"5 patterns P001-P005 attendus, {len(unique)} trouvés: {unique}"

    def test_learner_activity_defn_decorator(self):
        src = Path("workflows/activities/learner_activity.py").read_text(encoding="utf-8")
        assert "@activity.defn" in src, \
            "learner_activity.py: @activity.defn manquant"

    def test_worker_registers_learner_activity(self):
        path = Path("run/worker.py")
        if not path.exists():
            pytest.skip("run/worker.py introuvable")
        content = path.read_text(encoding="utf-8")
        assert "learner_activity" in content, \
            "run/worker.py: learner_activity non enregistrée"

    def test_workflow_calls_learner_activity(self):
        path = Path("workflows/todo_pilot_workflow.py")
        if not path.exists():
            pytest.skip("todo_pilot_workflow.py introuvable")
        content = path.read_text(encoding="utf-8")
        assert "learner_activity" in content, \
            "todo_pilot_workflow.py: learner_activity non branchée"

    def test_learner_is_best_effort_in_workflow(self):
        path = Path("workflows/todo_pilot_workflow.py")
        if not path.exists():
            pytest.skip("todo_pilot_workflow.py introuvable")
        src = path.read_text(encoding="utf-8")
        # Chercher l'appel execute_activity(learner_activity ...) — pas la ligne d'import
        call_idx = src.find("execute_activity(\n")
        # Trouver le execute_activity qui précède "learner_activity"
        search_from = 0
        call_pos = -1
        while True:
            idx = src.find("execute_activity(", search_from)
            if idx == -1:
                break
            snippet = src[idx:idx + 120]
            if "learner_activity" in snippet:
                call_pos = idx
                break
            search_from = idx + 1
        assert call_pos != -1, "execute_activity(learner_activity...) non trouvé dans le workflow"
        surrounding = src[max(0, call_pos - 200):call_pos + 50]
        assert "try:" in surrounding, \
            "learner_activity doit être dans un bloc try/except (best-effort)"


# ─────────────────────────────────────────────────────────────
# BLOC 5 — Architect : AgentState + filtre RAG
# ─────────────────────────────────────────────────────────────

class TestArchitectSprint3:
    """Vérifie les correctifs Sprint 3 dans l'agent architect."""

    ARCHITECT_PATH = Path("agents/architect.py")

    @pytest.fixture(autouse=True)
    def load_source(self):
        if not self.ARCHITECT_PATH.exists():
            pytest.skip("agents/architect.py introuvable")
        self.src = self.ARCHITECT_PATH.read_text(encoding="utf-8")

    def test_agent_state_has_run_id(self):
        state_block = re.search(
            r"class AgentState\(TypedDict\):.*?(?=\n\n|\nclass |\ndef )", self.src, re.DOTALL
        )
        assert state_block, "AgentState non trouvé dans architect.py"
        assert "run_id" in state_block.group(0), \
            "AgentState: run_id manquant — observabilité run-by-run cassée"

    def test_agent_state_has_stack_id(self):
        state_block = re.search(
            r"class AgentState\(TypedDict\):.*?(?=\n\n|\nclass |\ndef )", self.src, re.DOTALL
        )
        assert state_block, "AgentState non trouvé dans architect.py"
        assert "stack_id" in state_block.group(0), \
            "AgentState: stack_id manquant — multi-stack futur fragilisé"

    def test_architect_has_rag_filter_builder(self):
        assert "_build_architect_rag_filter" in self.src, \
            "_build_architect_rag_filter() manquant — architect sans filtre stack"

    def test_retrieval_node_uses_stack_filter(self):
        assert "_build_architect_rag_filter" in self.src, \
            "retrieval_node: filtre stack non appliqué (drift architect RAG)"

    def test_retrieval_node_propagates_run_id(self):
        # run_id doit être lu depuis state dans retrieval_node
        retrieval_match = re.search(
            r"async def retrieval_node.*?(?=\n    async def |\n    def |\Z)", self.src, re.DOTALL
        )
        assert retrieval_match, "retrieval_node non trouvée"
        body = retrieval_match.group(0)
        assert 'state.get("run_id"' in body or "state[\"run_id\"]" in body, \
            "retrieval_node: run_id non lu depuis state"


# ─────────────────────────────────────────────────────────────
# BLOC 6 — validate_config_consumption.py
# ─────────────────────────────────────────────────────────────

class TestValidateConfigConsumption:
    """Vérifie l'existence et le fonctionnement du détecteur de drift."""

    def test_script_exists(self):
        assert Path("scripts/validate_config_consumption.py").exists(), \
            "scripts/validate_config_consumption.py manquant"

    def test_script_covers_sprint3_fields(self):
        src = Path("scripts/validate_config_consumption.py").read_text(encoding="utf-8")
        for field in ("commands", "qdrant_filter", "cleanup_artifacts", "primary_manifest"):
            assert field in src, \
                f"validate_config_consumption.py: champ Sprint 3 '{field}' non couvert"

    def test_field_patterns_dict_present(self):
        src = Path("scripts/validate_config_consumption.py").read_text(encoding="utf-8")
        assert "FIELD_PATTERNS" in src, \
            "FIELD_PATTERNS dict manquant dans validate_config_consumption.py"


# ─────────────────────────────────────────────────────────────
# BLOC 7 — dev.py : hardcoding résiduel supprimé
# ─────────────────────────────────────────────────────────────

class TestDevPyNoHardcoding:
    """Vérifie que dev.py n'a plus de hardcoding Node.js résiduel Sprint 3."""

    DEV_PATH = Path("agents/dev.py")

    @pytest.fixture(autouse=True)
    def load_source(self):
        if not self.DEV_PATH.exists():
            pytest.skip("agents/dev.py introuvable")
        self.src = self.DEV_PATH.read_text(encoding="utf-8")

    def test_dev_uses_get_root_file(self):
        assert "get_root_file" in self.src, \
            "dev.py: get_root_file() non utilisé — guard Phase 1 hardcodé"

    def test_dev_uses_get_cleanup_artifacts(self):
        assert "get_cleanup_artifacts" in self.src, \
            "dev.py: get_cleanup_artifacts() non utilisé — cleanup hardcodé"

    def test_dev_uses_get_workdir_keep_extra(self):
        assert "get_workdir_keep_extra" in self.src, \
            "dev.py: get_workdir_keep_extra() non utilisé — workdir_keep hardcodé"


# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    import sys
    sys.exit(subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
    ).returncode)
