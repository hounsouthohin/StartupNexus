"""
agents/dev_actions_generator.py
────────────────────────────────
Génération DÉTERMINISTE des fichiers app/{route}/actions.ts depuis ProjectSpec.

Chaque actions.ts expose 3 Server Actions CRUD standard :
  createXxx(formData)        — auth guard + Zod + service.create + revalidatePath
  updateXxx(id, formData)    — auth guard + Zod + service.update + revalidatePath
  deleteXxx(id)              — auth guard + service.delete + revalidatePath + redirect

Règle de routage :
  Le path list_page est résolu via spec.get_list_page_for_model(model.name)
  (ProjectSpec — source de vérité, voir GENERATOR_CONTRACT.md § 3).
  L'heuristique est encapsulée dans cette méthode, pas ici.

Intégration dans dev_graph.py (après generate_service_files) :
    action_files = generate_action_files(spec_obj, project_workdir)
    template_written.update(action_files)
"""
from __future__ import annotations

import logging
import os

from .dev_naming import pascal_to_camel, pascal_to_kebab

logger = logging.getLogger(__name__)


def _generate_actions_for_model(model, list_page: str) -> str:
    """
    Génère le contenu complet du fichier actions.ts pour un modèle.

    Auth pattern : const { userId } = await auth() + redirect si absent.
    Service call : toujours userId en premier arg — TypeScript correct
    (le service accepte string; le nom du param est cosmétique).
    """
    name = model.name
    camel = pascal_to_camel(name)
    kebab = pascal_to_kebab(name)

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
        f"  await {camel}Service.update(userId, id, validated)",
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
        list_page = spec.get_list_page_for_model(model.name)
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
                camel = pascal_to_camel(m.name)
                kebab = pascal_to_kebab(m.name)
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
    camel = pascal_to_camel(name)
    kebab = pascal_to_kebab(name)

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
        f"  await {camel}Service.update(userId, id, validated)",
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
        list_page = spec.get_list_page_for_model(name)
        route_dir = list_page.lstrip("/")
        file_path = f"app/{route_dir}/actions.ts"
        lines.append(f"**{file_path}** :")
        lines.append(f"  create{name}(formData: FormData) → revalidatePath('{list_page}')")
        lines.append(f"  update{name}(id: string, formData: FormData) → revalidatePath('{list_page}')")
        lines.append(f"  delete{name}(id: string) → revalidatePath + redirect('{list_page}')")
        lines.append("")

    return "\n".join(lines)
