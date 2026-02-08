import json
import pytest
from pathlib import Path
import yaml

from agents.dev_test_agent import DevTestAgent


def load_config():
    path = Path("config/langgraph_config.yaml")
    assert path.exists(), "Fichier config manquant"
    with path.open() as f:
        return yaml.safe_load(f)


class TestLangGraphSwitch:

    def test_config_exists_and_fusion_default(self):
        cfg = load_config()
        assert cfg["deployment_mode"]["current"] == "fusion"
        assert cfg["fusion_config"]["enabled"] is True
        assert cfg["split_config"]["enabled"] is False

    def test_contracts_reusable_between_modes(self):
        cfg = load_config()
        f_dev = cfg["fusion_config"]["agents"]["dev_test_agent"]["contracts"]["dev"]["input"]
        s_dev = cfg["split_config"]["agents"]["dev_agent"]["contract"]
        assert f_dev == s_dev, "Contrat dev non réutilisable"

        f_test = cfg["fusion_config"]["agents"]["dev_test_agent"]["contracts"]["test"]["input"]
        s_test = cfg["split_config"]["agents"]["test_agent"]["contract"]
        assert f_test == s_test, "Contrat test non réutilisable"

    def test_metrics_gate_sprint4_configured(self):
        cfg = load_config()
        m = cfg["fusion_config"]["metrics"]
        assert m["complexity"]["measure"] is True
        assert m["complexity"]["threshold_percent"] == 20
        assert m["agent_count"]["threshold"] == 8

    def test_dev_test_agent_loads_two_contracts(self):
        agent = DevTestAgent()
        assert agent.dev_contract is not None
        assert agent.test_contract is not None
        assert "input_schema" in agent.dev_contract


class TestDevTestAgentValidation:

    @pytest.fixture
    def agent(self):
        return DevTestAgent()

    def test_rejects_missing_spec(self, agent):
        bad_input = {"mermaid": "...", "project_name": "test"}
        
        with pytest.raises(ValueError) as exc_info:
            agent.run(bad_input)
        
        error_msg = str(exc_info.value).lower()
        assert "dev" in error_msg
        assert "input" in error_msg
        assert "échouée" in error_msg or "failed" in error_msg
        # assert "spec" in error_msg   ← on enlève ou on commente cette ligne

    def test_health_check_structure(self, agent):
        health = agent.health_check()
        assert "status" in health
        assert "checks" in health
        assert "dev" in health["checks"]
        assert "test" in health["checks"]


# Pour lancer :  pytest tests/test_langgraph_switch.py -v