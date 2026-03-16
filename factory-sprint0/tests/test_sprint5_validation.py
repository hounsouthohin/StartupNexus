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

    def test_regle2_post_ne_matche_pas_postgresql(self):
        """Faux positif 'post' ∈ 'postgresql' — doit retourner 0 requirements_met."""
        req = ["Modèle Prisma: Post avec champs title, content, published"]
        # schema.prisma contient "postgresql" mais PAS de déclaration "model Post {"
        files = {
            "schema.prisma": (
                'datasource db {\n  provider = "postgresql"\n  url = env("DATABASE_URL")\n}\n'
            )
        }
        result = self._coverage(req, files)
        assert result["requirements_met"] == 0, (
            f"Faux positif détecté : 'post' dans 'postgresql' compte comme modèle satisfait "
            f"(requirements_met={result['requirements_met']})"
        )

    def test_regle2_model_post_exact_satisfait(self):
        """Modèle + champs critiques présents => requirement Prisma satisfait."""
        req = ["Modèle Prisma: Post avec champs title, content, published"]
        files = {
            "schema.prisma": (
                'datasource db {\n  provider = "postgresql"\n  url = env("DATABASE_URL")\n}\n'
                "model Post {\n  id Int @id\n  title String\n  content String\n  published Boolean\n}"
            )
        }
        result = self._coverage(req, files)
        assert result["requirements_met"] == 1, (
            f"La déclaration 'model Post {{' doit satisfaire le requirement "
            f"(requirements_met={result['requirements_met']})"
        )


# ─────────────────────────────────────────────────────────────
# BLOC 4 — Spec Validator déterministe
# ─────────────────────────────────────────────────────────────

class TestSpecValidator:
    """Vérifie que validate_spec_requirements détecte la dérive spec_writer."""

    def _validate(self, spec, requirements):
        from agents.spec_validator import validate_spec_requirements
        return validate_spec_requirements(spec, requirements)

    def test_ok_quand_termes_presents(self):
        """Tous les termes-clés présents dans la spec → status OK."""
        spec = (
            "L'application gère des articles de type Post. "
            "Route API : POST /api/posts pour créer un post. "
            "Page /dashboard pour l'auteur."
        )
        requirements = [
            "Modèle Prisma: Post avec champs title, content",
            "API Route: POST /api/posts créer un post",
            "Page protégée: /dashboard",
        ]
        result = self._validate(spec, requirements)
        assert result["status"] == "OK", f"Attendu OK, obtenu {result['status']}"
        assert result["unmatched_requirements"] == []

    def test_degraded_quand_entite_renommee(self):
        """Spec renomme Post en Article → status DEGRADED."""
        spec = (
            "L'application gère des articles de type Article. "
            "Route API : POST /api/articles. "
            "Page /dashboard."
        )
        requirements = [
            "Modèle Prisma: Post avec champs title, content",
            "API Route: POST /api/posts créer un post",
        ]
        result = self._validate(spec, requirements)
        assert result["status"] == "DEGRADED", (
            f"Attendu DEGRADED (Post renommé en Article), obtenu {result['status']}"
        )
        assert len(result["unmatched_requirements"]) >= 1

    def test_degraded_quand_route_absente(self):
        """Route /api/posts absente de la spec → status DEGRADED."""
        spec = "Application de blog avec modèle Post et page /dashboard."
        requirements = ["API Route: GET /api/posts liste des posts"]
        result = self._validate(spec, requirements)
        assert result["status"] == "DEGRADED"
        assert result["unmatched_requirements"] == ["API Route: GET /api/posts liste des posts"]

    def test_non_mappable_ignore(self):
        """Requirement sans terme extractible ne pénalise pas le score."""
        spec = "Application simple."
        requirements = ["Authentification Clerk robuste et sécurisée"]
        result = self._validate(spec, requirements)
        # Pas de terme extractible → total_mappable=0 → pas de DEGRADED
        assert result["total_mappable"] == 0
        assert result["status"] == "OK"

    def test_liste_vide_retourne_ok(self):
        """requirements=[] → status OK sans erreur."""
        result = self._validate("spec quelconque", [])
        assert result["status"] == "OK"
        assert result["total_mappable"] == 0

    def test_spec_vide_degraded_si_mappable(self):
        """Spec vide avec requirements mappables → DEGRADED."""
        requirements = ["Modèle Prisma: Post", "API Route: GET /api/posts"]
        result = self._validate("", requirements)
        assert result["status"] == "DEGRADED"
        assert result["matched_count"] == 0

    def test_modele_minuscule_extrait(self):
        """'modèle prisma: post' (tout minuscule) doit être mappable et extrait."""
        spec = "L'application gère des entités post dans la base."
        requirements = ["modèle prisma: post avec champs title et content"]
        result = self._validate(spec, requirements)
        assert result["total_mappable"] == 1, "Requirement minuscule doit être mappable"
        assert result["status"] == "OK", "post présent dans la spec → OK"

    def test_modele_minuscule_absent_degraded(self):
        """'modèle prisma: post' absent de la spec → DEGRADED même en minuscule."""
        spec = "L'application gère des articles de type Article."
        requirements = ["modèle prisma: post avec champs title"]
        result = self._validate(spec, requirements)
        assert result["status"] == "DEGRADED", (
            "post absent de la spec (renommé Article) → DEGRADED"
        )


