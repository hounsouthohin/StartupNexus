"""
agents/dev_actions_generator.py
────────────────────────────────
Génération DÉTERMINISTE des fichiers app/{route}/actions.ts depuis ProjectSpec.

Chaque actions.ts expose 3 Server Actions CRUD standard :
  createXxx(formData)        — auth guard + Zod + service.create + revalidatePath
  updateXxx(id, formData)    — auth guard + Zod + service.update + revalidatePath
  deleteXxx(id)              — auth guard + service.delete + revalidatePath + redirect

Règle de routage :
  Le fichier est écrit dans app/{list_page}/actions.ts où list_page est résolu
  par _find_list_page() : correspondance exacte d'abord, puis starts-with du
  premier segment kebab. Gère LeaveRequest → /leaves (pas /leave-requests).

Intégration dans dev_graph.py (après generate_service_files) :
    action_files = generate_action_files(spec_obj, project_workdir)
    template_written.update(action_files)
"""
from __future__ import annotations

import logging
import os
import re as _re

logger = logging.getLogger(__name__)


def _pascal_to_camel(name: str) -> str:
    """PascalCase → camelCase. Ex: LeaveRequest → leaveRequest"""
    return name[0].lower() + name[1:] if name else name


def _pascal_to_kebab(name: str) -> str:
    """PascalCase → kebab-case. Ex: LeaveRequest → leave-request"""
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _pluralize(word: str) -> str:
    """
    Pluralise un mot kebab-case en anglais.
    Règles par ordre de priorité :
      1. -y après consonne → -ies  (company→companies, category→categories)
      2. -s/-sh/-ch/-x/-z  → -es
      3. défaut             → -s
    Pas de table : les règles couvrent tous les cas réguliers.
    """
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "sh", "ch", "x", "z")):
        return word + "es"
    return word + "s"


def _find_list_page(model_name: str, spec) -> str:
    """
    Résout le chemin de la page liste pour un modèle.

    Ordre de résolution :
      1. Exact    : /{kebab} ou /{pluralize(kebab)} dans spec.pages
      2. Segment  : premier segment du chemin de page commence par le radical du kebab
                    → cherche dans spec.pages (sans [dynamic]) en priorité sur spec
      3. Fallback : /{pluralize(kebab)}

    Exemples :
      LeaveRequest → "leave-request" → base "leave" → /leaves ✓
      Company      → _pluralize("company") = "companies" → /companies ✓
      Project      → _pluralize("project") = "projects"  → /projects ✓
    """
    kebab = _pascal_to_kebab(model_name)
    plural = _pluralize(kebab)

    list_pages = [p.path for p in spec.pages if "[" not in p.path]

    # 1. Exact match — singulier puis pluriel
    if f"/{kebab}" in list_pages:
        return f"/{kebab}"
    if f"/{plural}" in list_pages:
        return f"/{plural}"

    # 2. Premier segment du chemin commence par le radical kebab
    #    Ex: "leave-request" → radical "leave" → /leaves, /leave-requests
    base = kebab.split("-")[0]
    for page_path in list_pages:
        first_seg = page_path.lstrip("/").split("/")[0]
        if first_seg.startswith(base):
            return page_path

    # 3. Fallback : pluriel calculé
    return f"/{plural}"


def _generate_actions_for_model(model, list_page: str) -> str:
    """
    Génère le contenu complet du fichier actions.ts pour un modèle.

    Auth pattern : const { userId } = await auth() + redirect si absent.
    Service call : toujours userId en premier arg — TypeScript correct
    (le service accepte string; le nom du param est cosmétique).
    """
    name = model.name
    camel = _pascal_to_camel(name)
    kebab = _pascal_to_kebab(name)

    lines = [
        "// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER",
        "'use server'",
        "",
        "import { auth } from '@clerk/nextjs/server'",
        "import { redirect } from 'next/navigation'",
        "import { revalidatePath } from 'next/cache'",
        f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'",
        f"import {{ Create{name}Schema, Update{name}Schema }} from '@/lib/schemas'",
        "",
        f"export async function create{name}(formData: FormData) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        f"  const validated = Create{name}Schema.parse(Object.fromEntries(formData) as Record<string, unknown>)",
        f"  await {camel}Service.create(userId, validated)",
        f"  revalidatePath('{list_page}')",
        "}",
        "",
        f"export async function update{name}(id: string, formData: FormData) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        f"  const validated = Update{name}Schema.parse(Object.fromEntries(formData) as Record<string, unknown>)",
        f"  await {camel}Service.update(id, validated)",
        f"  revalidatePath('{list_page}')",
        "}",
        "",
        f"export async function delete{name}(id: string) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        f"  await {camel}Service.delete(userId, id)",
        f"  revalidatePath('{list_page}')",
        f"  redirect('{list_page}')",
        "}",
        "",
    ]

    return "\n".join(lines)


