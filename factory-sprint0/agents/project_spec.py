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
PAGE_TYPE = Literal["list", "create", "detail", "custom"]


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
        Retourne l'owner_field validé contre les champs réels du modèle.
        Ordre de résolution :
          1. owner_field déclaré par l'architect s'il existe dans les champs → direct
          2. Pattern sémantique d'ownership (userId, authorId, ownerId, createdById)
          3. Premier champ *Id (hors 'id') — dernier recours avec warning
        """
        import logging as _log
        raw = self.owner_field or "userId"
        field_names = {f.name for f in self.fields}
        if raw in field_names:
            return raw
        # Priorité aux patterns sémantiques d'ownership avant les foreign-keys arbitraires
        _OWNER_PATTERNS = ("userId", "authorId", "ownerId", "createdById", "memberId")
        for _pat in _OWNER_PATTERNS:
            if _pat in field_names:
                _log.getLogger(__name__).warning(
                    "[project_spec] owner_field '%s' absent de %s — semantic fallback : '%s'",
                    raw, self.name, _pat,
                )
                return _pat
        candidates = [f.name for f in self.fields if f.name.endswith("Id") and f.name != "id"]
        if candidates:
            _log.getLogger(__name__).warning(
                "[project_spec] owner_field '%s' absent de %s — fallback *Id : '%s'",
                raw, self.name, candidates[0],
            )
            return candidates[0]
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
        description="Flux utilisateur principaux, ex: 'Un utilisateur crée un produit'"
    )
    spec_fingerprint: str = Field(
        default="",
        description="Hash SHA256 des noms critiques — calculé automatiquement"
    )

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

        Résolution par priorité :
          1. page.page_type == 'list' ET page.model == model_name  (déclaration explicite)
          2. Heuristique sur le path (rétrocompat briefs sans page_type)
          3. Fallback calculé : /{pluralize(kebab(model_name))}
        """
        import re as _re

        def _kebab(s: str) -> str:
            return _re.sub(r"(?<!^)(?=[A-Z])", "-", s).lower()

        def _pluralize(w: str) -> str:
            if w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
                return w[:-1] + "ies"
            if w.endswith(("s", "sh", "ch", "x", "z")):
                return w + "es"
            return w + "s"

        # 1. Résolution explicite — pages privées prioritaires (mutations → redirect auth)
        candidates = [p for p in self.pages if p.page_type == "list" and p.model == model_name]
        if candidates:
            private = next((p for p in candidates if p.auth_required), None)
            return (private or candidates[0]).path

        # 2. Heuristique (rétrocompat)
        kebab = _kebab(model_name)
        plural = _pluralize(kebab)
        list_pages = [p.path for p in self.pages if "[" not in p.path and p.path != "/"]
        if f"/{kebab}" in list_pages:
            return f"/{kebab}"
        if f"/{plural}" in list_pages:
            return f"/{plural}"
        base = kebab.split("-")[0]
        for page_path in list_pages:
            first_seg = page_path.lstrip("/").split("/")[0]
            if first_seg.startswith(base):
                return page_path

        # 3. Fallback calculé
        return f"/{plural}"

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
        Génère le fichier schema.prisma complet : header canonique + modèle User + modèles métier.
        Le header (generator + datasource) est INVARIANT — ne jamais l'omettre.
        Utilisé dans le system prompt du dev agent pour garantir la cohérence.
        """
        header = (
            'generator client {\n'
            '  provider = "prisma-client-js"\n'
            '}\n'
            '\n'
            'datasource db {\n'
            '  provider  = "postgresql"\n'
            '  url       = env("DATABASE_URL")\n'
            '  directUrl = env("DIRECT_DATABASE_URL")\n'
            '}\n'
            '\n'
        )

        # Modèle User standard — synchronisé via le webhook Clerk.
        # Présent dans TOUS les projets pour associer les entités métier à un utilisateur réel.
        user_model_block = (
            "model User {\n"
            '  id        String   @id              // Clerk userId (ex: user_xxx)\n'
            '  email     String   @unique\n'
            '  name      String?\n'
            '  createdAt DateTime @default(now())\n'
            '  updatedAt DateTime @updatedAt\n'
            "\n"
            "  @@index([email])\n"
            "}\n"
            "\n"
        )

        lines = []
        model_names = {m.name for m in self.models}
        # Injecte User seulement si des modèles l'utilisent réellement (ownership direct
        # ou relation explicite). Evite d'ajouter une table orpheline pour les apps sans auth user.
        _needs_user = any(
            m.resolved_owner().lower() == "userid"
            or any(f.type == "User" for f in m.fields)
            for m in self.models
        )
        if "User" not in model_names and _needs_user:
            lines.append(user_model_block)

        for model in self.models:
            lines.append(f"model {model.name} {{")
            for field in model.fields:
                lines.append(field.to_prisma_line())
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
