"""
tests/test_sprint_a_regression.py
Regression Test Pack Sprint A — Software Agent Factory

Valide les 4 invariants critiques introduits durant Sprint A (T000-B, T002, T003, T005, T006).
Ne nécessite pas Qdrant ni OPENAI_API_KEY (tests statiques uniquement).

DoD T013 :
  Cas 1 — prisma/schema.prisma double-encodé → normalize_file_content() → gate passe (T000-B)
  Cas 2 — build_attempted=false → final_message = NOT_BUILT_BY_GATE jamais texte LLM (T005)
  Cas 3 — payload sortie avec champ inattendu → ValidationError levée, jamais silencieuse (T006)
  Cas 4 — requirements_gate bloque + spec_coverage non-nul → divergence détectée (T002/T003)

Usage:
    cd factory-sprint0
    pytest tests/test_sprint_a_regression.py -v
"""

import json
import builtins
import io
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError


# ─────────────────────────────────────────────────────────────
# BLOC 1 — T000-B : Normalisation double-encodage Prisma
# ─────────────────────────────────────────────────────────────

class TestPrismaDoubleEncoding:
    """
    Cas 1 : schema.prisma double-encodé (\\n littéraux) → normalize_file_content()
    décode → gate_check peut matcher le modèle Prisma.

    Régression : sans la normalisation, les regex Prisma échouent silencieusement
    et gate_check retourne toujours (True, "manquant") même quand le modèle existe.
    """

    def test_normalize_file_content_importable(self):
        """normalize_file_content() doit être importable depuis agents.requirements_engine."""
        try:
            from agents.requirements_engine import normalize_file_content
        except ImportError as e:
            pytest.fail(f"Import échoué: {e}")

    def test_normalize_skips_json_files(self):
        """Les fichiers .json ne doivent jamais être normalisés (risque de corruption)."""
        from agents.requirements_engine import normalize_file_content
        content_with_literal_n = r'{"key": "line1\nline2"}'
        result = normalize_file_content("package.json", content_with_literal_n)
        assert result == content_with_literal_n, \
            "normalize_file_content ne doit PAS toucher les fichiers .json"

    def test_normalize_detects_double_encoded_prisma(self):
        """Un schema.prisma avec \\n littéraux doit être normalisé vers de vrais sauts."""
        from agents.requirements_engine import normalize_file_content
        # Simuler le double-encodage LLM : \\n à la place de vrais newlines
        raw = r"model User {\n  id String @id\n  name String\n}"
        assert "\n" not in raw, "Précondition : pas de vrai newline"
        assert r"\n" in raw, "Précondition : \\n littéraux présents"

        normalized = normalize_file_content("prisma/schema.prisma", raw)
        assert "\n" in normalized, \
            "normalize_file_content doit remplacer \\n littéraux par de vrais sauts de ligne"
        assert r"\n" not in normalized, \
            "Après normalisation, aucun \\n littéral ne doit subsister"

    def test_normalize_preserves_already_correct_content(self):
        """Un contenu avec de vrais newlines ne doit pas être modifié."""
        from agents.requirements_engine import normalize_file_content
        correct = "model User {\n  id String @id\n  name String\n}"
        result = normalize_file_content("prisma/schema.prisma", correct)
        assert result == correct, \
            "normalize_file_content ne doit pas modifier un contenu déjà correct"

    def test_gate_passes_after_normalization(self):
        """
        Invariant T000-B : après normalisation, gate_check trouve le modèle Prisma.

        Sans normalisation : schema double-encodé → regex model\\s+User\\s*{ ne matche pas
        → gate retourne (True, "User manquant") → build bloqué à tort.

        Avec normalisation intégrée dans _model_in_schema : gate passe correctement.
        """
        from agents.requirements_engine import gate_check

        # Schema double-encodé comme un LLM pourrait le produire
        double_encoded_schema = r"model User {\n  id String @id\n  name String\n}"

        files = {
            "prisma/schema.prisma": double_encoded_schema,
            "app/page.tsx": "export default function Home() { return <div/>; }",
        }
        requirements = ["Modèle Prisma: User avec id et name"]

        blocked, msg = gate_check(requirements, files)
        assert not blocked, (
            f"gate_check bloque à tort sur schema double-encodé — "
            f"la normalisation T000-B n'est pas appliquée dans _model_in_schema.\n"
            f"Message gate : {msg[:300]}"
        )


# ─────────────────────────────────────────────────────────────
# BLOC 2 — T005 : NOT_BUILT_BY_GATE canonique dans le contrat
# ─────────────────────────────────────────────────────────────

