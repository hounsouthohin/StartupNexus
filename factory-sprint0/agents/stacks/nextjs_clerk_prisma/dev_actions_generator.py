"""
agents/dev_actions_generator.py
────────────────────────────────
Génération DÉTERMINISTE des fichiers app/{route}/actions.ts depuis ProjectSpec.

Deux patterns de génération selon le type de modèle :

── Modèles standalone (Project, Task, Post…) — ont une page list dans le spec ──
  createXxx(formData)          — redirect(list_page)
  updateXxx(id, formData)      — redirect(list_page)
  deleteXxx(id)                — redirect(list_page)

── Modèles enfants CROSS_ENTITY (Comment, Module, Lesson…) — sans page list ──
  createXxx(formData)          — redirect vers page détail parent dynamique
                                  ex: redirect(`/tasks/${validated.taskId}`)
  updateXxx(id, formData)      — lit _redirectTo depuis formData (champ caché)
  deleteXxx(id, redirectTo)    — redirectTo passé explicitement par l'appelant

Détection enfant : ctx.list_page_path == "" ET ctx.fk_fields non vide.
La FK principale (fk_fields[0]) détermine le parent et le chemin de redirection.

Règle de routage (standalone) :
  Le path list_page est résolu via spec.get_list_page_for_model(model.name)
  (ProjectSpec — source de vérité, voir GENERATOR_CONTRACT.md § 3).

Intégration dans dev_graph.py (après generate_service_files) :
    action_files = generate_action_files(spec_obj, project_workdir, model_contexts)
    template_written.update(action_files)
"""
from __future__ import annotations

import logging
import os

from .dev_naming import pascal_to_camel, pascal_to_kebab

logger = logging.getLogger(__name__)


# ── Helpers pour la détection enfant ────────────────────────────────────────

def _is_child_model(ctx) -> bool:
    """
    True si le modèle est un enfant CROSS_ENTITY sans page liste standalone.
    Condition : pas de list_page_path résolu ET au moins un FK field vers un parent.
    """
    if ctx is None:
        return False
    has_list = bool(getattr(ctx, "list_page_path", ""))
    has_fk = bool(getattr(ctx, "fk_fields", None))
    return not has_list and has_fk


def _parent_paths(ctx, spec) -> tuple[str, str]:
    """
    Retourne (parent_list_path, fk_field_name) pour un modèle enfant.

    parent_list_path : chemin de la page list du modèle parent (ex: "/tasks")
    fk_field_name    : nom du champ FK principal (ex: "taskId")

    Utilise spec.get_list_page_for_model() pour résoudre le chemin du parent.
    Fallback : /{related_kebab}s si le parent n'a pas de page list déclarée.
    """
    fk = ctx.fk_fields[0]
    parent_list = (
        spec.get_list_page_for_model(fk.related_model)
        if spec else ""
    ) or f"/{pascal_to_kebab(fk.related_model)}s"
    return parent_list, fk.field_name


# ── Générateur principal ─────────────────────────────────────────────────────

def _m2m_parse_lines(schema: str, ctx, indent: str = "    ") -> list[str]:
    """
    Lignes TS de parsing du FormData vers le schema Zod.

    Sans M2M : Object.fromEntries direct (comportement historique).
    Avec M2M : Object.fromEntries PERD les valeurs multiples d'un <select multiple> —
    les ids M2M sont récupérés via formData.getAll() avant le parse.
    """
    m2m = list(getattr(ctx, "m2m_fields", []) or []) if ctx is not None else []
    if not m2m:
        return [f"{indent}const validated = {schema}.parse(Object.fromEntries(formData) as Record<string, unknown>)"]
    lines = [f"{indent}const _raw = Object.fromEntries(formData) as Record<string, unknown>"]
    for mf in m2m:
        lines.append(
            f"{indent}_raw.{mf.input_name} = formData.getAll('{mf.input_name}').map(String).filter(v => v.length > 0)"
        )
    lines.append(f"{indent}const validated = {schema}.parse(_raw)")
    return lines


def _generate_actions_for_model(model, list_page: str, ctx=None, spec=None) -> str:
    """
    Fichier actions.ts complet d'un modèle = EN-TÊTE + le bloc de fonctions.

    Fusionné le 17 Juil 2026 : ce fichier portait DEUX copies de la même logique
    (ici + `_actions_block` pour la fusion en cas de collision de list_page). Elles
    avaient déjà divergé — la copie collision n'avait pas le correctif `is_child`
    (revalidatePath après le catch → `validated` hors scope → TS2304).
    Une seule logique désormais : `_actions_block`.
    """
    name = model.name
    camel = pascal_to_camel(name)
    kebab = pascal_to_kebab(name)

    header = [
        "// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER",
        "'use server'",
        "",
        "import { auth } from '@clerk/nextjs/server'",
        "import { redirect } from 'next/navigation'",
        "import { revalidatePath } from 'next/cache'",
        "import { ZodError } from 'zod'",
        f"import {{ {camel}Service }} from '@/lib/services/{kebab}.service'",
        f"import {{ Create{name}Schema, Update{name}Schema }} from '@/lib/schemas'",
        "",
    ]
    return "\n".join(header) + "\n" + _actions_block(model, list_page, ctx=ctx, spec=spec)


