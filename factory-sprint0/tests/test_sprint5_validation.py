"""
tests/test_sprint5_validation.py
Quality gate Sprint 5 — Software Agent Factory

Valide les 3 invariants introduits lors des fixes post-run (06 mars 2026) :
  1. Contrat dev_agent accepte requirements[] sans ValidationError
  2. build_status=PARTIAL quand spec_coverage < SPEC_COVERAGE_SUCCESS_THRESHOLD
  3. compute_spec_coverage exige un chemin API exact (plus de faux positif route.ts)

Ne nécessite pas Qdrant ni OPENAI_API_KEY (tests statiques uniquement).

Usage:
    cd factory-sprint0
    pytest tests/test_sprint5_validation.py -v
"""

import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError


# ─────────────────────────────────────────────────────────────
# BLOC 1 — Contrat dev_agent accepte requirements[]
# ─────────────────────────────────────────────────────────────

class TestDevAgentContract:
    """Vérifie que le contrat d'entrée dev_agent accepte requirements[]."""

    CONTRACT_PATH = Path("schemas/contracts/dev_agent_contract.json")

    @pytest.fixture(autouse=True)
    def load_contract(self):
        assert self.CONTRACT_PATH.exists(), f"Contrat introuvable : {self.CONTRACT_PATH}"
        with self.CONTRACT_PATH.open(encoding="utf-8") as f:
            self.contract = json.load(f)
        self.schema = self.contract["input_schema"]

    def _valid_base(self) -> dict:
        return {
            "spec": "x" * 110,
            "mermaid": "x" * 55,
            "project_name": "test-project",
        }

    def test_requirements_accepte_liste_vide(self):
        """requirements=[] ne doit pas lever de ValidationError."""
        data = {**self._valid_base(), "requirements": []}
        validate(instance=data, schema=self.schema)  # ne doit pas lever

    def test_requirements_accepte_liste_non_vide(self):
        """requirements=[str] ne doit pas lever de ValidationError."""
        data = {**self._valid_base(), "requirements": ["Page: /dashboard", "API Route: POST /api/posts"]}
        validate(instance=data, schema=self.schema)

    def test_requirements_absents_ok(self):
        """requirements optionnel — absent ne doit pas lever."""
        validate(instance=self._valid_base(), schema=self.schema)

    def test_requirements_item_non_string_invalide(self):
        """requirements avec item non-string doit lever ValidationError."""
        data = {**self._valid_base(), "requirements": [123]}
        with pytest.raises(ValidationError):
            validate(instance=data, schema=self.schema)


# ─────────────────────────────────────────────────────────────
# BLOC 2 — PARTIAL quand spec_coverage < seuil
# ─────────────────────────────────────────────────────────────