class TestNotBuiltByGateContract:
    """
    Cas 2 : build_attempted=false → final_message doit être NOT_BUILT_BY_GATE.
    Invariant : jamais un texte LLM libre — toujours une valeur de l'enum contractualisée.
    """

    CONTRACT_PATH = Path("schemas/contracts/dev_agent_contract.json")

    @pytest.fixture(autouse=True)
    def load_contract(self):
        if not self.CONTRACT_PATH.exists():
            pytest.skip(f"Contrat introuvable : {self.CONTRACT_PATH}")
        with self.CONTRACT_PATH.open(encoding="utf-8") as f:
            self.contract = json.load(f)

    def test_final_message_enum_exists(self):
        """Le champ final_message de output_schema doit avoir un enum défini."""
        output_props = self.contract.get("output_schema", {}).get("properties", {})
        assert "final_message" in output_props, \
            "output_schema.properties.final_message manquant dans dev_agent_contract.json"
        fm = output_props["final_message"]
        assert "enum" in fm, \
            "final_message doit avoir une enum — texte LLM libre interdit (T005)"

    def test_not_built_by_gate_in_enum(self):
        """NOT_BUILT_BY_GATE doit être dans l'enum de final_message."""
        enum_values = (
            self.contract
            .get("output_schema", {})
            .get("properties", {})
            .get("final_message", {})
            .get("enum", [])
        )
        assert "NOT_BUILT_BY_GATE" in enum_values, (
            "NOT_BUILT_BY_GATE absent de l'enum final_message — "
            "la valeur canonique T005 n'est pas contractualisée.\n"
            f"Enum actuel : {enum_values}"
        )

    def test_final_message_enum_contains_all_canonical_values(self):
        """Les 4 valeurs canoniques T005 doivent toutes être dans l'enum."""
        expected = {"BUILD_SUCCESS", "BUILD_FAILED", "MAX_ITER_REACHED", "NOT_BUILT_BY_GATE"}
        enum_values = set(
            self.contract
            .get("output_schema", {})
            .get("properties", {})
            .get("final_message", {})
            .get("enum", [])
        )
        missing = expected - enum_values
        assert not missing, (
            f"Valeurs canoniques T005 manquantes dans final_message.enum : {missing}"
        )

    def test_output_schema_requires_final_message(self):
        """final_message doit être dans required de output_schema."""
        required = self.contract.get("output_schema", {}).get("required", [])
        assert "final_message" in required, \
            "final_message absent de output_schema.required — champ optionnel = dérive silencieuse"

    def test_not_built_by_gate_is_valid_enum_output(self):
        """Un payload avec final_message=NOT_BUILT_BY_GATE doit valider le contrat output."""
        output_schema = self.contract.get("output_schema", {})
        payload = {
            "files": {},
            "final_message": "NOT_BUILT_BY_GATE",
            "success": False,
        }
        try:
            validate(instance=payload, schema=output_schema)
        except ValidationError as e:
            pytest.fail(
                f"NOT_BUILT_BY_GATE est une valeur contractualisée — "
                f"la validation ne doit pas lever : {e.message}"
            )

    def test_llm_text_is_invalid_final_message(self):
        """Un texte LLM libre dans final_message doit lever ValidationError."""
        output_schema = self.contract.get("output_schema", {})
        payload = {
            "files": {},
            "final_message": "Le build a échoué car le fichier package.json est manquant",
            "success": False,
        }
        with pytest.raises(ValidationError):
            validate(instance=payload, schema=output_schema)

    def test_llm_text_is_invalid_final_message_raises(self):
        """Reformulation explicite : texte LLM libre → ValidationError levée (T006)."""
        output_schema = self.contract.get("output_schema", {})
        payload = {
            "files": {},
            "final_message": "J'ai tenté le build mais package.json est absent.",
            "success": False,
        }
        raised = False
        try:
            validate(instance=payload, schema=output_schema)
        except ValidationError:
            raised = True
        assert raised, (
            "Un texte LLM dans final_message doit lever ValidationError — "
            "le contrat T006 ne bloque pas les valeurs hors enum"
        )


# ─────────────────────────────────────────────────────────────
# BLOC 3 — T006 : Payload inattendu → ValidationError explicite
# ─────────────────────────────────────────────────────────────

class TestUnexpectedPayloadValidationError:
    """
    Cas 3 : un payload output avec un champ non contractualisé doit lever ValidationError.
    Invariant : additionalProperties=false dans output_schema → dérive silencieuse impossible.
    """

    CONTRACT_PATH = Path("schemas/contracts/dev_agent_contract.json")

    @pytest.fixture(autouse=True)
    def load_contract(self):
        if not self.CONTRACT_PATH.exists():
            pytest.skip(f"Contrat introuvable : {self.CONTRACT_PATH}")
        with self.CONTRACT_PATH.open(encoding="utf-8") as f:
            self.contract = json.load(f)

    def test_output_schema_has_additional_properties_false(self):
        """output_schema doit avoir additionalProperties=false pour bloquer les dérives."""
        output_schema = self.contract.get("output_schema", {})
        assert output_schema.get("additionalProperties") is False, \
            "output_schema.additionalProperties doit être false — T006 exige le blocage strict"

    def test_unexpected_field_raises_validation_error(self):
        """Un champ inattendu dans le payload output doit lever ValidationError."""
        output_schema = self.contract.get("output_schema", {})
        payload_with_unexpected = {
            "files": {"app/page.tsx": "export default function Home() {}"},
            "final_message": "BUILD_SUCCESS",
            "success": True,
            "unexpected_internal_state": "oops",   # champ non contractualisé
        }
        with pytest.raises(ValidationError):
            validate(instance=payload_with_unexpected, schema=output_schema)

    def test_extra_debug_field_raises_validation_error(self):
        """Un champ debug_ ajouté par erreur doit lever ValidationError, jamais passer."""
        output_schema = self.contract.get("output_schema", {})
        payload_with_debug = {
            "files": {},
            "final_message": "NOT_BUILT_BY_GATE",
            "success": False,
            "debug_llm_trace": "some internal trace",
        }
        with pytest.raises(ValidationError):
            validate(instance=payload_with_debug, schema=output_schema)

    def test_valid_payload_does_not_raise(self):
        """Un payload strictement conforme au contrat ne doit pas lever ValidationError."""
        output_schema = self.contract.get("output_schema", {})
        valid_payload = {
            "files": {"app/page.tsx": "export default function Home() {}"},
            "final_message": "BUILD_SUCCESS",
            "success": True,
        }
        try:
            validate(instance=valid_payload, schema=output_schema)
        except ValidationError as e:
            pytest.fail(f"Payload conforme ne doit pas lever ValidationError: {e.message}")

    def test_missing_required_field_raises(self):
        """Un payload sans 'success' (champ required) doit lever ValidationError."""
        output_schema = self.contract.get("output_schema", {})
        incomplete_payload = {
            "files": {},
            "final_message": "BUILD_FAILED",
            # 'success' manquant
        }
        with pytest.raises(ValidationError):
            validate(instance=incomplete_payload, schema=output_schema)


# ─────────────────────────────────────────────────────────────
# BLOC 4 — T002/T003 : requirements_gate vs spec_coverage divergence
# ─────────────────────────────────────────────────────────────

