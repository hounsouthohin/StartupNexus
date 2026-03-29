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

from pydantic import BaseModel, Field

HTTP_METHOD = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


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


class ProjectSpec(BaseModel):
    project_name: str = Field(default="", description="Nom du projet")
    stack_id: str = Field(default="nextjs-clerk-prisma", description="Identifiant de la stack")
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
    user_flows: List[str] = Field(
        default_factory=list,
        description="Flux utilisateur principaux, ex: 'Un utilisateur crée un produit'"
    )
    spec_fingerprint: str = Field(
        default="",
        description="Hash SHA256 des noms critiques — calculé automatiquement"
    )

    def compute_fingerprint(self) -> str:
        """Hash déterministe des noms modèles + chemins pages + chemins routes."""
        names = sorted(
            [m.name for m in self.models]
            + [p.path for p in self.pages]
            + [f"{r.method} {r.path}" for r in self.routes]
        )
        raw = json.dumps(names, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def with_fingerprint(self) -> "ProjectSpec":
        """Retourne une copie avec le fingerprint calculé."""
        self.spec_fingerprint = self.compute_fingerprint()
        return self

    def to_requirements(self) -> List[str]:
        """
        Convertit la spec en requirements[] pour compatibilité avec dev_test_activity.
        Format identique à celui de brief_parser / requirements_engine.
        """
        reqs: List[str] = []
        for m in self.models:
            reqs.append(f"Modèle Prisma: {m.name}")
        for p in self.pages:
            reqs.append(f"Page: {p.path}")
        for r in self.routes:
            reqs.append(f"API Route: {r.method} {r.path}")
        return reqs

    def to_prisma_schema_block(self) -> str:
        """
        Génère le fichier schema.prisma complet : header canonique + modèles métier.
        Le header (generator + datasource) est INVARIANT — ne jamais l'omettre.
        Utilisé dans le system prompt du dev agent pour garantir la cohérence.
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
        for route in self.routes:
            path = route.path.strip("/")
            if path:
                files.append(f"app/{path}/route.ts")
        # Déduplique en préservant l'ordre
        seen: set[str] = set()
        result = []
        for f in files:
            if f not in seen:
                seen.add(f)
                result.append(f)
        return result
