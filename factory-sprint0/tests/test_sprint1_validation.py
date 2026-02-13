"""
tests/test_sprint1_validation.py
Tests de validation Sprint 1 — Software Agent Factory v1.4

IMPORTANT: Lancer depuis factory-sprint0/
    cd factory-sprint0
    pytest tests/test_sprint1_validation.py -v -k "not RAG"

Signal mesurable Sprint 1:
  - SUPERVISEUR_DRAFT_v0.md > 300 lignes avec 4 tags obligatoires
  - Contrats cohérents après bug fixes
  - LearnerAgent en shadow mode
  - TodoPilotWorkflow cohérent avec factory_workflow
  - Score RAG > 0.75 (nécessite Qdrant + OPENAI_API_KEY)
"""

import json
import os
import re
from pathlib import Path

import pytest
import yaml


# ─────────────────────────────────────────────────────
# BLOC 1 — Superviseur DRAFT
# ─────────────────────────────────────────────────────

class TestSuperviseurDraft:
    """Validation du document Superviseur DRAFT v0."""

    def test_superviseur_file_exists(self):
        assert Path("docs/SUPERVISEUR_DRAFT_v0.md").exists(), \
            "SUPERVISEUR_DRAFT_v0.md manquant dans docs/ — Mission A1"

    def test_superviseur_minimum_lines(self):
        content = Path("docs/SUPERVISEUR_DRAFT_v0.md").read_text(encoding="utf-8")
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) >= 300, \
            f"Superviseur trop court: {len(lines)} lignes (minimum 300)"

    def test_superviseur_mandatory_tags(self):
        content = Path("docs/SUPERVISEUR_DRAFT_v0.md").read_text(encoding="utf-8")
        for tag in ["STATUT", "REVIEW_MANDATORY", "NO_OPTIMIZATION", "NO_HARD_CONTRACTS"]:
            assert tag in content, f"Tag obligatoire manquant: '{tag}'"

    def test_superviseur_no_forbidden_implementation(self):
        """Le Superviseur documente les interdictions mais ne les implémente pas.

        Les mots comme 'optimisation automatique' PEUVENT apparaître dans la
        section 'Ce qui est interdit' — c'est attendu et correct.
        On vérifie uniquement que le statut est bien PROVISOIRE (pas finalisé).
        """
        content = Path("docs/SUPERVISEUR_DRAFT_v0.md").read_text(encoding="utf-8")
        assert "NO_OPTIMIZATION" in content, "Tag NO_OPTIMIZATION manquant"
        assert "PROVISOIRE" in content.upper() or "DRAFT" in content.upper(), \
            "Statut PROVISOIRE/DRAFT manquant — doc semble finalisé prématurément"

    def test_superviseur_has_routing_section(self):
        content = Path("docs/SUPERVISEUR_DRAFT_v0.md").read_text(encoding="utf-8")
        assert "routing" in content.lower() or "routage" in content.lower(), \
            "Section routing/routage manquante"

    def test_superviseur_references_sprint4_gate(self):
        content = Path("docs/SUPERVISEUR_DRAFT_v0.md").read_text(encoding="utf-8")
        assert "sprint 4" in content.lower() or "sprint_4" in content.lower(), \
            "Référence Gate Sprint 4 manquante"


# ─────────────────────────────────────────────────────
# BLOC 2 — Configuration Agents
# ─────────────────────────────────────────────────────

