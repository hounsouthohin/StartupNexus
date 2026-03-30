"""
DevTestAgent - Agent fusionné Dev + Test (Sprint 4.6 v2).
Supervision inline multi-agents par fichier.
"""

import json
import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict

from jsonschema import ValidationError, validate

from agents.spec_coverage import compute_spec_coverage
from agents.stack_config import _DEFAULT_STACK_ID
from agents.dev import dev_agent
from agents.test_coverage import test_coverage_agent

logger = logging.getLogger(__name__)


def _match_supervision_routing(
    file_path: str,
    routing: dict[str, list[str]],
) -> list[str]:
    norm = (file_path or "").replace("\\", "/")
    for pattern, supervisors in (routing or {}).items():
        if fnmatch(norm, pattern):
            return supervisors or []
    return []


class DevTestAgent:
    def __init__(self):
        self.dev_contract = self._load_contract("dev_agent_contract.json")
        self.test_contract = self._load_contract("test_agent_contract.json")
        logger.info("DevTestAgent chargé — 2 contrats distincts (dev + test)")

    def _load_contract(self, filename: str) -> Dict:
        base_path = Path(__file__).parent.parent
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
        run_id = input_data.get("run_id", "")
        stack_id = input_data.get("stack_id", _DEFAULT_STACK_ID)
        plan = input_data.get("plan", {}) or {}

        dev_input = {
            "spec": input_data.get("spec"),
            "mermaid": input_data.get("mermaid"),
            "project_name": input_data.get("project_name"),
            "stack_id": stack_id,
            "requirements": input_data.get("requirements", []),
            "spec_validation_status": input_data.get("spec_validation_status", "OK"),
            "spec_unmatched_requirements": input_data.get("spec_unmatched_requirements", []),
        }
        user_flows = input_data.get("user_flows", [])
        self._validate(dev_input, self.dev_contract["input_schema"], "Dev", "input")

        try:
            dev_output = dev_agent(
                spec=dev_input["spec"],
                mermaid=dev_input["mermaid"],
                project_name=dev_input["project_name"],
                stack_id=stack_id,
                requirements=dev_input.get("requirements", []),
                spec_unmatched=dev_input.get("spec_unmatched_requirements", []),
                run_id=run_id,
                plan=plan,
            )
        except Exception as e:
            logger.exception("Échec phase Dev")
            return self._error_payload("dev", str(e))
        try:
            self._validate(dev_output, self.dev_contract["output_schema"], "Dev", "output")
        except Exception as e:
            logger.warning(f"Validation sortie Dev échouée (mode non bloquant): {e}")

        # Les superviseurs sont désormais exécutés inline dans dev.py.
        # Ici on lit uniquement les métriques déjà calculées côté Dev.
        dev_metadata = dict(dev_output.get("metadata", {}) or {})
        supervisor_files_reviewed = int(dev_metadata.get("supervisor_files_reviewed", 0) or 0)
        supervisor_corrections_count = int(dev_metadata.get("supervisor_corrections_count", 0) or 0)
        conformity_score = float(dev_metadata.get("conformity_score", 0.0) or 0.0)
        security_score = float(dev_metadata.get("security_score", 0.0) or 0.0)
        architecture_score = float(dev_metadata.get("architecture_score", 0.0) or 0.0)
        build_corrections_count = int(dev_metadata.get("build_corrections_count", 0) or 0)

        # ── Phase Test ──────────────────────────────────────────────────────
        dev_files = dev_output.get("files", {})
        try:
            from agents.stack_config import load_stack_config

            _templated = load_stack_config(str(stack_id)).get("templated_files", {})
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
                stack_id=str(stack_id),
            )
            if test_output.get("tests"):
                self._validate(test_output, self.test_contract["output_schema"], "Test", "output")
        except Exception as e:
            logger.warning(f"Échec phase Test (isolated) → {e}")
            test_output = {"tests": {}, "error": str(e), "success": False}

        # ── Assemblage résultat ─────────────────────────────────────────────
        combined = {**dev_output.get("files", {}), **test_output.get("tests", {})}
        build_success = bool(dev_output.get("success", False))
        tests_passed = bool(test_output.get("success", False))

        journey_result: dict = {}
        try:
            from agents.journey_validator import validate_user_flows

            journey_result = validate_user_flows(user_flows, combined)
        except Exception as jv_err:
            logger.warning(f"[journey_validator] Erreur non bloquante : {jv_err}")

        coverage_result = compute_spec_coverage(dev_input.get("requirements", []), combined)
        logger.info(
            f"[spec_coverage] {coverage_result['requirements_met']}/{coverage_result['requirements_total']} "
            f"requirements couverts ({coverage_result['spec_coverage']:.0%}) "
            f"| unknown={coverage_result.get('requirements_unknown', 0)}"
        )
        if coverage_result["unmet"]:
            logger.warning(f"[spec_coverage] Requirements non couverts: {coverage_result['unmet']}")
        if coverage_result.get("unknown"):
            logger.info(f"[spec_coverage] Requirements non vérifiables: {coverage_result['unknown']}")

        from config.factory_config import SPEC_COVERAGE_SUCCESS_THRESHOLD

        if build_success and coverage_result["spec_coverage"] < SPEC_COVERAGE_SUCCESS_THRESHOLD:
            unmet_by_category: dict = {"model": [], "page": [], "route": [], "feature": []}
            for req in coverage_result["unmet"]:
                rl = req.lower()
                if "prisma" in rl or "modèle" in rl or "model" in rl:
                    unmet_by_category["model"].append(req)
                elif "route" in rl or "api" in rl or any(
                    m in rl for m in ("get ", "post ", "put ", "patch ", "delete ")
                ):
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
                "metadata": dev_output.get("metadata", {}),
            },
            "test_output": test_output,
            "combined_files": combined,
            "success": build_success,
            "metadata": {
                "total_files": len(combined),
                "mode": "fusion",
                "dev_files_count": len(dev_output.get("files", {})),
                "test_files_count": len(test_output.get("tests", {})),
                "tests_passed": tests_passed,
                "spec_coverage": coverage_result["spec_coverage"],
                "requirements_met": coverage_result["requirements_met"],
                "requirements_unmet": coverage_result.get("requirements_unmet", len(coverage_result["unmet"])),
                "requirements_unknown": coverage_result.get("requirements_unknown", 0),
                "requirements_total": coverage_result["requirements_total"],
                "requirements_unmet_list": coverage_result["unmet"],
                "requirements_unknown_list": coverage_result.get("unknown", []),
                "requirements_unmet_by_category": coverage_result.get("unmet_by_category", {}),
                "spec_validation_status": dev_input.get("spec_validation_status", "OK"),
                "spec_unmatched_count": len(dev_input.get("spec_unmatched_requirements", [])),
                "user_flows_total": journey_result.get("user_flows_total", 0),
                "user_flows_covered": journey_result.get("user_flows_covered", 0),
                "user_flows_coverage": journey_result.get("user_flows_coverage", 1.0),
                "is_useful_app": journey_result.get("is_useful_app", True),
                "supervisor_files_reviewed": supervisor_files_reviewed,
                "supervisor_corrections_count": supervisor_corrections_count,
                "conformity_score": conformity_score,
                "security_score": security_score,
                "architecture_score": architecture_score,
                "build_corrections_count": int(build_corrections_count),
            },
        }

        logger.info(
            f"DevTestAgent terminé — {result['metadata']['total_files']} fichiers, "
            f"spec_coverage={coverage_result['spec_coverage']:.0%}"
        )
        return result

    def _error_payload(self, failed_phase: str, msg: str) -> Dict:
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
            "status": "healthy",
            "mode": "fusion",
            "checks": {"dev": {"status": "ok"}, "test": {"status": "ok"}},
        }


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