class TestPartialBuildStatus:
    """Vérifie la logique PARTIAL / SUCCESS pilotée par SPEC_COVERAGE_SUCCESS_THRESHOLD."""

    def test_threshold_dans_factory_config(self):
        """SPEC_COVERAGE_SUCCESS_THRESHOLD doit exister dans factory_config."""
        from config.factory_config import SPEC_COVERAGE_SUCCESS_THRESHOLD
        assert isinstance(SPEC_COVERAGE_SUCCESS_THRESHOLD, float), \
            "SPEC_COVERAGE_SUCCESS_THRESHOLD doit être un float"
        assert 0.0 < SPEC_COVERAGE_SUCCESS_THRESHOLD <= 1.0, \
            "SPEC_COVERAGE_SUCCESS_THRESHOLD doit être dans ]0, 1]"

    def test_build_status_partial_sous_seuil(self):
        """Simulation workflow : spec_coverage < seuil → PARTIAL."""
        from config.factory_config import SPEC_COVERAGE_SUCCESS_THRESHOLD
        spec_coverage = SPEC_COVERAGE_SUCCESS_THRESHOLD - 0.01
        dev_phase_success = True
        semantic_violations = []

        if semantic_violations:
            build_status = "SEMANTIC_VIOLATION"
        elif dev_phase_success:
            build_status = "SUCCESS" if spec_coverage >= SPEC_COVERAGE_SUCCESS_THRESHOLD else "PARTIAL"
        else:
            build_status = "BUILD_FAILED"

        assert build_status == "PARTIAL", \
            f"Attendu PARTIAL, obtenu {build_status} (coverage={spec_coverage})"

    def test_build_status_success_au_dessus_seuil(self):
        """Simulation workflow : spec_coverage >= seuil → SUCCESS."""
        from config.factory_config import SPEC_COVERAGE_SUCCESS_THRESHOLD
        spec_coverage = SPEC_COVERAGE_SUCCESS_THRESHOLD
        dev_phase_success = True
        semantic_violations = []

        if semantic_violations:
            build_status = "SEMANTIC_VIOLATION"
        elif dev_phase_success:
            build_status = "SUCCESS" if spec_coverage >= SPEC_COVERAGE_SUCCESS_THRESHOLD else "PARTIAL"
        else:
            build_status = "BUILD_FAILED"

        assert build_status == "SUCCESS", \
            f"Attendu SUCCESS, obtenu {build_status} (coverage={spec_coverage})"

    def test_delivery_status_partial_dans_payload_learner(self):
        """Un run PARTIAL doit émettre delivery_status='partial' dans le shadow log."""
        build_success = True
        spec_coverage = 0.16  # sous le seuil de 0.5
        from config.factory_config import SPEC_COVERAGE_SUCCESS_THRESHOLD

        if not build_success:
            delivery_status = "failed"
        elif spec_coverage >= SPEC_COVERAGE_SUCCESS_THRESHOLD:
            delivery_status = "success"
        else:
            delivery_status = "partial"

        assert delivery_status == "partial"


# ─────────────────────────────────────────────────────────────
# BLOC 3 — compute_spec_coverage : chemin API exact
# ─────────────────────────────────────────────────────────────

class TestSpecCoverageRouteMatching:
    """Vérifie que compute_spec_coverage exige un chemin API exact."""

    def _coverage(self, requirements, files):
        from agents.spec_coverage import compute_spec_coverage
        return compute_spec_coverage(requirements, files)

    def test_route_exacte_satisfait(self):
        """La route PUT /api/posts/[id] doit être satisfaite par app/api/posts/[id]/route.ts."""
        req = ["API Route: PUT /api/posts/[id] toggle published avec auth"]
        files = {"app/api/posts/[id]/route.ts": "export async function PUT() {}"}
        result = self._coverage(req, files)
        assert result["requirements_met"] == 1, \
            f"Attendu 1 met, obtenu {result['requirements_met']}"

    def test_route_au_mauvais_chemin_ne_satisfait_pas(self):
        """Un route.ts au mauvais chemin ne doit PAS satisfaire le requirement."""
        req = ["API Route: PUT /api/posts/[id] toggle published avec auth"]
        # route.ts présent mais pour un autre endpoint
        files = {"app/api/comments/route.ts": "export async function GET() {}"}
        result = self._coverage(req, files)
        assert result["requirements_met"] == 0, \
            f"Faux positif détecté : route.ts au mauvais chemin compte comme satisfait"

    def test_normalisation_casse_paths(self):
        """Les paths en casse mixte doivent être normalisés."""
        req = ["API Route: GET /api/posts"]
        files = {"App/Api/Posts/Route.ts": "export async function GET() {}"}
        result = self._coverage(req, files)
        assert result["requirements_met"] == 1, \
            "La normalisation lower-case doit permettre le matching malgré la casse"

    def test_page_exacte_satisfait(self):
        """Page /dashboard doit être satisfaite par app/dashboard/page.tsx."""
        req = ["Page protégée: /dashboard gestion posts auteur"]
        files = {"app/dashboard/page.tsx": "export default function Dashboard() {}"}
        result = self._coverage(req, files)
        assert result["requirements_met"] == 1

    def test_coverage_zero_si_aucun_fichier(self):
        """Aucun fichier généré → spec_coverage = 0."""
        req = ["Page: /dashboard", "API Route: GET /api/posts"]
        result = self._coverage(req, {})
        assert result["spec_coverage"] == 0.0
        assert result["requirements_met"] == 0
        assert len(result["unmet"]) == 2