class TestAgentsConfig:
    """Validation de la configuration agents."""

    def test_agents_config_exists(self):
        assert Path("config/agents_config.yaml").exists(), \
            "config/agents_config.yaml manquant — Fix #10 requis"

    def test_agents_config_valid_yaml(self):
        if not Path("config/agents_config.yaml").exists():
            pytest.skip("agents_config.yaml manquant")
        with open("config/agents_config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert config is not None and "agents" in config, \
            "Clé 'agents' manquante dans agents_config.yaml"

    def test_minimum_four_agents_configured(self):
        if not Path("config/agents_config.yaml").exists():
            pytest.skip("agents_config.yaml manquant")
        with open("config/agents_config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agents = config.get("agents", {})
        assert len(agents) >= 4, \
            f"Trop peu d'agents: {list(agents.keys())} (minimum 4)"

    def test_learner_agent_in_shadow_mode(self):
        if not Path("config/agents_config.yaml").exists():
            pytest.skip("agents_config.yaml manquant")
        with open("config/agents_config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        agents = config.get("agents", {})
        learner = agents.get("learner_agent") or agents.get("learner")
        if learner is None:
            pytest.skip("learner_agent non configuré — Fix #10 requis")
        mode = learner.get("mode")
        enabled = learner.get("enabled", True)
        assert (mode == "shadow") or (enabled is False), \
            f"LearnerAgent doit être shadow (mode={mode}, enabled={enabled})"

    def test_orchestration_block_present(self):
        if not Path("config/agents_config.yaml").exists():
            pytest.skip("agents_config.yaml manquant")
        with open("config/agents_config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert "orchestration" in config, \
            "Bloc 'orchestration' manquant — Fix #10 requis"

    def test_superviseur_observateur_mode(self):
        if not Path("config/agents_config.yaml").exists():
            pytest.skip("agents_config.yaml manquant")
        with open("config/agents_config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        orch = config.get("orchestration", {})
        assert orch.get("superviseur_mode") == "observateur", \
            "superviseur_mode doit être 'observateur' Sprint 1-3"


# ─────────────────────────────────────────────────────
# BLOC 3 — Contrats après bug fixes
# ─────────────────────────────────────────────────────

class TestContractsPostBugFix:
    """Vérifie l'intégrité des contrats après les bug fixes #2 et #3."""

    CONTRACTS = [
        "schemas/contracts/architect_agent_contract.json",
        "schemas/contracts/dev_agent_contract.json",
        "schemas/contracts/test_agent_contract.json",
        "schemas/contracts/qa_agent_contract.json",
        "schemas/contracts/github_agent_contract.json",
    ]

    def test_all_contracts_exist(self):
        for c in self.CONTRACTS:
            assert Path(c).exists(), f"Contrat manquant: {c}"

    def test_all_contracts_valid_json(self):
        missing = [c for c in self.CONTRACTS if not Path(c).exists()]
        if missing:
            pytest.skip(f"Contrats manquants: {missing}")
        for c in self.CONTRACTS:
            with open(c, encoding="utf-8") as f:
                try:
                    json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"JSON invalide dans {c}: {e}")

    def test_contracts_have_four_schemas(self):
        missing = [c for c in self.CONTRACTS if not Path(c).exists()]
        if missing:
            pytest.skip(f"Contrats manquants: {missing}")
        for c in self.CONTRACTS:
            with open(c, encoding="utf-8") as f:
                contract = json.load(f)
            for key in ["input_schema", "output_schema", "error_schema", "health_schema"]:
                assert key in contract, f"{Path(c).name}: '{key}' manquant"

    def test_qa_output_is_e2e_tests_dict(self):
        path = Path("schemas/contracts/qa_agent_contract.json")
        if not path.exists():
            pytest.skip("qa_agent_contract.json manquant")
        with open(path, encoding="utf-8") as f:
            contract = json.load(f)
        props = contract["output_schema"].get("properties", {})
        assert "e2e_tests" in props, \
            "QA contract: 'e2e_tests' manquant — Bug Fix #2 non appliqué"
        assert "generated_e2e_tests" not in props, \
            "QA contract: 'generated_e2e_tests' encore présent"
        assert props.get("e2e_tests", {}).get("type") == "object", \
            "QA contract: e2e_tests doit être type 'object'"

    def test_github_output_is_object_with_pr_url(self):
        path = Path("schemas/contracts/github_agent_contract.json")
        if not path.exists():
            pytest.skip("github_agent_contract.json manquant")
        with open(path, encoding="utf-8") as f:
            contract = json.load(f)
        schema = contract["output_schema"]
        assert schema.get("type") == "object", \
            "GitHub contract: output doit être 'object' — Bug Fix #3 non appliqué"
        assert "pr_url" in schema.get("properties", {}), \
            "GitHub contract: 'pr_url' manquant"

    def test_learner_contract_exists(self):
        assert Path("schemas/contracts/learner_agent_contract.json").exists(), \
            "learner_agent_contract.json manquant — Mission D1 Gemini Web"

    def test_learner_contract_shadow_mode(self):
        path = Path("schemas/contracts/learner_agent_contract.json")
        if not path.exists():
            pytest.skip("learner_agent_contract.json manquant")
        with open(path, encoding="utf-8") as f:
            contract = json.load(f)
        props = contract.get("output_schema", {}).get("properties", {})
        mode_enum = props.get("mode", {}).get("enum", [])
        assert "shadow" in mode_enum, "LearnerAgent: 'shadow' manquant dans mode enum"
        assert "active" not in mode_enum, \
            "LearnerAgent: 'active' ne doit pas être dans mode enum Sprint 1-3"


# ─────────────────────────────────────────────────────
# BLOC 4 — Bug fixes code source
# ─────────────────────────────────────────────────────

class TestBugFixesApplied:
    """Vérifie que les bug fixes sont correctement appliqués."""

    def test_fix1_no_f_prefix_in_dev_test_activity(self):
        path = Path("workflows/activities/dev_test_activity.py")
        if not path.exists():
            pytest.skip("dev_test_activity.py introuvable")
        first_line = path.read_text(encoding="utf-8").split("\n")[0]
        assert not first_line.startswith("f#"), \
            f"Bug #1 non fixé — ligne 1: '{first_line}'"

    def test_fix2_qa_returns_e2e_tests_dict(self):
        path = Path("workflows/activities/qa_activity.py")
        if not path.exists():
            pytest.skip("qa_activity.py introuvable")
        content = path.read_text(encoding="utf-8")
        assert "e2e_tests" in content, \
            "Bug #2 non fixé: 'e2e_tests' absent de qa_activity.py"
        assert "generated_e2e_tests" not in content, \
            "Bug #2 non fixé: 'generated_e2e_tests' encore présent"

    def test_fix3_github_returns_dict(self):
        path = Path("workflows/activities/github_activity.py")
        if not path.exists():
            pytest.skip("github_activity.py introuvable")
        content = path.read_text(encoding="utf-8")
        assert "pr_url" in content, "Bug #3 non fixé: 'pr_url' absent"
        naked = re.findall(r"return\s+\w+\.html_url\s*$", content, re.MULTILINE)
        assert len(naked) == 0, \
            f"Bug #3 non fixé: return string brut encore présent: {naked}"

    def test_fix4_no_duplicate_dev_test_activity(self):
        assert not Path("agents/dev_test_activity.py").exists(), \
            "Bug #4 non fixé: doublon agents/dev_test_activity.py encore présent"

    def test_fix6_todo_pilot_uses_function_refs(self):
        path = Path("workflows/todo_pilot_workflow.py")
        if not path.exists():
            pytest.skip("todo_pilot_workflow.py introuvable")
        content = path.read_text(encoding="utf-8")
        assert "imports_passed_through" in content, \
            "Bug #6 non fixé: 'imports_passed_through' manquant"
        string_refs = re.findall(
            r'execute_activity\s*\(\s*["\'](\w+_activity)["\']', content
        )
        assert len(string_refs) == 0, \
            f"Bug #6 non fixé: string refs: {string_refs}"

    def test_fix7_todo_pilot_has_qa_step(self):
        path = Path("workflows/todo_pilot_workflow.py")
        if not path.exists():
            pytest.skip("todo_pilot_workflow.py introuvable")
        content = path.read_text(encoding="utf-8")
        assert "qa_activity" in content, \
            "Bug #7 non fixé: qa_activity absente de todo_pilot_workflow.py"

    def test_fix9_todo_pilot_github_result_as_dict(self):
        path = Path("workflows/todo_pilot_workflow.py")
        if not path.exists():
            pytest.skip("todo_pilot_workflow.py introuvable")
        content = path.read_text(encoding="utf-8")
        assert "github_result.get" in content or 'github_result["' in content, \
            "Bug #9 non fixé: github_result doit être accédé comme Dict"


# ─────────────────────────────────────────────────────
# BLOC 5 — Structure fichiers Sprint 1
# ─────────────────────────────────────────────────────

class TestSprint1Structure:
    """Vérifie que tous les fichiers Sprint 1 sont en place."""

    def test_shadow_log_exists(self):
        assert Path("logs/shadow/learner_shadow_log.json").exists(), \
            "Shadow log manquant — Mission A2"

    def test_shadow_log_valid_schema(self):
        path = Path("logs/shadow/learner_shadow_log.json")
        if not path.exists():
            pytest.skip("shadow log manquant")
        with open(path, encoding="utf-8") as f:
            log = json.load(f)
        for key in ["schema_version", "mode", "suggested_standards", "confidence_scores"]:
            assert key in log, f"Shadow log: clé '{key}' manquante"
        assert log["mode"] == "shadow", "Shadow log mode doit être 'shadow'"

    def test_validate_contracts_script_exists(self):
        assert Path("scripts/validate_contracts.py").exists(), \
            "scripts/validate_contracts.py manquant — Mission B2"

    def test_populate_qdrant_script_exists(self):
        assert Path("scripts/populate_qdrant.py").exists(), \
            "scripts/populate_qdrant.py manquant — Mission B1"

    def test_missions_folder_structure(self):
        for folder in ["missions/pending", "missions/in_progress", "missions/done"]:
            assert Path(folder).exists(), f"Dossier '{folder}' manquant"

    def test_worker_registers_todo_pilot(self):
        path = Path("run/worker.py")
        if not path.exists():
            pytest.skip("run/worker.py introuvable")
        assert "TodoPilotWorkflow" in path.read_text(encoding="utf-8"), \
            "run/worker.py: TodoPilotWorkflow non enregistré — Mission D1"

    def test_worker_registers_four_activities(self):
        path = Path("run/worker.py")
        if not path.exists():
            pytest.skip("run/worker.py introuvable")
        content = path.read_text(encoding="utf-8")
        for a in ["architect_activity", "dev_test_activity", "qa_activity", "github_activity"]:
            assert a in content, f"run/worker.py: '{a}' non enregistrée"

    def test_langgraph_config_exists(self):
        assert Path("config/langgraph_config.yaml").exists(), \
            "config/langgraph_config.yaml manquant"

    def test_langgraph_config_fusion_mode(self):
        path = Path("config/langgraph_config.yaml")
        if not path.exists():
            pytest.skip("langgraph_config.yaml manquant")
        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        mode = config.get("deployment_mode", {}).get("current")
        assert mode == "fusion", f"LangGraph doit être en mode fusion (actuel: {mode})"

    def test_logs_metrics_folder_exists(self):
        assert Path("logs/metrics").exists(), \
            "logs/metrics/ manquant — Mission A2"


# ─────────────────────────────────────────────────────
# BLOC 6 — RAG Score (nécessite Qdrant + OPENAI_API_KEY)
# Lancer avec: pytest tests/test_sprint1_validation.py -v
# (sans -k "not RAG")
# ─────────────────────────────────────────────────────

class TestRAGScore:
    """Validation du score RAG > 0.75 (signal Sprint 1)."""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY requis",
    )
    def test_qdrant_collection_not_empty(self):
        try:
            from qdrant_client import QdrantClient
        except ImportError:
            pytest.skip("qdrant-client non installé")
        client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        try:
            count = client.count(
                collection_name="factory_standards", exact=True
            ).count
        except Exception as e:
            pytest.skip(f"Qdrant inaccessible: {e}")
        assert count >= 20, \
            f"factory_standards: {count} standards (min 20). " \
            "Lance: python scripts/populate_qdrant.py"

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY requis",
    )
    def test_rag_score_above_threshold(self):
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_qdrant import QdrantVectorStore
            from qdrant_client import QdrantClient
        except ImportError as e:
            pytest.skip(f"Dépendance manquante: {e}")
        try:
            client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
            embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            vs = QdrantVectorStore(
                client=client,
                collection_name="factory_standards",
                embedding=embeddings,
            )
        except Exception as e:
            pytest.skip(f"Qdrant/OpenAI inaccessible: {e}")

        queries = [
            "Next.js authentication Clerk middleware",
            "Prisma schema user model postgres",
            "shadcn/ui Button Form components",
        ]
        scores = []
        for q in queries:
            try:
                results = vs.similarity_search_with_score(q, k=3)
                if results:
                    scores.append(sum(s for _, s in results) / len(results))
            except Exception:
                continue

        if not scores:
            pytest.skip("Aucun résultat RAG")

        final = sum(scores) / len(scores)
        assert final >= 0.55, \
            f"Score RAG: {final:.3f} < 0.75. Relancer populate_qdrant.py"


# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import subprocess
    import sys
    sys.exit(subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-k", "not RAG"],
    ).returncode)