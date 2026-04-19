"""
agents/dev_pages_generator.py
──────────────────────────────
Génération DÉTERMINISTE des pages Next.js (liste + détail) et services DAL
depuis ProjectSpec — avant que le LLM démarre.

Rôle :
  1. lib/services/<model>.service.ts  — DAL complet par modèle métier
  2. app/<path>/page.tsx              — Server Component avec vraies données Prisma
  3. app/<path>/loading.tsx           — Skeleton adjacent obligatoire

Ces fichiers remplacent les shells vides (<h1>Titre</h1>) que le LLM produit
quand la spec ne lui dit pas QUOI afficher. En les écrivant de façon déterministe,
le LLM peut se concentrer sur les routes API et les formulaires (Client Components).

Intégration dans dev_graph.py :
    pages_result = generate_pages_and_services(spec_obj, project_workdir)
    template_written.update(pages_result.files)
    # Ajouter pages_result.protected_files dans set_protected_files()

Convention de nommage :
  - Modèle "Task"   → service: task.service.ts, chemin préféré: /tasks, /tasks/[id]
  - Modèle "Invoice"→ service: invoice.service.ts, chemin: /invoices, /invoices/[id]
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Champs à ne PAS afficher dans les JSX générés (infrastructure, non-métier)
_SKIP_FIELDS = {"id", "userid", "createdat", "updatedat", "deletedat", "password",
                "passwordhash", "token", "secret"}

# Champs "titre principal" — utilisés en premier dans le rendu liste
_PRIMARY_DISPLAY = {"title", "name", "label", "subject", "heading", "nom"}

# Champs "métadonnées secondaires" — affichés après le titre
_SECONDARY_DISPLAY = {"description", "status", "amount", "total", "duedate",
                      "priority", "email", "date", "type", "category"}


@dataclass
class PagesGeneratorResult:
    files: dict[str, str]          # relative_path → content
    protected_files: set[str]      # fichiers à protéger contre réécriture LLM
    service_names: list[str]       # ex: ["task.service.ts", "invoice.service.ts"]
    pages_generated: list[str]     # ex: ["app/tasks/page.tsx", "app/tasks/[id]/page.tsx"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_camel(s: str) -> str:
    """PascalCase → camelCase : Task → task, InvoiceItem → invoiceItem"""
    return s[0].lower() + s[1:] if s else s


def _to_plural_lower(name: str) -> str:
    """Task → tasks, Invoice → invoices, Category → categories"""
    lower = name.lower()
    if lower.endswith("y") and not lower.endswith("ay") and not lower.endswith("ey"):
        return lower[:-1] + "ies"
    if lower.endswith("s") or lower.endswith("x") or lower.endswith("z"):
        return lower + "es"
    return lower + "s"


def _service_file_name(model_name: str) -> str:
    """Task → task.service.ts"""
    # CamelCase → kebab: InvoiceItem → invoice-item
    kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", model_name).lower()
    return f"{kebab}.service.ts"


def _find_model_for_page(page_path: str, models: list) -> Optional[object]:
    """
    Tente de faire correspondre un chemin de page à un modèle Prisma.
    /tasks → Task, /tasks/[id] → Task, /invoice-items/[id] → InvoiceItem
    """
    # Premier segment significatif
    segment = page_path.strip("/").split("/")[0].lower()
    # Retirer les paramètres dynamiques
    segment = re.sub(r"\[.*?\]", "", segment).strip("-").strip()
    if not segment:
        return None

    # Essai 1 : match exact (singulier ou pluriel)
    for m in models:
        ml = m.name.lower()
        if segment == ml or segment == ml + "s" or segment == ml + "es":
            return m
        if segment.rstrip("s") == ml or segment.rstrip("es") == ml:
            return m

    # Essai 2 : le segment contient le nom du modèle (kebab-case)
    for m in models:
        kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", m.name).lower()
        if kebab in segment or segment in kebab:
            return m

    # Essai 3 : fuzzy — segment commence par les premières lettres du modèle
    for m in models:
        if segment[:4] and m.name.lower().startswith(segment[:4]):
            return m

    return None


def _pick_display_fields(model) -> tuple[str | None, list[str]]:
    """
    Retourne (primary_field_name, [secondary_field_names]) pour le JSX.
    Analyse les champs réels du modèle Prisma.
    """
    primary: str | None = None
    secondary: list[str] = []

    for f in model.fields:
        fname = f.name.lower()
        ftype = f.type.lower()

        # Ignorer les champs infrastructure
        if fname in _SKIP_FIELDS:
            continue
        # Ignorer les relations (type commence par majuscule, pas dans les primitifs)
        base_type = ftype.rstrip("?")
        if base_type not in {"string", "int", "float", "decimal", "boolean", "datetime",
                             "json", "bytes", "bigint"}:
            continue

        if fname in _PRIMARY_DISPLAY and primary is None:
            primary = f.name
        elif fname in _SECONDARY_DISPLAY:
            secondary.append(f.name)
        elif primary is None and base_type == "string":
            # Premier champ String non-infrastructure → candidat titre de fallback
            primary = f.name

    return primary, secondary[:2]  # max 2 champs secondaires


# ── Générateurs de contenu ─────────────────────────────────────────────────────

def _gen_service(model) -> str:
    """Génère lib/services/<model>.service.ts — DAL complet."""
    name = model.name
    camel = _to_camel(name)
    primary, secondary = _pick_display_fields(model)
    display_fields = ([primary] if primary else []) + secondary

    # Champs "create" — exclut id, timestamps, userId, relations
    create_fields = []
    for f in model.fields:
        fname_lower = f.name.lower()
        attrs = (f.attributes or "").lower()
        if fname_lower in _SKIP_FIELDS:
            continue
        if "@id" in attrs or "@default(now())" in attrs or "@updatedat" in attrs.replace(" ", ""):
            continue
        base = f.type.rstrip("?")
        if base not in {"String", "Int", "Float", "Decimal", "Boolean", "DateTime",
                        "Json", "Bytes", "BigInt"}:
            continue
        optional = "?" in f.type or "?" in attrs
        ts_type = _prisma_to_ts(base)
        opt_mark = "?" if optional else ""
        create_fields.append((f.name + opt_mark, ts_type))

    # Construction des types Create/Update inline (au cas où types.ts n'est pas importé)
    create_type_body = "\n".join(f"  {fn}: {ft}" for fn, ft in create_fields) or "  [key: string]: unknown"

    lines = [
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
        "      data: { ...data, userId } as any,",
        "    })",
        "  },",
        "",
        f"  async update(id: string, data: Update{name}Input, userId: string): Promise<{name}> {{",
        f"    const record = await prisma.{camel}.findUnique({{ where: {{ id }} }})",
        "    if (!record || record.userId !== userId) throw new Error('Forbidden')",
        f"    return prisma.{camel}.update({{",
        "      where: { id },",
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
    ]
    return "\n".join(lines)


def _gen_list_page(page_path: str, model) -> str:
    """Génère app/<path>/page.tsx — Server Component liste avec vraies données."""
    name = model.name
    camel = _to_camel(name)
    kebab_service = _service_file_name(name).replace(".service.ts", "")
    primary, secondary = _pick_display_fields(model)
    plural_label = _to_plural_lower(name).capitalize()
    new_path = page_path.rstrip("/") + "/new"

    # Champ principal d'affichage — avec fallback sur id si aucun trouvé
    if primary:
        primary_jsx = f"{{item.{primary}}}"
    else:
        primary_jsx = "{item.id}"

    # Champs secondaires
    secondary_jsx_lines = []
    for sf in secondary:
        secondary_jsx_lines.append(
            f'                <p className="text-sm text-gray-500">{{String(item.{sf})}}</p>'
        )
    secondary_block = "\n".join(secondary_jsx_lines)

    lines = [
        "export const dynamic = 'force-dynamic'",
        "import { auth } from '@clerk/nextjs/server'",
        "import { redirect } from 'next/navigation'",
        f"import {{ {camel}Service }} from '@/lib/services/{kebab_service}.service'",
        f"import type {{ {name} }} from '@prisma/client'",
        "",
        f"export default async function {name}sPage() {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        "",
        f"  const items: {name}[] = await {camel}Service.findMany(userId).catch(() => [])",
        "",
        "  return (",
        '    <main className="container mx-auto p-6">',
        '      <div className="flex justify-between items-center mb-6">',
        f'        <h1 className="text-2xl font-bold">{plural_label}</h1>',
        f'        <a href="{new_path}" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">',
        f'          Nouveau {name}',
        "        </a>",
        "      </div>",
        "      {items.length === 0 ? (",
        '        <p className="text-gray-500 text-center py-8">Aucun élément trouvé.</p>',
        "      ) : (",
        '        <ul className="space-y-3">',
        f"          {{items.map((item: {name}) => (",
        '            <li key={{item.id}} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">',
        f'              <a href="{page_path.rstrip("/")}/{{item.id}}" className="block">',
        f'                <p className="font-semibold">{primary_jsx}</p>',
    ]

    if secondary_block:
        lines.append(secondary_block)

    lines += [
        '                <p className="text-xs text-gray-400 mt-1">',
        '                  {{new Date(item.createdAt).toLocaleDateString("fr-FR")}}',
        "                </p>",
        "              </a>",
        "            </li>",
        "          ))}",
        "        </ul>",
        "      )}",
        "    </main>",
        "  )",
        "}",
    ]
    return "\n".join(lines)


def _gen_detail_page(page_path: str, model) -> str:
    """Génère app/<path>/[id]/page.tsx — Server Component détail avec notFound()."""
    name = model.name
    camel = _to_camel(name)
    kebab_service = _service_file_name(name).replace(".service.ts", "")
    primary, secondary = _pick_display_fields(model)

    # Calcule le chemin liste (parent)
    list_path = re.sub(r"/\[[\w]+\]$", "", page_path.rstrip("/")) or "/"

    # Champs à afficher (tous les champs non-infrastructure)
    display_all: list[str] = []
    for f in model.fields:
        fname_lower = f.name.lower()
        attrs = (f.attributes or "").lower()
        if fname_lower in _SKIP_FIELDS:
            continue
        if "@id" in attrs or "@default(now())" in attrs:
            continue
        base = f.type.rstrip("?")
        if base not in {"String", "Int", "Float", "Decimal", "Boolean", "DateTime",
                        "Json", "Bytes", "BigInt"}:
            continue
        display_all.append(f.name)

    # JSX des champs
    fields_jsx = []
    for fname in display_all[:8]:  # max 8 champs
        label = fname[0].upper() + fname[1:]
        fields_jsx.append(
            f'        <div className="mb-4">\n'
            f'          <dt className="text-sm font-medium text-gray-500">{label}</dt>\n'
            f'          <dd className="mt-1 text-sm text-gray-900">{{String(item.{fname})}}</dd>\n'
            f'        </div>'
        )

    # Titre de la page
    if primary:
        page_title = f"{{item.{primary}}}"
    else:
        page_title = f"{name} #{{}}"

    # Extraction du param dynamique du chemin ex: /tasks/[id] → id
    param_match = re.findall(r"\[(\w+)\]", page_path)
    param_name = param_match[-1] if param_match else "id"

    lines = [
        "export const dynamic = 'force-dynamic'",
        "import { auth } from '@clerk/nextjs/server'",
        "import { redirect, notFound } from 'next/navigation'",
        f"import {{ {camel}Service }} from '@/lib/services/{kebab_service}.service'",
        "",
        f"export default async function {name}DetailPage({{",
        f"  params,",
        f"}}: {{",
        f"  params: {{ {param_name}: string }}",
        "}) {",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        "",
        f"  const item = await {camel}Service.findUnique(params.{param_name}, userId)",
        "  if (!item) notFound()",
        "",
        "  return (",
        '    <main className="container mx-auto p-6">',
        '      <div className="mb-6">',
        f'        <a href="{list_path}" className="text-blue-600 hover:underline text-sm">',
        f'          ← Retour',
        "        </a>",
        "      </div>",
        f'      <h1 className="text-2xl font-bold mb-6">{page_title}</h1>',
        '      <dl className="bg-white rounded-lg border p-6 space-y-4">',
    ]

    for field_jsx in fields_jsx:
        lines.append(field_jsx)

    lines += [
        "      </dl>",
        '      <div className="mt-6 flex gap-4">',
        f'        <a href="{list_path}/{{item.id}}/edit"',
        '           className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">',
        "          Modifier",
        "        </a>",
        "      </div>",
        "    </main>",
        "  )",
        "}",
    ]
    return "\n".join(lines)


def _gen_loading_tsx() -> str:
    """Génère loading.tsx — skeleton standard."""
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


def _prisma_to_ts(prisma_type: str) -> str:
    _MAP = {
        "String": "string", "Int": "number", "Float": "number",
        "Decimal": "number", "Boolean": "boolean", "DateTime": "string",
        "Json": "unknown", "Bytes": "string", "BigInt": "bigint",
    }
    return _MAP.get(prisma_type, "unknown")


def _page_path_to_file(page_path: str) -> str:
    """
    /tasks → app/tasks/page.tsx
    /tasks/[id] → app/tasks/[id]/page.tsx
    """
    clean = page_path.strip("/")
    if not clean:
        return "app/page.tsx"
    return f"app/{clean}/page.tsx"


def _is_detail_page(page_path: str) -> bool:
    """Retourne True si le chemin contient un paramètre dynamique ex: /tasks/[id]."""
    return bool(re.search(r"\[.+\]", page_path))


# ── Point d'entrée principal ───────────────────────────────────────────────────

def generate_pages_and_services(spec: "ProjectSpec", project_workdir: str) -> PagesGeneratorResult:  # type: ignore[name-defined]
    """
    Génère et écrit sur le disque :
      - lib/services/<model>.service.ts  pour chaque modèle métier
      - app/<path>/page.tsx              pour chaque page avec modèle associé
      - app/<path>/loading.tsx           pour chaque page générée

    Retourne PagesGeneratorResult avec les fichiers écrits et ceux à protéger.
    """
    files: dict[str, str] = {}
    protected: set[str] = set()
    service_names: list[str] = []
    pages_generated: list[str] = []

    # ── 1. Services DAL — un par modèle métier ────────────────────────
    for model in spec.models:
        svc_filename = _service_file_name(model.name)
        svc_rel_path = f"lib/services/{svc_filename}"
        svc_content = _gen_service(model)

        abs_path = os.path.join(project_workdir, "lib", "services", svc_filename)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(svc_content)

        files[svc_rel_path] = svc_content
        protected.add(svc_rel_path)
        service_names.append(svc_filename)
        logger.info("[pages_gen] ✓ service : %s", svc_rel_path)

    # ── 2. Pages — liste + détail ─────────────────────────────────────
    for page in spec.pages:
        path = page.path

        # Page racine ou dashboard sans modèle → skip (LLM gère mieux)
        if path in {"/", "/dashboard", "/home", "/about"}:
            continue

        model = _find_model_for_page(path, spec.models)
        if model is None:
            logger.info("[pages_gen] aucun modèle trouvé pour %s — skip", path)
            continue

        # Génère le contenu selon le type de page
        if _is_detail_page(path):
            content = _gen_detail_page(path, model)
        else:
            content = _gen_list_page(path, model)

        file_rel = _page_path_to_file(path)
        abs_path = os.path.join(project_workdir, file_rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        files[file_rel] = content
        protected.add(file_rel)
        pages_generated.append(file_rel)

        # loading.tsx adjacent
        loading_rel = file_rel.replace("page.tsx", "loading.tsx")
        loading_abs = abs_path.replace("page.tsx", "loading.tsx")
        if not os.path.exists(loading_abs):
            loading_content = _gen_loading_tsx()
            with open(loading_abs, "w", encoding="utf-8") as f:
                f.write(loading_content)
            files[loading_rel] = loading_content
            # loading.tsx n'est pas protégé — le LLM peut l'enrichir
        logger.info("[pages_gen] ✓ page %s → %s (%s)", path, file_rel,
                    "détail" if _is_detail_page(path) else "liste")

    logger.info(
        "[pages_gen] terminé — %d services, %d pages, %d protégés",
        len(service_names), len(pages_generated), len(protected),
    )
    return PagesGeneratorResult(
        files=files,
        protected_files=protected,
        service_names=service_names,
        pages_generated=pages_generated,
    )
