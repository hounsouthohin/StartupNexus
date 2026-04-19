"""
agents/dev_pages_generator.py
──────────────────────────────
Génération DÉTERMINISTE de lib/services/<model>.service.ts et loading.tsx
depuis ProjectSpec — avant que le LLM démarre.

Rôle limité et intentionnel :
  1. lib/services/<model>.service.ts  — DAL complet (findMany, findUnique, create, update, delete)
  2. app/<path>/loading.tsx            — Skeleton adjacent obligatoire

Ces deux types de fichiers sont INDÉPENDANTS du contenu du brief :
  - Le service DAL est une structure pure (Prisma + ownership check) qui ne dépend
    pas de ce que l'UI veut afficher.
  - loading.tsx est un skeleton générique valide pour n'importe quelle page.

Les page.tsx (liste, détail, formulaire) sont volontairement LAISSÉES au LLM
car leur contenu dépend du brief. La spec_writer.md produit un blueprint par page
(Données / Rendu / Actions) que le LLM suit pour générer les vraies données.

Intégration dans dev_graph.py :
    pages_result = generate_pages_and_services(spec_obj, project_workdir)
    template_written.update(pages_result.files)
    _pages_protected |= pages_result.protected_files
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_SKIP_FIELDS = {"id", "userid", "createdat", "updatedat", "deletedat",
                "password", "passwordhash", "token", "secret"}


@dataclass
class PagesGeneratorResult:
    files: dict[str, str]
    protected_files: set[str]
    service_names: list[str]
    pages_generated: list[str] = field(default_factory=list)  # toujours vide — pages laissées au LLM


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_camel(s: str) -> str:
    return s[0].lower() + s[1:] if s else s


def _service_file_name(model_name: str) -> str:
    """Task → task.service.ts, InvoiceItem → invoice-item.service.ts"""
    kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", model_name).lower()
    return f"{kebab}.service.ts"


def _prisma_to_ts(prisma_type: str) -> str:
    _MAP = {
        "String": "string", "Int": "number", "Float": "number",
        "Decimal": "number", "Boolean": "boolean", "DateTime": "string",
        "Json": "unknown", "Bytes": "string", "BigInt": "bigint",
    }
    return _MAP.get(prisma_type, "unknown")


def _gen_service(model) -> str:
    """Génère lib/services/<model>.service.ts — DAL complet avec ownership check."""
    name = model.name
    camel = _to_camel(name)

    create_fields = []
    for f in model.fields:
        fname_lower = f.name.lower()
        attrs = (f.attributes or "").lower()
        if fname_lower in _SKIP_FIELDS:
            continue
        if "@id" in attrs or "@default(now())" in attrs or "@updatedat" in attrs.replace(" ", ""):
            continue
        if "@relation" in attrs:
            continue
        base = f.type.rstrip("?")
        if base not in {"String", "Int", "Float", "Decimal", "Boolean", "DateTime",
                        "Json", "Bytes", "BigInt"}:
            continue
        optional = "?" in f.type or ("?" in attrs and "@" not in attrs.split("?")[0])
        ts_type = _prisma_to_ts(base)
        opt_mark = "?" if optional else ""
        create_fields.append((f.name + opt_mark, ts_type))

    create_type_body = (
        "\n".join(f"  {fn}: {ft}" for fn, ft in create_fields)
        or "  [key: string]: unknown"
    )

    return "\n".join([
        "// AUTO-GÉNÉRÉ PAR dev_pages_generator.py — NE PAS MODIFIER",
        "import prisma from '@/lib/prisma'",
        f"import type {{ {name} }} from '@prisma/client'",
        "",
        f"export type Create{name}Input = {{",
        create_type_body,
        "}",
        f"export type Update{name}Input = Partial<Create{name}Input>",
        "",
        f"export const {camel}Service = {{",
        "",
        f"  async findMany(userId: string): Promise<{name}[]> {{",
        f"    return prisma.{camel}.findMany({{",
        "      where: { userId },",
        "      orderBy: { createdAt: 'desc' },",
        "    })",
        "  },",
        "",
        f"  async findUnique(id: string, userId: string): Promise<{name} | null> {{",
        f"    const record = await prisma.{camel}.findUnique({{ where: {{ id }} }})",
        "    if (!record || record.userId !== userId) return null",
        "    return record",
        "  },",
        "",
        f"  async create(data: Create{name}Input, userId: string): Promise<{name}> {{",
        f"    return prisma.{camel}.create({{",
        "      data: {{ ...data, userId }} as any,",
        "    })",
        "  },",
        "",
        f"  async update(id: string, data: Update{name}Input, userId: string): Promise<{name}> {{",
        f"    const record = await prisma.{camel}.findUnique({{ where: {{ id }} }})",
        "    if (!record || record.userId !== userId) throw new Error('Forbidden')",
        f"    return prisma.{camel}.update({{",
        "      where: {{ id }},",
        "      data: data as any,",
        "    })",
        "  },",
        "",
        f"  async delete(id: string, userId: string): Promise<void> {{",
        f"    const record = await prisma.{camel}.findUnique({{ where: {{ id }} }})",
        "    if (!record || record.userId !== userId) throw new Error('Forbidden')",
        f"    await prisma.{camel}.delete({{ where: {{ id }} }})",
        "  },",
        "",
        "}",
    ])


def _gen_loading_tsx() -> str:
    return "\n".join([
        "export default function Loading() {",
        "  return (",
        '    <main className="container mx-auto p-6">',
        '      <div className="animate-pulse space-y-4">',
        '        <div className="h-8 bg-gray-200 rounded w-48" />',
        '        <div className="h-4 bg-gray-200 rounded w-full" />',
        '        <div className="h-4 bg-gray-200 rounded w-3/4" />',
        '        <div className="h-4 bg-gray-200 rounded w-5/6" />',
        "      </div>",
        "    </main>",
        "  )",
        "}",
    ])


def _page_path_to_loading(page_path: str) -> str:
    clean = page_path.strip("/")
    if not clean:
        return "app/loading.tsx"
    return f"app/{clean}/loading.tsx"


# ── Point d'entrée principal ───────────────────────────────────────────────────

def generate_pages_and_services(spec: "ProjectSpec", project_workdir: str) -> PagesGeneratorResult:  # type: ignore[name-defined]
    """
    Génère et écrit sur le disque :
      - lib/services/<model>.service.ts  — un par modèle métier (protégé)
      - app/<path>/loading.tsx           — un par page auth (non protégé)

    Les page.tsx sont intentionnellement laissées au LLM (guidé par spec_writer blueprint).
    """
    files: dict[str, str] = {}
    protected: set[str] = set()
    service_names: list[str] = []

    # ── 1. Services DAL — un par modèle ──────────────────────────────
    for model in spec.models:
        svc_filename = _service_file_name(model.name)
        svc_rel = f"lib/services/{svc_filename}"
        content = _gen_service(model)

        abs_path = os.path.join(project_workdir, "lib", "services", svc_filename)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        files[svc_rel] = content
        protected.add(svc_rel)
        service_names.append(svc_filename)
        logger.info("[pages_gen] ✓ service : %s", svc_rel)

    # ── 2. loading.tsx — adjacent à chaque page qui fetche des données ──
    for page in spec.pages:
        if not page.auth_required:
            continue  # pages publiques sans fetch Prisma → pas de loading nécessaire
        loading_rel = _page_path_to_loading(page.path)
        loading_abs = os.path.join(project_workdir, loading_rel.replace("/", os.sep))
        if os.path.exists(loading_abs):
            continue  # déjà généré (template précédent)
        os.makedirs(os.path.dirname(loading_abs), exist_ok=True)
        content = _gen_loading_tsx()
        with open(loading_abs, "w", encoding="utf-8") as f:
            f.write(content)
        files[loading_rel] = content
        logger.info("[pages_gen] ✓ loading : %s", loading_rel)

    logger.info(
        "[pages_gen] terminé — %d services, %d loading.tsx, 0 pages (rôle LLM)",
        len(service_names), len(files) - len(service_names),
    )
    return PagesGeneratorResult(
        files=files,
        protected_files=protected,
        service_names=service_names,
    )
