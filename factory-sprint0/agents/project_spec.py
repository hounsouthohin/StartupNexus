# agents/project_spec.py
"""
ProjectSpec — modèle Pydantic typé, source de vérité unique entre architect et dev agent.
Phase 1 — Nouvelle Base (28 Mars 2026).

Remplace la chaîne spec_writer (texte libre, dérive garantie) par un objet structuré
dont les noms de modèles/pages/routes sont garantis par le type Python.
instructor assure que le LLM ne peut pas retourner autre chose que ce schéma.
"""
from __future__ import annotations

import hashlib
import json
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

HTTP_METHOD = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
PAGE_TYPE = Literal["list", "create", "detail", "detail-slug", "edit", "custom"]


class PrismaField(BaseModel):
    name: str = Field(description="Nom du champ Prisma, ex: id, title, userId")
    type: str = Field(description="Type Prisma, ex: String, Int, Boolean, DateTime")
    attributes: str = Field(
        default="",
        description="Attributs Prisma, ex: @id @default(uuid()), ?, @relation(...)"
    )

    def to_prisma_line(self) -> str:
        parts = [self.name, self.type]
        if self.attributes:
            parts.append(self.attributes)
        return "  " + " ".join(parts)


class PrismaModel(BaseModel):
    name: str = Field(
        description=(
            "Nom EXACT du modèle Prisma tel qu'extrait du brief — "
            "PascalCase, aucune traduction ni synonyme. "
            "Ex: Product, Order, AuditLog, BookingSlot"
        )
    )
    fields: List[PrismaField] = Field(
        description="Liste des champs du modèle. Toujours inclure id, createdAt minimum."
    )
    owner_field: str = Field(
        default="userId",
        description=(
            "Champ d'ownership dans ce modèle. "
            "'userId' pour les modèles directs (Expense, Task, Invoice). "
            "'authorId' pour les modèles CMS (Post, Article). "
            "Nom du champ parent (ex: 'boardId') pour les modèles enfants sans userId direct."
        )
    )

    def resolved_owner(self) -> str:
        """
        Retourne l'owner_field résolu pour ce modèle.
        Fallback en cascade : champ déclaré → userId → premier champ disponible.
        Logue un warning si le champ déclaré n'existe pas (architect halucination).
        """
        import logging as _log
        _logger = _log.getLogger(__name__)
        raw = self.owner_field or "userId"
        field_names = {f.name for f in self.fields}
        if raw in field_names:
            return raw
        if "userId" in field_names:
            _logger.warning(
                "[PrismaModel] %s : owner_field='%s' absent du schema Prisma → fallback 'userId'",
                self.name, raw,
            )
            return "userId"
        _logger.error(
            "[PrismaModel] %s : owner_field='%s' absent ET 'userId' absent — "
            "le service utilisera un champ inexistant (erreur TypeScript probable).",
            self.name, raw,
        )
        return raw


class ApiRoute(BaseModel):
    method: HTTP_METHOD = Field(description="Méthode HTTP")
    path: str = Field(
        description=(
            "Chemin de la route API, ex: /api/products, /api/orders/[id]. "
            "Toujours commencer par /api/"
        )
    )
    description: str = Field(default="", description="Ce que fait la route en une phrase")


class AppPage(BaseModel):
    path: str = Field(
        description=(
            "Chemin de la page Next.js, ex: /dashboard, /products/[id], /admin/users. "
            "Toujours commencer par /"
        )
    )
    auth_required: bool = Field(
        default=True,
        description="True si la page nécessite une authentification Clerk"
    )
    page_type: PAGE_TYPE = Field(
        default="custom",
        description=(
            "Type explicite de la page — déclaré dans le brief, jamais deviné par heuristique. "
            "'list'   : page affichant une collection de modèles (model obligatoire). "
            "'create' : formulaire de création (path finit en /new ou /create). "
            "'detail' : vue d'un item unique (path contient [id], model obligatoire). "
            "'custom' : tout autre type (dashboard de stats, landing, etc.)."
        )
    )
    model: Optional[str] = Field(
        default=None,
        description=(
            "Nom PascalCase du modèle Prisma principal affiché sur cette page. "
            "Obligatoire si page_type='list' ou 'detail'. "
            "Omis pour page_type='create' et 'custom'. "
            "Ex: 'Post' pour /dashboard, 'Category' pour /categories"
        )
    )

    @model_validator(mode="after")
    def validate_model_required_for_list_detail(self) -> "AppPage":
        if self.page_type in ("list", "detail") and not self.model:
            import logging
            logging.getLogger(__name__).warning(
                "[AppPage] page_type='%s' sur '%s' sans champ 'model' — "
                "le générateur ne pourra pas synchroniser les props page.tsx / page-client.tsx.",
                self.page_type, self.path,
            )
        return self