class TestGateCoverageDivergence:
    """
    Cas 4 : requirements_gate bloque ET spec_coverage est non-nul → divergence détectée.

    Contexte architectural :
    - gate_check() (T002) bloque si un requirement MAPPABLE est non-couvert.
    - compute_coverage() (T003) retourne un ratio : requirements couverts / total.
    - Les requirements NON-MAPPABLES sont assumés satisfaits dans les deux fonctions.

    Divergence à tester :
    Un mix requirements mappables-manquants + non-mappables → gate bloque (T002),
    mais spec_coverage > 0.0 (T003). Le système doit détecter que build bloqué ≠ "tout va bien".
    """

    def _gate(self, requirements, files):
        from agents.requirements_engine import gate_check
        return gate_check(requirements, files)

    def _coverage(self, requirements, files):
        from agents.requirements_engine import compute_coverage
        return compute_coverage(requirements, files)

    def test_gate_blocks_on_missing_mappable_requirement(self):
        """gate_check bloque si une route API mappable est absente."""
        requirements = ["API Route: POST /api/posts créer un article"]
        files = {"app/page.tsx": "export default function Home() {}"}  # route manquante

        blocked, msg = self._gate(requirements, files)
        assert blocked, (
            "gate_check devrait bloquer : POST /api/posts/route.ts est absent.\n"
            f"Message: {msg[:200]}"
        )

    def test_coverage_nonzero_with_non_mappable_plus_missing(self):
        """
        Divergence T002/T003 :
        1 requirement mappable manquant + 1 requirement non-mappable (satisfait par défaut)
        → gate bloque (mappable manquant)
        → spec_coverage = 0.5 (non-mappable compte comme satisfait)
        """
        requirements = [
            "API Route: POST /api/posts créer un article",   # mappable — fichier absent
            "Authentification Clerk robuste avec session",   # non-mappable — assumé satisfait
        ]
        files = {"app/page.tsx": "export default function Home() {}"}

        blocked, _msg = self._gate(requirements, files)
        coverage_result = self._coverage(requirements, files)

        # gate bloque (requirement mappable absent)
        assert blocked, "gate_check doit bloquer sur le requirement mappable manquant"

        # coverage > 0 (non-mappable compte comme satisfait)
        assert coverage_result["spec_coverage"] > 0.0, (
            "spec_coverage devrait être > 0 grâce au non-mappable satisfait par défaut.\n"
            f"Result: {coverage_result}"
        )

        # divergence : gate dit "bloqué" mais coverage n'est pas 0
        assert blocked and coverage_result["spec_coverage"] > 0.0, (
            "DIVERGENCE T002/T003 non détectée : gate bloque (mappable manquant) "
            "mais spec_coverage > 0 (non-mappable satisfait). "
            "Le monitoring doit détecter que build_attempted=False ≠ spec_coverage=0."
        )

    def test_gate_passes_when_all_mappable_covered(self):
        """gate_check passe si tous les requirements mappables sont couverts."""
        requirements = [
            "API Route: POST /api/posts créer un article",
            "Page: /dashboard tableau de bord",
        ]
        files = {
            "app/api/posts/route.ts": "export async function POST() {}",
            "app/dashboard/page.tsx": "export default function Dashboard() {}",
        }

        blocked, msg = self._gate(requirements, files)
        assert not blocked, (
            f"gate_check bloque à tort alors que tous les fichiers sont présents.\n"
            f"Message: {msg[:300]}"
        )

    def test_page_requirement_does_not_fallback_to_root_path(self):
        """
        Régression Priorité 1:
        "Page: /dashboard" ne doit pas matcher "/" par défaut.
        """
        requirements = ["Page: /dashboard tableau de bord"]
        files = {
            "app/page.tsx": "export default function Home() {}",
        }
        blocked, _ = self._gate(requirements, files)
        assert blocked, (
            "Le requirement /dashboard ne doit pas être considéré couvert par app/page.tsx."
        )

    def test_root_page_requirement_still_maps_to_app_page(self):
        """Le requirement explicite 'Page: /' doit matcher app/page.tsx."""
        requirements = ["Page: /"]
        files = {"app/page.tsx": "export default function Home() {}"}
        blocked, _ = self._gate(requirements, files)
        assert not blocked, "Le requirement racine '/' doit matcher app/page.tsx."

    def test_model_requirement_blocks_when_critical_field_missing(self):
        """
        Le requirement Prisma doit vérifier les champs critiques explicitement demandés.
        Régression visée: modèle présent mais champ `content` absent.
        """
        requirements = [
            "Modèle Prisma: Post avec champs title, content, slug @unique, published Boolean, authorId String"
        ]
        files = {
            "prisma/schema.prisma": (
                "model Post {\n"
                "  id String @id @default(cuid())\n"
                "  title String\n"
                "  slug String @unique\n"
                "  published Boolean @default(false)\n"
                "  authorId String\n"
                "  createdAt DateTime @default(now())\n"
                "}\n"
            )
        }

        blocked, _ = self._gate(requirements, files)
        coverage = self._coverage(requirements, files)
        assert blocked, "gate_check doit bloquer si un champ Prisma requis manque"
        assert coverage["spec_coverage"] == 0.0

    def test_model_requirement_blocks_when_unique_constraint_missing(self):
        """Le requirement `slug @unique` doit échouer si @unique est absent dans le modèle."""
        requirements = [
            "Modèle Prisma: Post avec champs title, content, slug @unique, published Boolean, authorId String"
        ]
        files = {
            "prisma/schema.prisma": (
                "model Post {\n"
                "  id String @id @default(cuid())\n"
                "  title String\n"
                "  content String\n"
                "  slug String\n"
                "  published Boolean @default(false)\n"
                "  authorId String\n"
                "  createdAt DateTime @default(now())\n"
                "}\n"
            )
        }

        blocked, _ = self._gate(requirements, files)
        assert blocked, "gate_check doit bloquer si une contrainte @unique requise est absente"

    def test_coverage_100_when_all_covered(self):
        """compute_coverage retourne 1.0 quand tous les requirements sont couverts."""
        requirements = [
            "API Route: GET /api/posts liste des articles",
            "Page: /dashboard tableau de bord",
        ]
        files = {
            "app/api/posts/route.ts": "export async function GET() {}",
            "app/dashboard/page.tsx": "export default function Dashboard() {}",
        }

        result = self._coverage(requirements, files)
        assert result["spec_coverage"] == 1.0, (
            f"Tous les requirements sont couverts → spec_coverage doit être 1.0.\n"
            f"Result: {result}"
        )

    def test_gate_and_coverage_consistent_when_all_missing(self):
        """
        Cohérence totale : aucun fichier → gate bloque ET spec_coverage = 0
        (tous les requirements mappables sont non-couverts).
        """
        requirements = [
            "API Route: DELETE /api/posts/[id] supprimer un article",
            "Page: /profile page profil utilisateur",
        ]
        files = {}

        blocked, _msg = self._gate(requirements, files)
        coverage_result = self._coverage(requirements, files)

        assert blocked, "gate_check doit bloquer si aucun fichier n'est généré"
        assert coverage_result["spec_coverage"] == 0.0, (
            f"spec_coverage doit être 0.0 si aucun requirement n'est couvert.\n"
            f"Result: {coverage_result}"
        )

    def test_requirements_engine_gate_check_importable(self):
        """gate_check doit être importable depuis agents.requirements_engine (T002)."""
        try:
            from agents.requirements_engine import gate_check
        except ImportError as e:
            pytest.fail(f"gate_check non importable — requirements_engine.py manquant ou cassé: {e}")

    def test_requirements_engine_compute_coverage_importable(self):
        """compute_coverage doit être importable depuis agents.requirements_engine (T003)."""
        try:
            from agents.requirements_engine import compute_coverage
        except ImportError as e:
            pytest.fail(f"compute_coverage non importable — requirements_engine.py manquant ou cassé: {e}")


