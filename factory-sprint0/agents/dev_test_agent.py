"""
DevTestAgent - Agent fusionné Dev + Test (Sprints 0.5–3)
Encapsule dev_agent + test_coverage_agent avec validation de contrats.
Prépare la réversibilité vers mode split sans casser le code métier.
"""

import json
import logging
import re
from typing import Dict, Any
from pathlib import Path

from jsonschema import validate, ValidationError
from agents.stack_config import _DEFAULT_STACK_ID

# Agents métier existants
from agents.dev import dev_agent
from agents.test_coverage import test_coverage_agent

logger = logging.getLogger(__name__)


def compute_spec_coverage(requirements: list, combined_files: dict) -> dict:
    """
    Compare requirements[] (Architect) vs combined_files (DevAgent).
    Retourne spec_coverage en pourcentage + liste des requirements non couverts.
    Algorithme déterministe — aucun LLM.
    """
    if not requirements:
        return {"spec_coverage": 0.0, "requirements_met": 0, "requirements_total": 0, "unmet": []}

    file_paths = set(combined_files.keys())

    met, unmet = [], []
    for req in requirements:
        req_lower = req.lower()
        satisfied = False

        # Règle 1 : path explicite dans le requirement (app/..., *.ts, schema.prisma...)
        path_match = re.search(
            r'(app/[\w/\[\].]+\.(tsx?|js|jsx)|[\w-]+\.(ts|tsx|js|prisma|json))',
            req, re.IGNORECASE
        )
        if path_match:
            req_path = path_match.group(1).lower()
            if any(req_path in fp.lower() or fp.lower().endswith(req_path) for fp in file_paths):
                satisfied = True

        # Règle 2 : mention d'un modèle Prisma → vérifier schema.prisma
        if not satisfied and ("modèle prisma" in req_lower or "model prisma" in req_lower or "prisma:" in req_lower):
            model_match = re.search(r':\s*(\w+)', req)
            if model_match:
                model_name = model_match.group(1).lower()
                schema_content = next(
                    (v for k, v in combined_files.items() if "schema.prisma" in k), ""
                )
                if model_name in schema_content.lower():
                    satisfied = True

        # Règle 3 : route API (GET/POST/PUT/PATCH/DELETE /path)
        if not satisfied:
            route_match = re.search(
                r'(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', req, re.IGNORECASE
            )
            if route_match:
                api_path = route_match.group(2).strip('/')
                segments = api_path.split('/')
                expected = 'app/api/' + '/'.join(segments) + '/route.ts'
                if any(expected in fp for fp in file_paths):
                    satisfied = True

        # Règle 4 : page mentionnée (Page: /path ou page publique/protégée)
        if not satisfied and ("page" in req_lower):
            page_match = re.search(r'/[\w/\[\]-]+', req)
            if page_match:
                page_path = page_match.group(0).strip('/')
                if any(page_path in fp for fp in file_paths):
                    satisfied = True

        (met if satisfied else unmet).append(req)

    coverage = round(len(met) / len(requirements), 3) if requirements else 0.0
    return {
        "spec_coverage": coverage,
        "requirements_met": len(met),
        "requirements_total": len(requirements),
        "unmet": unmet,
    }


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
        }
        self._validate(dev_input, self.dev_contract["input_schema"], "Dev", "input")

        try:
            dev_output = dev_agent(
                spec=dev_input["spec"],
                mermaid=dev_input["mermaid"],
                project_name=dev_input["project_name"],
                stack_id=dev_input["stack_id"],
                requirements=dev_input.get("requirements", []),
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

        result = {
            "dev_output": dev_output,
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
            }
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
                "final_message": msg,
                "success": False,
            },  
            "test_output": {
                "tests": {},
                "success": False,
            },
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