class ProjectSpec(BaseModel):
    project_name: str = Field(default="", description="Nom du projet")
    stack_id: str = Field(default="nextjs-clerk-prisma", description="Identifiant de la stack")
    description: str = Field(
        default="",
        description="Description humaine du projet — transmise au spec_writer pour contexte métier"
    )
    models: List[PrismaModel] = Field(
        description=(
            "Tous les modèles Prisma nécessaires au projet. "
            "Chaque modèle appelé dans le code DOIT figurer ici."
        )
    )
    routes: List[ApiRoute] = Field(
        description="Toutes les routes API du projet"
    )
    pages: List[AppPage] = Field(
        description="Toutes les pages Next.js du projet (App Router)"
    )
    pages_detail: dict = Field(
        default_factory=dict,
        description=(
            "Instructions d'affichage par page : { '/path': 'description précise des données, "
            "champs, actions, état vide' }. Transmis au spec_writer pour les blueprints."
        )
    )
    user_flows: List[str] = Field(
        default_factory=list,
        description=(
            "Flux utilisateur principaux. Chaque flux DOIT mentionner le chemin de la page "
            "concernée : 'Sur /dashboard : l\'auteur voit un résumé de son activité'."
        )
    )
    ui_labels: dict = Field(
        default_factory=dict,
        description=(
            "Labels d'affichage par modèle et par champ, dans la langue du brief. "
            "Format : { 'ModelName': { 'fieldName': 'Label affiché' } }. "
            "Exemple : { 'Recipe': { 'title': 'Titre', 'status': 'Statut', 'categoryId': 'Catégorie' } }"
        )
    )
    title_plurals: dict = Field(
        default_factory=dict,
        description=(
            "Titre pluriel lisible pour chaque modèle, dans la langue du brief. "
            "Format : { 'ModelName': 'Titre pluriel' }. "
            "Exemple : { 'Recipe': 'Recettes', 'LeaveRequest': 'Demandes de congé' }"
        )
    )
    enums: dict = Field(
        default_factory=dict,
        description=(
            "Enums Prisma du projet : { 'EnumName': ['value1', 'value2', ...] }. "
            "Utilisé par le zod generator pour générer z.enum([...]) au lieu de z.string(). "
            "Exemple : { 'PostStatus': ['draft', 'published', 'archived'] }"
        )
    )
    enum_value_labels: dict = Field(
        default_factory=dict,
        description=(
            "Labels d'affichage pour chaque valeur d'enum, dans la langue du brief. "
            "Format : { 'EnumName': { 'value': 'Label affiché' } }. "
            "Exemple : { 'LeaveStatus': { 'pending': 'En attente', 'approved': 'Approuvé', 'rejected': 'Refusé' } }"
        )
    )
    page_links: dict = Field(
        default_factory=dict,
        description=(
            "Contrat de navigation par page : { '/path': ['/link1', '/link2'] }. "
            "Chaque page liste les SEULS chemins valides pour ses <Link href>. "
            "Dérivé de spec.pages — ne jamais inclure un chemin absent de pages. "
            "Exemple : { '/projects': ['/projects/new'], '/projects/new': ['/projects'] }"
        )
    )
    spec_fingerprint: str = Field(
        default="",
        description="Hash SHA256 des noms critiques — calculé automatiquement"
    )
    design_system: dict = Field(
        default_factory=dict,
        description=(
            "Design system du projet : mood, primary_color (classe Tailwind ex: 'indigo-600'), "
            "sidebar_bg, brand_name, animation_level, density. "
            "Produit par brief_writer_node — propagé vers tous les générateurs."
        )
    )
    enriched_spec: dict = Field(
        default_factory=dict,
        description=(
            "Spec enrichie par le semantic annotator : field_annotations, "
            "required_queries, features, ux_hints (empty_states, dependency_order)."
        )
    )

    # Noms de modèles interdits : Clerk gère l'authentification — un modèle User
    # dans Prisma crée des TS2339 (userId vs User.id) et viole STACK_INVARIANTS.
    _FORBIDDEN_MODEL_NAMES: set[str] = {"User", "Account", "Session", "VerificationToken"}

    @model_validator(mode="after")
    def strip_forbidden_models(self) -> "ProjectSpec":
        import logging as _log
        _logger = _log.getLogger(__name__)
        filtered = [m for m in self.models if m.name not in self._FORBIDDEN_MODEL_NAMES]
        if len(filtered) < len(self.models):
            removed = [m.name for m in self.models if m.name in self._FORBIDDEN_MODEL_NAMES]
            _logger.warning(
                "[ProjectSpec] modèles interdits retirés (géré par Clerk) : %s",
                removed,
            )
            self.models = filtered
        return self

    @model_validator(mode="after")
    def _normalize_pages(self) -> "ProjectSpec":
        """
        Spec Completion Layer — corrige les incohérences de l'architect sur les pages.

        1. page.model référence un modèle absent → model=None (évite les KeyError en génération)
        2. page_type="custom" avec un model → inférence depuis le chemin :
             /new | /create → type="create", model=None (create pages n'ont pas de model)
             /[id] | /[slug] → type="detail" ou "detail-slug"
             chemin sans paramètre → type="list"
        3. page.model référence un modèle existant avec page_type="detail-slug" mais le
           modèle n'a pas de champ slug → rétrogradation en "detail"
        """
        import logging as _log
        _logger = _log.getLogger(__name__)
        model_names = {m.name for m in self.models}
        model_fields: dict[str, set[str]] = {
            m.name: {f.name.lower() for f in m.fields} for m in self.models
        }

        for page in self.pages:
            # Fix 1 — modèle fantôme
            if page.model and page.model not in model_names:
                _logger.warning(
                    "[ProjectSpec] page '%s' référence le modèle '%s' absent → model=None",
                    page.path, page.model,
                )
                page.model = None

            # Fix 2 — type "custom" avec un modèle → inférence depuis le chemin
            if page.page_type == "custom" and page.model:
                parts = [p for p in page.path.rstrip("/").split("/") if p]
                last = parts[-1] if parts else ""
                if last in ("new", "create"):
                    _logger.info(
                        "[ProjectSpec] page '%s' : custom+model → create (chemin /new|/create)",
                        page.path,
                    )
                    page.page_type = "create"
                    page.model = None
                elif last.startswith("[") and last.endswith("]"):
                    segment = last[1:-1]
                    inferred = "detail-slug" if "slug" in segment.lower() else "detail"
                    _logger.info(
                        "[ProjectSpec] page '%s' : custom+model → %s (segment [%s])",
                        page.path, inferred, segment,
                    )
                    page.page_type = inferred
                else:
                    _logger.info(
                        "[ProjectSpec] page '%s' : custom+model → list (chemin plat)",
                        page.path,
                    )
                    page.page_type = "list"

            # Fix 3 — detail-slug sans champ slug dans le modèle
            if page.page_type == "detail-slug" and page.model:
                fields = model_fields.get(page.model, set())
                if "slug" not in fields:
                    _logger.warning(
                        "[ProjectSpec] page '%s' : detail-slug mais modèle '%s' sans champ slug → detail",
                        page.path, page.model,
                    )
                    page.page_type = "detail"

            # Fix 5 — edit page sans model → inférer depuis la page parente dans spec
            # /dashboard/posts/[slug]/edit → chemin parent = /dashboard/posts → liste Post
            if page.page_type == "edit" and not page.model:
                _edit_segs = [s for s in page.path.strip("/").split("/")
                              if not s.startswith("[") and s != "edit"]
                _parent_path = "/" + "/".join(_edit_segs)
                _parent = next(
                    (p for p in self.pages if p.path == _parent_path and p.model),
                    None,
                )
                if _parent and _parent.model in model_names:
                    page.model = _parent.model
                    _logger.info(
                        "[ProjectSpec] page edit '%s' : model inféré → %s",
                        page.path, page.model,
                    )

            # Fix 4 — edit page avec [id] pour un modèle avec slug → remplace par [slug]
            # dev_form_generator génère les edit à [slug] si has_slug=True.
            # Si l'architect déclare [id]/edit, le form_generator produit [id]/edit/page-client.tsx
            # ET [slug]/edit/page-client.tsx → deux fichiers orphelins en conflit.
            if page.page_type == "edit" and page.model and "[id]" in page.path:
                fields = model_fields.get(page.model, set())
                if "slug" in fields:
                    page.path = page.path.replace("[id]", "[slug]")
                    _logger.info(
                        "[ProjectSpec] page '%s' : edit+slug → path normalisé [id]→[slug]",
                        page.path,
                    )

        return self

    def compute_fingerprint(self) -> str:
        """Hash déterministe : noms modèles + owner_fields + pages + routes + pages_detail."""
        elements = sorted(
            [f"{m.name}:{m.resolved_owner()}" for m in self.models]
            + [p.path for p in self.pages]
            + [f"{r.method} {r.path}" for r in self.routes]
        )
        detail_raw = json.dumps(self.pages_detail, ensure_ascii=False, sort_keys=True)
        raw = json.dumps({"e": elements, "d": detail_raw}, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def with_fingerprint(self) -> "ProjectSpec":
        """Retourne une copie avec le fingerprint calculé."""
        self.spec_fingerprint = self.compute_fingerprint()
        return self

    # ── Méthodes de lookup — source de vérité pour tous les générateurs ──────

    def get_model_by_name(self, name: str) -> "Optional[PrismaModel]":
        """Lookup PascalCase → PrismaModel. Retourne None si absent."""
        return next((m for m in self.models if m.name == name), None)

    def get_list_page_for_model(self, model_name: str) -> str:
        """
        Path de la page liste pour ce modèle.
        Résolution stricte : page.page_type == 'list' ET page.model == model_name.
        Pages privées prioritaires (redirect post-mutation → page auth).
        Retourne "" si aucune page liste déclarée pour ce modèle.
        """
        candidates = [p for p in self.pages if p.page_type == "list" and p.model == model_name]
        if not candidates:
            return ""
        private = next((p for p in candidates if p.auth_required), None)
        return (private or candidates[0]).path

    def get_public_pages(self) -> "List[AppPage]":
        """Pages avec auth_required=False, dans l'ordre du brief."""
        return [p for p in self.pages if not p.auth_required]

    def get_private_pages(self) -> "List[AppPage]":
        """Pages avec auth_required=True."""
        return [p for p in self.pages if p.auth_required]

    def get_pages_for_model(self, model_name: str) -> "List[AppPage]":
        """Toutes les pages référençant ce modèle via page.model."""
        return [p for p in self.pages if p.model == model_name]

    def model_has_status_field(self, model_name: str) -> bool:
        """True si le modèle a un champ nommé 'status'."""
        m = self.get_model_by_name(model_name)
        return bool(m and any(f.name.lower() == "status" for f in m.fields))

    # ─────────────────────────────────────────────────────────────────────────

    def to_requirements(self) -> List[str]:
        """
        Convertit la spec en requirements[] pour compatibilité avec dev_test_activity.
        Seuls les modèles et pages sont trackés — les routes API ont été remplacées
        par des Server Actions et ne peuvent pas être vérifiées de la même façon.
        """
        reqs: List[str] = []
        for m in self.models:
            reqs.append(f"Modèle Prisma: {m.name}")
        for p in self.pages:
            reqs.append(f"Page: {p.path}")
        return reqs

    def to_prisma_schema_block(self) -> str:
        """
        Génère le fichier schema.prisma complet : header canonique + modèles métier.
        Le header (generator + datasource) est INVARIANT — ne jamais l'omettre.
        Utilisé dans le system prompt du dev agent pour garantir la cohérence.
        Note : le modèle User n'est PAS injecté — userId/authorId sont des String scalaires
        (référence Clerk externe), pas des FK vers un modèle Prisma.
        """
        header = (
            'generator client {\n'
            '  provider = "prisma-client-js"\n'
            '}\n'
            '\n'
            'datasource db {\n'
            '  provider = "postgresql"\n'
            '}\n'
            '\n'
        )

        lines = []

        # Enums Prisma — OBLIGATOIRE avant les modèles qui les référencent.
        # Sans ce bloc, prisma validate échoue P1012 "Type X is neither a built-in type..."
        spec_enums: dict = getattr(self, "enums", None) or {}
        for enum_name, enum_values in spec_enums.items():
            lines.append(f"enum {enum_name} {{")
            for val in enum_values:
                lines.append(f"  {val}")
            lines.append("}")
            lines.append("")

        # Guard P1012 : auto-complétion des relations inverses manquantes.
        # Prisma exige les deux côtés de chaque @relation. Quand l'architect LLM
        # déclare `child.ref Parent @relation(...)` sans ajouter `children Child[]`
        # sur Parent, prisma generate échoue avant même le LLM dev.
        # On détecte et injecte les champs inverses manquants au moment de la génération.
        _all_model_names: set[str] = {m.name for m in self.models}
        _existing_array_types: dict[str, set[str]] = {}
        for _m in self.models:
            _existing_array_types[_m.name] = {
                _f.type.replace("[]", "").strip()
                for _f in _m.fields if "[]" in _f.type
            }
        _inverse_to_inject: dict[str, list[str]] = {}
        _injected: set[tuple[str, str]] = set()
        for _m in self.models:
            for _f in _m.fields:
                if "@relation" not in (_f.attributes or ""):
                    continue
                _parent = _f.type.rstrip("?").rstrip("[]")
                if _parent not in _all_model_names:
                    continue
                if _m.name not in _existing_array_types.get(_parent, set()):
                    _key = (_parent, _m.name)
                    if _key not in _injected:
                        _injected.add(_key)
                        _inv_name = _m.name[0].lower() + _m.name[1:] + "s"
                        _inverse_to_inject.setdefault(_parent, []).append(
                            f"  {_inv_name} {_m.name}[]"
                        )

        # Guard P1012 (bis) : many-to-many implicite déclaré d'un seul côté.
        # Prisma exige les DEUX côtés en tableau (Post.tags Tag[] ↔ Tag.posts Post[]).
        # Un champ tableau vers un modèle SANS FK inverse est un M2M implicite —
        # si le côté opposé manque, on l'injecte.
        _model_by_name = {m.name: m for m in self.models}
        for _m in self.models:
            for _f in _m.fields:
                if "[]" not in _f.type or "@relation" in (_f.attributes or ""):
                    continue
                _target_name = _f.type.rstrip("?").rstrip("[]")
                _target = _model_by_name.get(_target_name)
                if _target is None:
                    continue
                # FK inverse chez le cible → côté inverse d'un 1-N, pas un M2M
                _has_fk_back = any(
                    _tf.name.endswith("Id") and _tf.name != "id"
                    and (_tf.name[:-2][0].upper() + _tf.name[:-2][1:] if _tf.name[:-2] else "") == _m.name
                    for _tf in _target.fields
                )
                if _has_fk_back:
                    continue
                if _m.name in _existing_array_types.get(_target_name, set()):
                    continue  # côté inverse déjà déclaré
                _key = (_target_name, _m.name)
                if _key not in _injected:
                    _injected.add(_key)
                    _inv_name = _m.name[0].lower() + _m.name[1:] + "s"
                    _inverse_to_inject.setdefault(_target_name, []).append(
                        f"  {_inv_name} {_m.name}[]"
                    )

        for model in self.models:
            lines.append(f"model {model.name} {{")
            _field_names = {f.name.lower() for f in model.fields}
            _field_names_exact = {f.name for f in model.fields}
            for field in model.fields:
                lines.append(field.to_prisma_line())
            for _inv in _inverse_to_inject.get(model.name, []):
                lines.append(_inv)
            # Inject updatedAt if missing — all entity models need it for cache invalidation
            if "updatedat" not in _field_names and "createdat" in _field_names:
                lines.append("  updatedAt DateTime @updatedAt")
            # Inject @@index([ownerField]) if missing — userId queries are always filtered
            _owner = model.resolved_owner()
            if _owner in _field_names_exact:
                _all_field_lines = "\n".join(f.to_prisma_line() for f in model.fields)
                if f"@@index([{_owner}])" not in _all_field_lines and f"@@index([{_owner}" not in _all_field_lines:
                    lines.append(f"  @@index([{_owner}])")
            lines.append("}")
            lines.append("")
        return header + "\n".join(lines)

    def expected_files(self) -> List[str]:
        """
        Checklist déterministe des fichiers que le dev agent DOIT générer.
        Injectée dans le system prompt comme guide (pas comme gate).
        """
        files = [
            "package.json",
            "app/layout.tsx",
            "app/page.tsx",
            "middleware.ts",
            "prisma/schema.prisma",
            ".env.local",
        ]
        for page in self.pages:
            path = page.path.strip("/")
            if path:
                files.append(f"app/{path}/page.tsx")
        # Option A (Avril 2026) : mutations → Server Actions (actions.ts).
        # Seules les routes webhook génèrent un route.ts.
        for route in self.routes:
            path = route.path.strip("/")
            if path and ("webhook" in route.path.lower() or "stripe" in route.path.lower()):
                files.append(f"app/{path}/route.ts")
        # Déduplique en préservant l'ordre
        seen: set[str] = set()
        result = []
        for f in files:
            if f not in seen:
                seen.add(f)
                result.append(f)
        return result