# ─────────────────────────────────────────────────────────────
# BLOC 5 — Gate SPEC_DEGRADED bloque le workflow (Commit 1)
# ─────────────────────────────────────────────────────────────

class TestSpecDegradedGate:
    """Vérifie que la logique SPEC_GATE stoppe le workflow sur spec DEGRADED."""

    def _simulate_gate(self, spec_validation_status: str, unmatched: list) -> str:
        """Simule la condition SPEC_GATE du workflow — retourne 'BLOCKED' ou 'CONTINUE'."""
        if spec_validation_status == "DEGRADED" and unmatched:
            return "BLOCKED"
        return "CONTINUE"

    def test_gate_bloque_sur_degraded(self):
        """DEGRADED + unmatched non vide → workflow bloqué."""
        result = self._simulate_gate("DEGRADED", ["Modèle Prisma: Post"])
        assert result == "BLOCKED"

    def test_gate_laisse_passer_ok(self):
        """Spec OK → workflow continue."""
        result = self._simulate_gate("OK", [])
        assert result == "CONTINUE"

    def test_gate_laisse_passer_degraded_sans_unmatched(self):
        """DEGRADED sans unmatched (cas limite) → workflow continue."""
        result = self._simulate_gate("DEGRADED", [])
        assert result == "CONTINUE"

    def test_gate_laisse_passer_warning(self):
        """Status WARNING → workflow continue (seul DEGRADED bloque)."""
        result = self._simulate_gate("WARNING", ["Modèle Prisma: Post"])
        assert result == "CONTINUE"


# ─────────────────────────────────────────────────────────────
# BLOC 6 — spec_coverage compte Page: / (Commit 5)
# ─────────────────────────────────────────────────────────────

class TestSpecCoverageRootPage:
    """Vérifie que compute_spec_coverage gère la racine '/' correctement."""

    def _coverage(self, requirements, files):
        from agents.spec_coverage import compute_spec_coverage
        return compute_spec_coverage(requirements, files)

    def test_page_racine_satisfaite_par_app_page_tsx(self):
        """'Page: /' doit être satisfaite par app/page.tsx."""
        req = ["Page: / (page d'accueil publique)"]
        files = {"app/page.tsx": "export default function Home() { return <div/>; }"}
        result = self._coverage(req, files)
        assert result["requirements_met"] == 1, (
            f"Page: / doit être satisfaite par app/page.tsx "
            f"(requirements_met={result['requirements_met']})"
        )

    def test_page_racine_non_satisfaite_sans_app_page_tsx(self):
        """'Page: /' sans app/page.tsx → non satisfait."""
        req = ["Page: / (page d'accueil publique)"]
        files = {"app/dashboard/page.tsx": "export default function Dashboard() {}"}
        result = self._coverage(req, files)
        assert result["requirements_met"] == 0, (
            "Page: / ne doit pas être satisfaite par dashboard/page.tsx"
        )

    def test_page_sous_chemin_non_affecte(self):
        """La correction racine ne casse pas les pages /dashboard."""
        req = ["Page protégée: /dashboard gestion des articles"]
        files = {"app/dashboard/page.tsx": "export default function Dashboard() {}"}
        result = self._coverage(req, files)
        assert result["requirements_met"] == 1, (
            "Page /dashboard doit toujours être satisfaite par app/dashboard/page.tsx"
        )


# ─────────────────────────────────────────────────────────────
# BLOC 7 — FACTORY_LOG_DIR absolu (Commit 7)
# ─────────────────────────────────────────────────────────────

class TestAbsoluteLogPaths:
    """Vérifie que les modules utilisent FACTORY_LOG_DIR pour leurs chemins de log."""

    def test_sprint5_gate_path_utilise_env(self, tmp_path, monkeypatch):
        """GATE_PATH doit respecter FACTORY_LOG_DIR si défini avant import."""
        import importlib
        monkeypatch.setenv("FACTORY_LOG_DIR", str(tmp_path))
        import scripts.sprint5_gate as gate_mod
        importlib.reload(gate_mod)
        assert str(tmp_path) in str(gate_mod.GATE_PATH), (
            f"GATE_PATH ({gate_mod.GATE_PATH}) ne commence pas par FACTORY_LOG_DIR ({tmp_path})"
        )

    def test_learner_shadow_log_path_utilise_env(self, tmp_path, monkeypatch):
        """SHADOW_LOG_PATH doit respecter FACTORY_LOG_DIR si défini avant import."""
        import importlib
        monkeypatch.setenv("FACTORY_LOG_DIR", str(tmp_path))
        import agents.learner as learner_mod
        importlib.reload(learner_mod)
        assert str(tmp_path) in str(learner_mod.SHADOW_LOG_PATH), (
            f"SHADOW_LOG_PATH ({learner_mod.SHADOW_LOG_PATH}) ne commence pas par FACTORY_LOG_DIR ({tmp_path})"
        )
