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
from agents.stack_config import _DEFAULT_STACK_ID
from agents.spec_coverage import compute_spec_coverage  # module isolé, testable sans langchain

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
        run_id = input_data.get("run_id", "")
        dev_input = {
            "spec": input_data.get("spec"),
            "mermaid": input_data.get("mermaid"),
            "project_name": input_data.get("project_name"),
            "stack_id": input_data.get("stack_id", _DEFAULT_STACK_ID),
            "requirements": input_data.get("requirements", []),
            "spec_validation_status": input_data.get("spec_validation_status", "OK"),
            "spec_unmatched_requirements": input_data.get("spec_unmatched_requirements", []),
        }
        self._validate(dev_input, self.dev_contract["input_schema"], "Dev", "input")

        try:
            dev_output = dev_agent(
                spec=dev_input["spec"],
                mermaid=dev_input["mermaid"],
                project_name=dev_input["project_name"],
                stack_id=dev_input["stack_id"],
                requirements=dev_input.get("requirements", []),
                spec_unmatched=dev_input.get("spec_unmatched_requirements", []),
                run_id=run_id,
            )
        except Exception as e:
            logger.exception("Échec phase Dev")         
            return self._error_payload("dev", str(e))
        try:
            self._validate(dev_output, self.dev_contract["output_schema"], "Dev", "output")
        except Exception as e:
            # Ne pas jeter un run potentiellement exploitable à cause d'un écart de contrat.
            logger.warning(f"Validation sortie Dev échouée (mode non bloquant): {e}")

        # ─── Phase Test ───────────────────────────────────────
        # Exclure les fichiers d'infrastructure (templated_files) du contexte du
        # test agent : middleware.ts (Edge Runtime), jest.config.js, tsconfig.json,
        # .env.local, etc. ne sont pas des fichiers de logique métier testables en jest.
        dev_files = dev_output.get("files", {})
        try:
            from agents.stack_config import load_stack_config
            _stack_id = str(input_data.get("stack_id", _DEFAULT_STACK_ID))
            _templated = load_stack_config(_stack_id).get("templated_files", {})
            testable_files = {k: v for k, v in dev_files.items() if k not in _templated}
            logger.info(
                f"Test agent — {len(testable_files)}/{len(dev_files)} fichiers testables "
                f"(exclus: {sorted(set(dev_files) - set(testable_files))})"
            )
        except Exception:
            testable_files = dev_files
        test_input = {"files": testable_files}
        self._validate(test_input, self.test_contract["input_schema"], "Test", "input")

        try:
            test_output = test_coverage_agent(
                files=test_input["files"],
                stack_id=str(input_data.get("stack_id", _DEFAULT_STACK_ID)),
            )
            if test_output.get("tests"):
                self._validate(test_output, self.test_contract["output_schema"], "Test", "output")
        except Exception as e:
            logger.warning(f"Échec phase Test (isolated) → {e}")
            test_output = {"tests": {}, "error": str(e), "success": False}

        # ─── Assemblage résultat ─────────────────────────────
        combined = {**dev_output.get("files", {}), **test_output.get("tests", {})}
        build_success = bool(dev_output.get("success", False))
        tests_passed = bool(test_output.get("success", False))

        # ─── Spec Coverage (Sprint 4) ─────────────────────────
        requirements = input_data.get("requirements", [])
        coverage_result = compute_spec_coverage(requirements, combined)
        logger.info(
            f"[spec_coverage] {coverage_result['requirements_met']}/{coverage_result['requirements_total']} "
            f"requirements couverts ({coverage_result['spec_coverage']:.0%})"
        )
        if coverage_result["unmet"]:
            logger.warning(f"[spec_coverage] Requirements non couverts: {coverage_result['unmet']}")

        # Guard : build fonctionnel mais spec_coverage sous le seuil → log critique
        # + tagging des unmet par catégorie pour feedback Learner plus actionnable.
        from config.factory_config import SPEC_COVERAGE_SUCCESS_THRESHOLD
        if build_success and coverage_result["spec_coverage"] < SPEC_COVERAGE_SUCCESS_THRESHOLD:
            unmet_by_category: dict = {"model": [], "page": [], "route": [], "feature": []}
            for req in coverage_result["unmet"]:
                rl = req.lower()
                if "prisma" in rl or "modèle" in rl or "model" in rl:
                    unmet_by_category["model"].append(req)
                elif "route" in rl or "api" in rl or any(m in rl for m in ("get ", "post ", "put ", "patch ", "delete ")):
                    unmet_by_category["route"].append(req)
                elif "page" in rl:
                    unmet_by_category["page"].append(req)
                else:
                    unmet_by_category["feature"].append(req)
            logger.critical(
                f"[spec_coverage] PARTIAL — build ok mais couverture insuffisante "
                f"({coverage_result['spec_coverage']:.0%} < {SPEC_COVERAGE_SUCCESS_THRESHOLD:.0%}). "
                f"Unmet par catégorie: {unmet_by_category}"
            )
            coverage_result["unmet_by_category"] = unmet_by_category

        result = {
            "dev_output": {
                "files": dev_output.get("files", {}),
                "final_message": dev_output.get("final_message", ""),
                "success": dev_output.get("success", False),
                "metadata": dev_output.get("metadata", {}),  # propagé pour run_metric downstream
            },
            "test_output": test_output,
            "combined_files": combined,
            # success = build réussi. Les tests sont un signal qualité non bloquant.
            "success": build_success,
            "metadata": {
                "total_files": len(combined),
                "mode": "fusion",
                "dev_files_count": len(dev_output.get("files", {})),
                "test_files_count": len(test_output.get("tests", {})),
                "tests_passed": tests_passed,
                "spec_coverage": coverage_result["spec_coverage"],
                "requirements_met": coverage_result["requirements_met"],
                "requirements_total": coverage_result["requirements_total"],
                "requirements_unmet": coverage_result["unmet"],
                "requirements_unmet_by_category": coverage_result.get("unmet_by_category", {}),
                # Signal SpecValidator propagé pour observabilité Learner
                "spec_validation_status": dev_input.get("spec_validation_status", "OK"),
                "spec_unmatched_count": len(dev_input.get("spec_unmatched_requirements", [])),
            }
        }

        logger.info(
            f"DevTestAgent terminé — {result['metadata']['total_files']} fichiers, "
            f"spec_coverage={coverage_result['spec_coverage']:.0%}"
        )
        return result

    def _error_payload(self, failed_phase: str, msg: str) -> Dict:
        # Pas de clé 'error' à la racine — output_schema a additionalProperties:false.
        # L'erreur est portée par final_message + success:False.
        return {
            "dev_output": {
                "files": {},
                "final_message": f"[{failed_phase.upper()}_ERROR] {msg}",
                "success": False,
                "metadata": {},
            },
            "test_output": {
                "tests": {},
                "success": False,
            },
            "combined_files": {},
            "metadata": {},
            "success": False,
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
# Recréé si le stack_id change entre deux runs sur le même worker (évite le drift multi-stack).
_DEV_TEST_AGENT_SINGLETON: DevTestAgent | None = None
_DEV_TEST_AGENT_STACK_ID: str = ""


def dev_test_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    global _DEV_TEST_AGENT_SINGLETON, _DEV_TEST_AGENT_STACK_ID
    current_stack = str(input_data.get("stack_id", _DEFAULT_STACK_ID))
    if _DEV_TEST_AGENT_SINGLETON is None or current_stack != _DEV_TEST_AGENT_STACK_ID:
        _DEV_TEST_AGENT_SINGLETON = DevTestAgent()
        _DEV_TEST_AGENT_STACK_ID = current_stack
        logger.info(f"[DevTestAgent] Singleton (re)créé pour stack_id={current_stack}")
    return _DEV_TEST_AGENT_SINGLETON.run(input_data)