def generate_action_files(spec, project_workdir: str) -> dict[str, str]:
    """
    Génère un fichier actions.ts par modèle Prisma et les écrit sur le disque.
    Retourne un dict {chemin_relatif: contenu} pour intégration dans template_written.

    Collision : si deux modèles se résolvent vers le même list_page (ex: Contact + Note → /contacts),
    un warning est logué et le second fichier fusionne les actions dans le même fichier.
    """
    # Regroupe les modèles par list_page pour gérer les collisions
    page_to_models: dict[str, list] = {}
    for model in spec.models:
        list_page = _find_list_page(model.name, spec)
        page_to_models.setdefault(list_page, []).append(model)

    written: dict[str, str] = {}

    for list_page, models in page_to_models.items():
        route_dir = list_page.lstrip("/")
        rel_path = f"app/{route_dir}/actions.ts"

        if len(models) > 1:
            logger.warning(
                "[action_generator] %d modèles sur la même page '%s' : %s — actions fusionnées",
                len(models), list_page, [m.name for m in models],
            )
            # Fusion : header commun + blocs de chaque modèle
            parts = [
                "// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER",
                "'use server'",
                "",
                "import { auth } from '@clerk/nextjs/server'",
                "import { redirect } from 'next/navigation'",
                "import { revalidatePath } from 'next/cache'",
            ]
            for m in models:
                camel = _pascal_to_camel(m.name)
                kebab = _pascal_to_kebab(m.name)
                parts.append(f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'")
            for m in models:
                parts.append(
                    f"import {{ Create{m.name}Schema, Update{m.name}Schema }} from '@/lib/schemas'"
                )
            parts.append("")
            for m in models:
                parts.append(_actions_block(m, list_page))
            content = "\n".join(parts)
        else:
            content = _generate_actions_for_model(models[0], list_page)

        abs_dir = os.path.join(project_workdir, "app", route_dir)
        os.makedirs(abs_dir, exist_ok=True)
        abs_path = os.path.join(abs_dir, "actions.ts")

        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            written[rel_path] = content
            logger.info(
                "[action_generator] ✓ %s généré (%d modèle(s))",
                rel_path, len(models),
            )
        except Exception as e:
            logger.error("[action_generator] ✗ Erreur écriture %s : %s", rel_path, e)

    return written


def _actions_block(model, list_page: str) -> str:
    """Génère uniquement les 3 fonctions d'un modèle (sans header imports) pour fusion."""
    name = model.name
    camel = _pascal_to_camel(name)
    kebab = _pascal_to_kebab(name)

    lines = [
        f"export async function create{name}(formData: FormData) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        f"  const validated = Create{name}Schema.parse(Object.fromEntries(formData) as Record<string, unknown>)",
        f"  await {camel}Service.create(userId, validated)",
        f"  revalidatePath('{list_page}')",
        "}",
        "",
        f"export async function update{name}(id: string, formData: FormData) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        f"  const validated = Update{name}Schema.parse(Object.fromEntries(formData) as Record<string, unknown>)",
        f"  await {camel}Service.update(id, validated)",
        f"  revalidatePath('{list_page}')",
        "}",
        "",
        f"export async function delete{name}(id: string) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        f"  await {camel}Service.delete(userId, id)",
        f"  revalidatePath('{list_page}')",
        f"  redirect('{list_page}')",
        "}",
        "",
    ]
    return "\n".join(lines)


def format_action_map_for_prompt(spec) -> str:
    """
    Génère un bloc compact injectable dans le prompt LLM.
    Expose les signatures COMPLÈTES des Server Actions pré-générées.
    Le LLM voit (formData: FormData) → il sait comment appeler depuis un Client Component.
    """
    if not spec or not getattr(spec, "models", None):
        return ""

    lines = [
        "### Action Map (Server Actions pré-générées — NE PAS recréer ces fichiers)\n",
        "SIGNATURES : create/update reçoivent `formData: FormData` | delete reçoit `id: string`.",
        "APPEL create/update : const fd = new FormData(); fd.set('field', val); await createXxx(fd)   ← NE PAS passer { field } → TS2353",
        "APPEL delete        : await deleteXxx(item.id)   ← id string, PAS FormData → TS2345 fatal\n",
    ]
    for model in spec.models:
        name = model.name
        list_page = _find_list_page(name, spec)
        route_dir = list_page.lstrip("/")
        file_path = f"app/{route_dir}/actions.ts"
        lines.append(f"**{file_path}** :")
        lines.append(f"  create{name}(formData: FormData) → revalidatePath('{list_page}')")
        lines.append(f"  update{name}(id: string, formData: FormData) → revalidatePath('{list_page}')")
        lines.append(f"  delete{name}(id: string) → revalidatePath + redirect('{list_page}')")
        lines.append("")

    return "\n".join(lines)