def generate_action_files(
    spec,
    project_workdir: str,
    model_contexts: "dict | None" = None,
) -> dict[str, str]:
    """
    Génère un fichier actions.ts par modèle Prisma et les écrit sur le disque.
    Retourne un dict {chemin_relatif: contenu} pour intégration dans template_written.

    model_contexts : dict {model_name: ModelGenerationContext} passé depuis dev_graph.
    Quand fourni, ctx.list_page_path est la source de vérité (identique à ce que
    form_generator utilise) — élimine le couplage implicite par convention de nommage.

    Collision : si deux modèles se résolvent vers le même list_page (ex: Contact + Note → /contacts),
    un warning est logué et le second fichier fusionne les actions dans le même fichier.
    """
    # Modèles référencés explicitement dans au moins une page du spec
    # (les pages create ont model=None — elles sont couvertes via detail/list du même modèle)
    models_with_pages = {
        getattr(p, "model", None)
        for p in spec.pages
        if getattr(p, "model", None)
    }

    # Regroupe les modèles par list_page pour gérer les collisions.
    # Tous les modèles reçoivent un actions.ts — même les enfants CROSS_ENTITY sans
    # page standalone (ex: Comment dans tasks/[id]) ont besoin de deleteXxx côté client.
    page_to_models: dict[str, list] = {}
    ctx_by_model: dict[str, object] = {}

    for model in spec.models:
        if model.name not in models_with_pages:
            logger.info(
                "[action_generator] %s — aucune page standalone, actions générées quand même (CROSS_ENTITY child)",
                model.name,
            )
        ctx = (model_contexts or {}).get(model.name)
        ctx_by_model[model.name] = ctx

        # Pour les modèles enfants : list_page est une clé de regroupement unique.
        # On utilise app/comments/actions.ts comme chemin (heuristique conservée pour le path).
        # La LOGIQUE de redirect est dans _generate_actions_for_model, pas dans list_page.
        if _is_child_model(ctx):
            # L'heuristique /{kebab}s sert uniquement à choisir le répertoire de sortie,
            # pas à construire les redirects (qui utilisent le parent dynamique).
            file_key = f"/{pascal_to_kebab(model.name)}s"
        else:
            file_key = (
                (ctx.list_page_path if ctx else "")
                or spec.get_list_page_for_model(model.name)
                or f"/{pascal_to_kebab(model.name)}s"
            )
        page_to_models.setdefault(file_key, []).append(model)

    written: dict[str, str] = {}

    for file_key, models in page_to_models.items():
        route_dir = file_key.lstrip("/")
        rel_path = f"app/{route_dir}/actions.ts"

        if len(models) > 1:
            logger.warning(
                "[action_generator] %d modèles sur la même page '%s' : %s — actions fusionnées",
                len(models), file_key, [m.name for m in models],
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
            parts.append("import { ZodError } from 'zod'")
            parts.append("")
            for m in models:
                ctx = ctx_by_model.get(m.name)
                parts.append(_actions_block(m, file_key, ctx=ctx, spec=spec))
            content = "\n".join(parts)
        else:
            ctx = ctx_by_model.get(models[0].name)
            content = _generate_actions_for_model(models[0], file_key, ctx=ctx, spec=spec)

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


def _actions_block(model, list_page: str, ctx=None, spec=None) -> str:
    """Génère uniquement les 3 fonctions d'un modèle (sans header imports) pour fusion."""
    name = model.name
    camel = pascal_to_camel(name)

    is_child = _is_child_model(ctx)

    if is_child:
        parent_list, fk_field = _parent_paths(ctx, spec)
        create_revalidate = f"`{parent_list}/${{validated.{fk_field}}}`"
        create_redirect   = create_revalidate
        update_lines = [
            f"  const redirectTo = (formData.get('_redirectTo') as string) || '{parent_list}'",
            "  revalidatePath(redirectTo)",
            "  redirect(redirectTo)",
        ]
        delete_sig        = f"(id: string, redirectTo: string = '{parent_list}')"
        delete_revalidate = "redirectTo"
        delete_redirect   = "redirectTo"
    else:
        create_revalidate = f"'{list_page}'"
        create_redirect   = f"'{list_page}'"
        update_lines = [
            f"  revalidatePath('{list_page}')",
            f"  redirect('{list_page}')",
        ]
        delete_sig        = "(id: string)"
        delete_revalidate = f"'{list_page}'"
        delete_redirect   = f"'{list_page}'"

    # transition{Name} (type I) — chemin béni de changement d'état (appelle transitionTo).
    transition_lines: list[str] = []
    if ctx is not None and getattr(ctx, "status_flow", None) is not None:
        transition_lines = [
            "",
            f"export async function transition{name}(id: string, newStatus: string, formData: FormData) {{",
            "  const { userId } = await auth()",
            "  if (!userId) redirect('/sign-in')",
            "  try {",
            f"    const data = Update{name}Schema.parse(Object.fromEntries(formData) as Record<string, unknown>)",
            f"    await {camel}Service.transitionTo(userId, id, newStatus, data)",
            "  } catch (e) {",
            "    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))",
            "    throw new Error('Une erreur est survenue. Veuillez réessayer.')",
            "  }",
            *update_lines,
            "}",
        ]

    # Modèles ENFANTS : revalidatePath/redirect utilisent `validated.{fk}`, or `validated` est
    # const-scoped dans le try → le placer après le catch donne TS2304. D'où le corps distinct.
    # (Ce correctif n'existait QUE dans le chemin principal avant la fusion du 17 Juil —
    # le chemin collision produisait donc du TS2304 sur les modèles enfants.)
    if is_child:
        create_body_lines = [
            "  try {",
            *_m2m_parse_lines(f"Create{name}Schema", ctx),
            f"    await {camel}Service.create(userId, validated)",
            f"    revalidatePath({create_revalidate})",
            f"    redirect({create_redirect})",
            "  } catch (e) {",
            "    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))",
            "    throw new Error('Une erreur est survenue. Veuillez réessayer.')",
            "  }",
            "}",
        ]
    else:
        create_body_lines = [
            "  try {",
            *_m2m_parse_lines(f"Create{name}Schema", ctx),
            f"    await {camel}Service.create(userId, validated)",
            "  } catch (e) {",
            "    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))",
            "    throw new Error('Une erreur est survenue. Veuillez réessayer.')",
            "  }",
            f"  revalidatePath({create_revalidate})",
            f"  redirect({create_redirect})",
            "}",
        ]

    lines = [
        f"export async function create{name}(formData: FormData) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        *create_body_lines,
        "",
        f"export async function update{name}(id: string, formData: FormData) {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        "  try {",
        *_m2m_parse_lines(f"Update{name}Schema", ctx),
        f"    await {camel}Service.update(userId, id, validated)",
        "  } catch (e) {",
        "    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))",
        "    throw new Error('Une erreur est survenue. Veuillez réessayer.')",
        "  }",
        *update_lines,
        "}",
        *transition_lines,
        "",
        f"export async function delete{name}{delete_sig} {{",
        "  const { userId } = await auth()",
        "  if (!userId) redirect('/sign-in')",
        "  try {",
        f"    await {camel}Service.delete(userId, id)",
        "  } catch {",
        "    return { error: 'Impossible de supprimer cet élément.' }",
        "  }",
        f"  revalidatePath({delete_revalidate})",
        f"  redirect({delete_redirect})",
        "}",
        "",
    ]
    return "\n".join(lines)


def format_action_map_for_prompt(spec, model_contexts: "dict | None" = None) -> str:
    """
    Génère un bloc compact injectable dans le prompt LLM.
    Expose les signatures COMPLÈTES des Server Actions pré-générées.

    Pour les modèles enfants (CROSS_ENTITY), affiche les vraies signatures :
      deleteXxx(id, redirectTo)  au lieu de deleteXxx(id)
    afin que le LLM appelle correctement les actions depuis les page-clients.
    """
    if not spec or not getattr(spec, "models", None):
        return ""

    lines = [
        "### Action Map (Server Actions pré-générées — NE PAS recréer ces fichiers)\n",
        "SIGNATURES standalone : create/update reçoivent `formData: FormData` | delete reçoit `id: string`.",
        "SIGNATURES enfant     : delete reçoit `(id, redirectTo)` | create redirige vers parent automatiquement.",
        "APPEL create/update : const fd = new FormData(); fd.set('field', val); await createXxx(fd)   ← NE PAS passer { field } → TS2353",
        "APPEL delete standalone : await deleteXxx(item.id)",
        "APPEL delete enfant     : await deleteXxx(item.id, `/parent/${parentId}`)  ← redirectTo OBLIGATOIRE\n",
    ]
    for model in spec.models:
        name = model.name
        ctx = (model_contexts or {}).get(name)
        is_child = _is_child_model(ctx)

        if is_child:
            parent_list, fk_field = _parent_paths(ctx, spec)
            route_dir = pascal_to_kebab(name) + "s"
            file_path = f"app/{route_dir}/actions.ts"
            lines.append(f"**{file_path}** (modèle enfant CROSS_ENTITY) :")
            lines.append(f"  create{name}(formData: FormData) → redirect vers `{parent_list}/{{fk_field}}`")
            lines.append(f"  update{name}(id: string, formData: FormData) → lit _redirectTo dans formData")
            lines.append(f"  delete{name}(id: string, redirectTo: string = '{parent_list}') → redirect(redirectTo)")
        else:
            list_page = spec.get_list_page_for_model(name)
            if not list_page:
                continue
            route_dir = list_page.lstrip("/")
            file_path = f"app/{route_dir}/actions.ts"
            lines.append(f"**{file_path}** :")
            lines.append(f"  create{name}(formData: FormData) → redirect('{list_page}')")
            lines.append(f"  update{name}(id: string, formData: FormData) → redirect('{list_page}')")
            lines.append(f"  delete{name}(id: string) → redirect('{list_page}')")
        lines.append("")

    return "\n".join(lines)
