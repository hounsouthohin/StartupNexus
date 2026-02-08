"""
DevTestAgent - Agent fusionné Dev + Test (Sprints 0.5–3)
Encapsule dev_agent + test_coverage_agent avec validation de contrats.
Prépare la réversibilité vers mode split sans casser le code métier.
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path

from jsonschema import validate, ValidationError

# Agents métier existants
from agents.dev import dev_agent
from agents.test_coverage import test_coverage_agent

logger = logging.getLogger(__name__)


class DevTestAgent:
    def __init__(self):
        self.dev_contract = self._load_contract("dev_agent_contract.json")
        self.test_contract = self._load_contract("test_agent_contract.json")
        logger.info("DevTestAgent chargé — 2 contrats distincts (dev + test)")

    def _load_contract(self, filename: str) -> Dict:
        base_path = Path(__file__).parent.parent # This gets to factory-sprint0
        path = base_path / "schemas" / "contracts" / filename
        if not path.exists():
            raise FileNotFoundError(f"Contrat manquant : {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _validate(self, data: Dict, schema: Dict, phase: str, io_type: str = "input") -> None:
        try:
            validate(instance=data, schema=schema)
            logger.debug(f"Validation {io_type} {phase} OK")
        except ValidationError as e:
            msg = f"Validation {io_type} {phase} échouée : {e.message}"
            logger.error(msg)
            raise ValueError(msg)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("DevTestAgent — démarrage workflow fusionné")

        # ─── Phase Dev ────────────────────────────────────────
        dev_input = {
            "spec": input_data.get("spec"),
            "mermaid": input_data.get("mermaid"),
            "project_name": input_data.get("project_name")
        }
        self._validate(dev_input, self.dev_contract["input_schema"], "Dev", "input")

        try:
            dev_output = dev_agent(**dev_input)
            self._validate(dev_output, self.dev_contract["output_schema"], "Dev", "output")
        except Exception as e:
            logger.exception("Échec phase Dev")
            return self._error_payload("dev", str(e))

        # ─── Phase Test ───────────────────────────────────────
        test_input = {"files": dev_output.get("files", {})}
        self._validate(test_input, self.test_contract["input_schema"], "Test", "input")

        try:
            test_output = test_coverage_agent(**test_input)
            if test_output.get("tests"):
                self._validate(test_output, self.test_contract["output_schema"], "Test", "output")
        except Exception as e:
            logger.warning(f"Échec phase Test (isolated) → {e}")
            test_output = {"tests": {}, "error": str(e), "success": False}

        # ─── Assemblage résultat ─────────────────────────────
        combined = {**dev_output.get("files", {}), **test_output.get("tests", {})}

        result = {
            "dev_output": dev_output,
            "test_output": test_output,
            "combined_files": combined,
            "success": dev_output.get("success", False) and len(test_output.get("tests", {})) > 0,
            "metadata": {
                "total_files": len(combined),
                "mode": "fusion",
                "dev_files_count": len(dev_output.get("files", {})),
                "test_files_count": len(test_output.get("tests", {}))
            }
        }

        logger.info(f"DevTestAgent terminé — {result['metadata']['total_files']} fichiers")
        return result

    def _error_payload(self, failed_phase: str, msg: str) -> Dict:
        return {
            "dev_output": {} if failed_phase == "dev" else None,
            "test_output": {} if failed_phase == "test" else None,
            "combined_files": {},
            "success": False,
            "error": {"phase": failed_phase, "message": msg}
        }

    def health_check(self) -> Dict:
        return {
            "status": "healthy",  # on peut affiner plus tard
            "mode": "fusion",
            "checks": {
                "dev": {"status": "ok"},
                "test": {"status": "ok"}
            }
        }


# Wrapper pour appels simples / Temporal
def dev_test_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return DevTestAgent().run(input_data)