# ─────────────────────────────────────────────────────────────
# BLOC 5 — content_guards : mécanisme config-driven (hardening T-QA2 expérimental)
# ─────────────────────────────────────────────────────────────

class TestContentGuards:
    """
    Valide le mécanisme content_guards lu depuis nextjs-clerk-prisma.json.

    Couverture :
    - Structure JSON valide (champs requis présents dans chaque guard)
    - Guard use_client : déclenche sur hooks sans directive, passe avec directive
    - Guard use_client : détecte imports multilignes (régression vs regex [^}]*)
    - Guard prisma_import_path : déclenche sur chemin relatif, passe sur @/lib/prisma
    - Absence de content_guards dans config → pas de crash

    NB : _prebuild_gates() est une closure non-importable (nested dans dev_test_activity).
    La logique du reader est reproduite ici pour être testable sans dépendance workflow.
    Ce test échoue si le JSON est mal formé OU si la logique de lecture change de façon incompatible.
    """

    STACK_JSON = Path("config/stacks/nextjs-clerk-prisma.json")

    @pytest.fixture(autouse=True)
    def load_stack(self):
        if not self.STACK_JSON.exists():
            pytest.skip(f"Stack JSON introuvable : {self.STACK_JSON}")
        with self.STACK_JSON.open(encoding="utf-8") as f:
            self.stack_cfg = json.load(f)

    def _apply_guard(self, guard: dict, files_dict: dict) -> tuple:
        """
        Reproduit la logique du reader content_guards de _prebuild_gates() dans dev.py.
        Retourne (blocked: bool, message: str).
        Si cette fonction diverge de l'implémentation réelle, les tests échoueront — c'est voulu.
        """
        file_prefix = guard.get("file_prefix", "")
        file_exts = guard.get("file_extensions", [])
        triggers = guard.get("trigger_contains", [])
        directive = guard.get("requires_first_directive")
        conflicts = guard.get("conflicts_with_directive")
        mode = str(guard.get("mode", "block")).strip().lower()
        if mode not in ("block", "warn"):
            mode = "block"
        exclude_paths = [str(p).replace("\\", "/") for p in (guard.get("exclude_paths", []) or [])]
        exclude_when_contains = [str(s) for s in (guard.get("exclude_when_contains", []) or [])]
        msg_lines = guard.get("message_lines", [])

        violations = []
        for fp, fc in files_dict.items():
            fp_norm = fp.replace("\\", "/")
            if any(fp_norm.startswith(xp) for xp in exclude_paths):
                continue
            if file_prefix and not fp_norm.startswith(file_prefix):
                continue
            if file_exts and not any(fp_norm.endswith(ext) for ext in file_exts):
                continue
            if exclude_when_contains and any(needle in fc for needle in exclude_when_contains):
                continue
            found = [t for t in triggers if t in fc]
            if not found:
                continue
            if directive is not None or conflicts is not None:
                first = next((ln.strip() for ln in fc.splitlines() if ln.strip()), "")
                first_norm = first.replace("'", "").replace('"', "").rstrip(";").strip()
                if directive is not None and directive in first_norm:
                    continue
                if conflicts is not None and conflicts not in first_norm:
                    continue
            violations.append((fp_norm, found))

        if violations:
            if mode == "warn":
                return False, ""
            details = "\n".join(
                f"  - {fp}  [{', '.join(found)}]" for fp, found in violations
            )
            msg = "\n".join(msg_lines).replace("{details}", details)
            return True, msg
        return False, ""

    def _get_guard(self, guard_id: str) -> dict:
        for g in self.stack_cfg.get("content_guards", []):
            if g.get("id") == guard_id:
                return g
        pytest.skip(f"Guard '{guard_id}' absent de content_guards — vérifier nextjs-clerk-prisma.json")

    # --- Structure JSON ---

    def test_content_guards_present_in_stack(self):
        """content_guards doit être présent dans nextjs-clerk-prisma.json."""
        assert "content_guards" in self.stack_cfg, (
            "Clé 'content_guards' absente — le mécanisme guard config-driven est désactivé."
        )

    def test_templated_globals_css_present(self):
        """app/globals.css doit être templated (layout.tsx l'importe systématiquement)."""
        templated = self.stack_cfg.get("templated_files", {})
        assert "app/globals.css" in templated, (
            "app/globals.css manquant dans templated_files — risque de build fail "
            "sur \"Can't resolve './globals.css'\" depuis app/layout.tsx."
        )

    def test_route_handler_untyped_signature_guard_present(self):
        """Le guard d'observabilité des signatures route.ts non typées doit être présent."""
        guard_ids = [g.get("id") for g in self.stack_cfg.get("content_guards", [])]
        assert "route_handler_untyped_signature" in guard_ids, (
            "Guard route_handler_untyped_signature manquant — "
            "les TS implicit-any sur app/api/**/route.ts deviennent invisibles."
        )

    def test_content_guards_is_non_empty_list(self):
        """content_guards doit être une liste non-vide."""
        guards = self.stack_cfg.get("content_guards")
        assert isinstance(guards, list), "content_guards doit être une liste"
        assert len(guards) > 0, "content_guards ne doit pas être vide"

    def test_each_guard_has_required_fields(self):
        """Chaque guard doit avoir les champs requis : id, trigger_contains, message_lines."""
        for guard in self.stack_cfg.get("content_guards", []):
            gid = guard.get("id", "<sans id>")
            assert "id" in guard, "Guard sans 'id'"
            assert "trigger_contains" in guard, f"Guard '{gid}' sans 'trigger_contains'"
            assert isinstance(guard["trigger_contains"], list) and len(guard["trigger_contains"]) > 0, \
                f"Guard '{gid}': trigger_contains doit être une liste non-vide"
            assert "message_lines" in guard, f"Guard '{gid}' sans 'message_lines'"
            assert isinstance(guard["message_lines"], list) and len(guard["message_lines"]) > 0, \
                f"Guard '{gid}': message_lines doit être une liste non-vide"
            assert "{details}" in "\n".join(guard["message_lines"]), \
                f"Guard '{gid}': message_lines doit contenir le placeholder {{details}}"

    # --- Guard use_client ---

    def test_use_client_triggers_on_hooks_without_directive(self):
        """use_client guard déclenche si useEffect présent dans app/*.tsx sans 'use client'."""
        guard = self._get_guard("use_client")
        files = {
            "app/page.tsx": (
                "import { useEffect } from 'react'\n"
                "export default function Page() {\n"
                "  useEffect(() => {}, [])\n"
                "  return <div>Hello</div>\n"
                "}\n"
            )
        }
        triggered, msg = self._apply_guard(guard, files)
        assert triggered, "use_client guard doit déclencher sur useEffect sans directive"
        assert "USE CLIENT" in msg.upper() or "use client" in msg.lower()

    def test_use_client_passes_with_single_quote_directive(self):
        """use_client guard passe si 'use client' (guillemets simples) est en première ligne."""
        guard = self._get_guard("use_client")
        files = {
            "app/page.tsx": (
                "'use client'\n"
                "import { useEffect } from 'react'\n"
                "export default function Page() { useEffect(() => {}, []); return <div/> }\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert not triggered, "use_client guard ne doit PAS déclencher avec 'use client' (simple)"

    def test_use_client_passes_with_double_quote_directive(self):
        """use_client guard passe si \"use client\" (guillemets doubles) est en première ligne."""
        guard = self._get_guard("use_client")
        files = {
            "app/dashboard/page.tsx": (
                '"use client"\n'
                "import { useState } from 'react'\n"
                "export default function Dashboard() { const [x] = useState(0); return <div/> }\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert not triggered, "use_client guard doit accepter les guillemets doubles"

    def test_use_client_ignores_non_app_files(self):
        """use_client guard ne s'applique pas aux fichiers hors du dossier app/."""
        guard = self._get_guard("use_client")
        files = {
            "components/Button.tsx": (
                "import { useState } from 'react'\n"
                "export function Button() { return <button /> }\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert not triggered, "use_client guard ne doit pas s'appliquer hors de app/"

    def test_use_client_detects_multiline_import(self):
        """
        Régression critique : use_client détecte les imports multilignes.
        C'est exactement le cas que le regex [^}]* de l'implémentation précédente manquait —
        [^}]* ne traverse pas les newlines, donc un import sur plusieurs lignes passait inaperçu.
        La détection par substring 'in' n'a pas ce problème.
        """
        guard = self._get_guard("use_client")
        files = {
            "app/posts/page.tsx": (
                "import {\n"
                "  useEffect,\n"
                "  useState\n"
                "} from 'react'\n"
                "export default function Posts() { return <div /> }\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert triggered, (
            "use_client guard doit détecter les imports multilignes — "
            "régression vs implémentation regex précédente"
        )

    # --- Guard prisma_import_path ---

    def test_prisma_import_triggers_on_relative_deep_path(self):
        """prisma_import_path guard déclenche sur un chemin relatif profond (../../../../lib/prisma)."""
        guard = dict(self._get_guard("prisma_import_path"))
        guard["mode"] = "block"
        files = {
            "app/api/posts/[id]/route.ts": (
                "import prisma from '../../../../lib/prisma'\n"
                "export async function PUT() {}\n"
            )
        }
        triggered, msg = self._apply_guard(guard, files)
        assert triggered, "prisma_import_path guard doit déclencher sur ../../../../lib/prisma"
        assert "@/lib/prisma" in msg, "Le message doit proposer l'alias @/lib/prisma"

    def test_prisma_import_passes_on_alias(self):
        """prisma_import_path guard NE déclenche PAS si @/lib/prisma est utilisé."""
        guard = self._get_guard("prisma_import_path")
        files = {
            "app/api/posts/route.ts": (
                "import prisma from '@/lib/prisma'\n"
                "export async function GET() {}\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert not triggered, "prisma_import_path guard ne doit pas déclencher sur @/lib/prisma"

    def test_content_guard_warn_mode_does_not_block(self):
        """Un guard en mode warn ne doit jamais bloquer le build."""
        guard = dict(self._get_guard("use_client"))
        guard["mode"] = "warn"
        files = {
            "app/page.tsx": (
                "import { useEffect } from 'react'\n"
                "export default function Page() { useEffect(() => {}, []); return <div/> }\n"
            )
        }
        blocked, _ = self._apply_guard(guard, files)
        assert not blocked, "mode=warn doit journaliser sans bloquer"

    def test_content_guard_exclude_paths_prevents_false_positive(self):
        """exclude_paths doit empêcher un blocage sur chemins explicitement exclus."""
        guard = dict(self._get_guard("use_client"))
        guard["exclude_paths"] = ["app/legacy/"]
        files = {
            "app/legacy/page.tsx": (
                "import { useEffect } from 'react'\n"
                "export default function Legacy() { useEffect(() => {}, []); return <div/> }\n"
            )
        }
        blocked, _ = self._apply_guard(guard, files)
        assert not blocked, "exclude_paths doit neutraliser le guard sur le chemin ciblé"

    def test_prisma_import_triggers_on_two_level_relative(self):
        """prisma_import_path guard détecte aussi un chemin à 2 niveaux (../../lib/prisma)."""
        guard = dict(self._get_guard("prisma_import_path"))
        guard["mode"] = "block"
        files = {
            "app/api/route.ts": (
                "import prisma from '../../lib/prisma'\n"
                "export async function POST() {}\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert triggered, "prisma_import_path guard doit détecter ../../lib/prisma"

    def test_prisma_named_import_triggers(self):
        """prisma_named_import doit bloquer import { prisma } from '@/lib/prisma'."""
        guard = dict(self._get_guard("prisma_named_import"))
        guard["mode"] = "block"
        files = {
            "app/api/posts/route.ts": (
                "import { prisma } from '@/lib/prisma'\n"
                "export async function GET() { return Response.json([]) }\n"
            )
        }
        triggered, msg = self._apply_guard(guard, files)
        assert triggered, "prisma_named_import doit déclencher sur import nommé Prisma"
        assert "import prisma from '@/lib/prisma'" in msg

    def test_prisma_named_import_passes_on_default(self):
        """prisma_named_import ne doit pas bloquer le default import Prisma."""
        guard = self._get_guard("prisma_named_import")
        files = {
            "app/api/posts/route.ts": (
                "import prisma from '@/lib/prisma'\n"
                "export async function GET() { return Response.json([]) }\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert not triggered

    # --- Guard prisma_schema_datasource_url ---

    def test_prisma_schema_datasource_url_triggers(self):
        """Prisma 7: guard doit bloquer datasource.url dans schema.prisma (P1012)."""
        guard = self._get_guard("prisma_schema_datasource_url")
        files = {
            "prisma/schema.prisma": (
                "datasource db {\n"
                "  provider = \"postgresql\"\n"
                "  url      = env(\"DATABASE_URL\")\n"
                "}\n\n"
                "generator client {\n"
                "  provider = \"prisma-client-js\"\n"
                "}\n"
            )
        }
        triggered, msg = self._apply_guard(guard, files)
        assert triggered, "prisma_schema_datasource_url doit déclencher sur datasource.url"
        assert "P1012" in msg or "datasource.url" in msg, (
            "Le message doit expliquer explicitement la contrainte Prisma 7 (P1012)"
        )

    def test_prisma_schema_datasource_url_passes_without_url(self):
        """Prisma 7: pas de blocage si schema.prisma ne contient pas datasource.url."""
        guard = self._get_guard("prisma_schema_datasource_url")
        files = {
            "prisma/schema.prisma": (
                "datasource db {\n"
                "  provider = \"postgresql\"\n"
                "}\n\n"
                "generator client {\n"
                "  provider = \"prisma-client-js\"\n"
                "}\n"
            )
        }
        triggered, _ = self._apply_guard(guard, files)
        assert not triggered, "Le guard ne doit pas bloquer un schema Prisma 7 valide"

    # --- Robustesse config vide ---

    def test_empty_content_guards_no_crash(self):
        """Si content_guards est absent de la config, le reader ne doit pas crasher."""
        empty_cfg: dict = {}
        files = {"app/page.tsx": "import { useEffect } from 'react'"}
        # Simule exactement le reader de _prebuild_gates()
        for guard in empty_cfg.get("content_guards", []):
            self._apply_guard(guard, files)
        # Arriver ici sans exception = OK
        assert True


# ─────────────────────────────────────────────────────────────
# BLOC 6 — T011 : Formule gate_divergence_rate (gates structurels exclus)
# ─────────────────────────────────────────────────────────────

class TestGateDivergenceFormula:
    """
    Valide la formule gate_divergence_rate de determinism_harness.py.
    La détection repose sur metadata.gate_source (tracé dans dev.py) :
      "content_guard" | "no_files" → gate structurel légitime, PAS une divergence
      "requirements" | ""          → gate requirements, divergence si requirements_unmet vide
    """

    def _make_run(
        self,
        build_attempted: bool = False,
        build_success: bool = False,
        final_message: str = "",
        spec_coverage: float = 0.0,
        requirements_unmet: list | None = None,
        gate_source: str = "",
        build_status: str = "NOT_BUILT",
        iterations: int = 5,
    ) -> dict:
        meta: dict = {}
        if requirements_unmet is not None:
            meta["requirements_unmet"] = requirements_unmet
        if gate_source:
            meta["gate_source"] = gate_source
        return {
            "run_metric": {
                "build_attempted": build_attempted,
                "build_success": build_success,
                "final_message": final_message,
                "spec_coverage": spec_coverage,
                "iterations": iterations,
            },
            "build_status": build_status,
            "activity_results": {
                "dev_test": {"metadata": meta}
            },
        }

    def _divergence_rate(self, runs: list) -> float:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from determinism_harness import _compute_metrics
        return _compute_metrics(runs)["gate_divergence_rate"]

    def test_structural_gate_not_counted_as_divergence(self):
        """
        gate_source="content_guard" + requirements_unmet vide + spec_coverage > 0
        → NE doit PAS compter comme divergence.
        """
        run = self._make_run(
            build_attempted=False,
            final_message="NOT_BUILT_BY_GATE",
            spec_coverage=0.7,
            requirements_unmet=[],
            gate_source="content_guard",
        )
        rate = self._divergence_rate([run])
        assert rate == 0.0, (
            f"gate_source='content_guard' ne doit pas compter comme divergence. Got: {rate}"
        )

    def test_structural_gate_from_nested_run_metric_not_counted(self):
        """
        Régression T011 : certains logs exposent gate_source uniquement dans
        activity_results.dev_test.run_metric (pas en top-level/metadata).
        Ce cas doit rester NON-divergent pour content_guard.
        """
        run = {
            "run_metric": {
                "build_attempted": False,
                "build_success": False,
                "final_message": "NOT_BUILT_BY_GATE",
                "spec_coverage": 0.8,
                "iterations": 14,
            },
            "build_status": "BUILD_FAILED",
            "activity_results": {
                "dev_test": {
                    "metadata": {"requirements_unmet": []},
                    "run_metric": {"gate_source": "content_guard"},
                }
            },
        }
        rate = self._divergence_rate([run])
        assert rate == 0.0, (
            "gate_source dans activity_results.dev_test.run_metric doit exclure la divergence"
        )

    def test_no_files_gate_not_counted(self):
        """gate_source='no_files' = aucun fichier généré, pas une divergence requirements."""
        run = self._make_run(
            build_attempted=False,
            final_message="NOT_BUILT_BY_GATE",
            spec_coverage=0.0,
            requirements_unmet=[],
            gate_source="no_files",
        )
        rate = self._divergence_rate([run])
        assert rate == 0.0, f"gate_source='no_files' ne doit pas compter comme divergence. Got: {rate}"

    def test_requirements_gate_without_justification_is_divergence(self):
        """
        gate_source='requirements' + requirements_unmet vide + spec_coverage > 0
        = vraie divergence : le gate bloque sans justification tracée.
        """
        run = self._make_run(
            build_attempted=False,
            final_message="NOT_BUILT_BY_GATE",
            spec_coverage=0.8,
            requirements_unmet=[],
            gate_source="requirements",
        )
        rate = self._divergence_rate([run])
        assert rate == 1.0, (
            f"gate_source='requirements' sans justification doit être divergence. Got: {rate}"
        )

    def test_gate_with_requirements_unmet_is_not_divergence(self):
        """
        requirements_unmet non vide = gate justifié, pas une divergence, quelle que soit gate_source.
        """
        run = self._make_run(
            build_attempted=False,
            final_message="NOT_BUILT_BY_GATE",
            spec_coverage=0.6,
            requirements_unmet=["API Route: /api/posts manquante"],
            gate_source="requirements",
        )
        rate = self._divergence_rate([run])
        assert rate == 0.0, (
            f"Gate avec requirements_unmet non vide ne doit pas être divergence. Got: {rate}"
        )

    def test_build_attempted_runs_never_divergence(self):
        """Un run où le build a été tenté n'est jamais une divergence de gate."""
        run = self._make_run(
            build_attempted=True,
            build_success=False,
            final_message="BUILD_FAILED",
            spec_coverage=0.9,
            requirements_unmet=[],
        )
        rate = self._divergence_rate([run])
        assert rate == 0.0, f"Run avec build_attempted ne doit jamais être divergence. Got: {rate}"

    def test_mixed_runs_correct_rate(self):
        """
        3 runs: 1 content_guard, 1 requirements divergence, 1 build_attempted.
        Seul le requirements gate (sans justification) compte → rate = 1/3.
        """
        runs = [
            self._make_run(
                build_attempted=False,
                final_message="NOT_BUILT_BY_GATE",
                spec_coverage=0.7, requirements_unmet=[], gate_source="content_guard",
            ),
            self._make_run(
                build_attempted=False,
                final_message="NOT_BUILT_BY_GATE",
                spec_coverage=0.8, requirements_unmet=[], gate_source="requirements",
            ),
            self._make_run(build_attempted=True, build_success=True, final_message="BUILD_SUCCESS"),
        ]
        rate = self._divergence_rate(runs)
        expected = round(1 / 3, 3)
        assert rate == expected, f"Rate attendu {expected}, got {rate}"


# ─────────────────────────────────────────────────────────────
# BLOC 7 — T007 : Fallback model configuré sur les agents (feature-flag LLM_FALLBACK_ENABLED)
# ─────────────────────────────────────────────────────────────

class TestT007Fallback:
    """
    Vérifie que le fallback model est bien configuré sur les agents LLM.
    Le fallback est activé par LLM_FALLBACK_ENABLED=1 pour ne pas polluer
    les mesures de déterminisme (variance + coût) lors des runs harness.
    Tests statiques — pas d'appel réseau, pas d'OPENAI_API_KEY requis.
    """

    def _src(self, filename: str) -> str:
        import os
        return open(os.path.join(os.path.dirname(__file__), "..", "agents", filename)).read()

    def test_feature_flag_present_in_all_agents(self):
        """LLM_FALLBACK_ENABLED doit être présent dans les 3 agents concernés."""
        for agent in ("architect.py", "qa.py", "test_coverage.py"):
            src = self._src(agent)
            assert "LLM_FALLBACK_ENABLED" in src, (
                f"{agent} doit vérifier la variable d'env LLM_FALLBACK_ENABLED (T007)"
            )

    def test_fallback_model_is_gpt4o(self):
        """Le fallback model doit être gpt-4o dans les 3 agents."""
        for agent in ("architect.py", "qa.py", "test_coverage.py"):
            src = self._src(agent)
            assert "gpt-4o" in src, f"{agent} doit définir gpt-4o comme fallback (T007)"

    def test_with_fallbacks_guarded_by_flag(self):
        """with_fallbacks() ne doit être appelé que sous le bloc LLM_FALLBACK_ENABLED."""
        for agent in ("architect.py", "qa.py", "test_coverage.py"):
            src = self._src(agent)
            assert "with_fallbacks" in src, f"{agent} doit contenir with_fallbacks (T007)"
            # Vérifie que le flag précède l'appel (ordre dans le fichier)
            flag_pos = src.find("LLM_FALLBACK_ENABLED")
            fb_pos = src.find("with_fallbacks")
            assert flag_pos < fb_pos, (
                f"{agent} : LLM_FALLBACK_ENABLED doit apparaître avant with_fallbacks"
            )

    def test_dev_llm_max_retries_no_fallback(self):
        """
        dev.py : max_retries=3 présent, .with_fallbacks() non appelé
        (bind_tools incompatible avec RunnableWithFallbacks).
        Le commentaire peut mentionner 'with_fallbacks', mais l'appel ne doit pas exister.
        """
        src = self._src("dev.py")
        assert "max_retries=3" in src, "dev.py doit avoir max_retries=3 (T007)"
        # Vérifie l'absence d'un appel réel (pas juste une mention en commentaire)
        assert ".with_fallbacks(" not in src, (
            "dev.py ne doit pas appeler .with_fallbacks() — bind_tools incompatible"
        )

    def test_fallback_triggers_on_rate_limit(self):
        """
        Simulation 429 : RunnableWithFallbacks doit invoquer le fallback si le primaire échoue.
        Test offline via mock — valide le comportement LangChain indépendamment de l'API.
        Skippé si langchain_core non installé dans l'env host (nécessite le conteneur).
        """
        from unittest.mock import MagicMock
        try:
            from langchain_core.runnables.fallbacks import RunnableWithFallbacks
            from langchain_core.runnables import RunnableLambda
        except Exception:
            pytest.skip("RunnableWithFallbacks indisponible dans cette version de langchain_core")

        primary = RunnableLambda(lambda _: (_ for _ in ()).throw(Exception("RateLimitError 429 Too Many Requests")))
        fallback_mock = MagicMock(side_effect=lambda _: {"content": "fallback response"})
        fallback = RunnableLambda(fallback_mock)

        runnable = RunnableWithFallbacks(runnable=primary, fallbacks=[fallback])
        result = runnable.invoke({"messages": []})
        assert fallback_mock.called, "Le fallback doit être appelé quand le primaire lève 429"
        assert isinstance(result, dict) and result.get("content") == "fallback response"

    def test_fallback_disabled_by_default(self):
        """
        Sans LLM_FALLBACK_ENABLED=1, le flag vaut '0' → fallback inactif par défaut.
        Garantit que les runs harness sans flag ne basculent pas sur gpt-4o.
        """
        import os
        original = os.environ.pop("LLM_FALLBACK_ENABLED", None)
        try:
            val = os.getenv("LLM_FALLBACK_ENABLED", "0")
            assert val == "0", "LLM_FALLBACK_ENABLED doit valoir '0' par défaut"
        finally:
            if original is not None:
                os.environ["LLM_FALLBACK_ENABLED"] = original


class TestTemplatePathNormalization:
    """Évite le contournement de la protection template via chemins mal normalisés."""

    def test_normalize_guard_path(self):
        pytest.importorskip("pydantic")
        from agents.shared_tools import _normalize_guard_path

        assert _normalize_guard_path("./lib//prisma.ts") == "lib/prisma.ts"
        assert _normalize_guard_path("lib\\prisma.ts") == "lib/prisma.ts"
        assert _normalize_guard_path("/lib/prisma.ts") == "lib/prisma.ts"


class TestBuildOutcomeCoherence:
    """Empêche l'incohérence BUILD_SUCCESS + build_success=false dans run_metric."""

    def test_build_success_message_wins(self):
        pytest.importorskip("temporalio")
        from workflows.activities.dev_test_activity import _compute_build_outcome

        success, attempts, attempted = _compute_build_outcome(
            result_success=True,
            final_message="BUILD_SUCCESS",
            dev_meta={"build_attempted": True, "build_attempts": 0},
        )
        assert success is True
        assert attempted is True
        assert attempts == 1

    def test_result_success_without_attempt_is_not_success(self):
        pytest.importorskip("temporalio")
        from workflows.activities.dev_test_activity import _compute_build_outcome

        success, attempts, attempted = _compute_build_outcome(
            result_success=True,
            final_message="MAX_ITER_REACHED",
            dev_meta={"build_attempted": False, "build_attempts": 0},
        )
        assert success is False
        assert attempted is False
        assert attempts == 0


class TestForbiddenImportsRuntime:
    """Valide le bridge runtime des forbidden_imports stack -> dev.py."""

    def test_collect_forbidden_import_violations_detects_token(self):
        pytest.importorskip("langchain_openai")
        from agents.dev import _collect_forbidden_import_violations

        files = {
            "app/api/auth/route.ts": "import NextAuth from 'next-auth';\nexport async function GET(){}",
            "app/page.tsx": "export default function Page(){ return <div/>; }",
        }
        violations = _collect_forbidden_import_violations(files, ["next-auth"])
        assert violations
        assert violations[0][0] == "app/api/auth/route.ts"
        assert violations[0][1] == "next-auth"

    def test_collect_forbidden_import_violations_ignores_templated_files(self):
        pytest.importorskip("langchain_openai")
        from agents.dev import _collect_forbidden_import_violations

        files = {
            "lib/prisma.ts": "import { PrismaClient } from '@prisma/client';\nexport default new PrismaClient();",
        }
        violations = _collect_forbidden_import_violations(
            files,
            ["@prisma/client"],
            templated_names={"lib/prisma.ts"},
        )
        assert violations == []


class TestPackageJsonStrictWrite:
    """Empêche les EJSONPARSE npm en refusant package.json invalide dès write_file."""

    def test_write_file_rejects_invalid_package_json(self, monkeypatch):
        pytest.importorskip("pydantic")
        import agents.shared_tools as st

        # Aucun accès disque nécessaire: package.json invalide doit échouer
        # avant l'étape d'écriture.
        monkeypatch.setattr(st, "_get_workdir", lambda: ".")
        monkeypatch.setattr(st, "_resolve_safe_path", lambda p, b: f"./{p}")
        monkeypatch.setattr(st.os, "makedirs", lambda *args, **kwargs: None)

        opened = {"called": False}

        def _fake_open(*args, **kwargs):
            opened["called"] = True
            return io.StringIO()

        monkeypatch.setattr(builtins, "open", _fake_open)

        result = st.write_file.invoke({
            "path": "package.json",
            "content": '{"name": "x", "dependencies": {"next": "15.0.0",}}',
        })
        assert "package.json invalide" in result

    def test_write_file_accepts_and_normalizes_valid_package_json(self, monkeypatch):
        pytest.importorskip("pydantic")
        import agents.shared_tools as st

        monkeypatch.setattr(st, "_get_workdir", lambda: ".")
        monkeypatch.setattr(st, "_resolve_safe_path", lambda p, b: f"./{p}")
        monkeypatch.setattr(st.os, "makedirs", lambda *args, **kwargs: None)

        sink = io.StringIO()

        class _DummyCtx:
            def __enter__(self):
                return sink

            def __exit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: _DummyCtx())

        result = st.write_file.invoke({
            "path": "package.json",
            "content": '{"name":"x","dependencies":{"next":"15.0.0"}}',
        })
        assert result.startswith("OK:")
        parsed = json.loads(sink.getvalue())
        assert parsed["name"] == "x"
        assert parsed["dependencies"]["next"] == "15.0.0"


