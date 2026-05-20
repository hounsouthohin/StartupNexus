"""
agents/stacks/nextjs_clerk_prisma/dev_form_generator.py
────────────────────────────────────────────────────────
Génération déterministe des page-client.tsx pour les pages CRUD standard.

PRINCIPE 4 : "Déterministe pour la forme, Agentique pour le sens"
Ce générateur couvre la forme (Tailwind, structure JSX, types, imports)
pour les 4 patterns CRUD universels : list, create, edit, detail.

Fichiers produits (tous ajoutés à template_written) :
  app/{list_path}/page-client.tsx            (list)
  app/{list_path}/new/page-client.tsx        (create)
  app/{list_path}/[id]/page-client.tsx       (detail, si déclarée)
  app/{list_path}/[id]/edit/page-client.tsx  (edit, si modèle CRUD)

Point d'entrée : generate_all_page_clients(spec, model_contexts, project_workdir)
"""
from __future__ import annotations

import logging
import os
import re as _re

from .dev_naming import (
    pascal_to_camel,
    pascal_to_plural_camel,
    path_to_client_component,
)
from .dev_model_context import ModelGenerationContext, FieldInfo, FKFieldInfo

logger = logging.getLogger(__name__)


# ── Helpers UI ────────────────────────────────────────────────────────────────

def _field_label(name: str) -> str:
    """categoryId → Category, firstName → First Name, title → Title"""
    n = name[:-2] if name.endswith("Id") else name
    words = _re.sub(r"([A-Z])", r" \1", n).strip().split()
    return " ".join(w.capitalize() for w in words) if words else n.capitalize()


_INPUT_CLASSES = "w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
_CHECKBOX_CLASSES = "h-4 w-4 rounded border-gray-300 text-blue-600"
_TEXTAREA_CLASSES = "w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px]"


def _label_jsx(name: str, required: bool) -> str:
    label = _field_label(name)
    req = ' <span className="text-red-500">*</span>' if required else ""
    return f'<label className="block text-sm font-medium text-gray-700 mb-1">{label}{req}</label>'


def _gen_field_input(field: FieldInfo, spec_enums: dict, prefix: str = "") -> list[str]:
    """
    Génère les lignes JSX pour un champ éditable.
    prefix = "item." pour les formulaires edit (defaultValue sur chaque champ).
    Retourne des lignes déjà indentées à 8 espaces (niveau field-wrapper).
    """
    name = field.name
    itype = field.input_type
    required = not field.is_optional and not field.has_default
    label_jsx = _label_jsx(name, required)
    req_attr = "\n            required" if required else ""

    lines: list[str] = ["        <div>"]

    if itype == "checkbox":
        checked_attr = f"\n              defaultChecked={{item.{name}}}" if prefix else ""
        lines += [
            "          <div className=\"flex items-center gap-2\">",
            f"            <input",
            f"              type=\"checkbox\"",
            f"              name=\"{name}\"",
            f"              className=\"{_CHECKBOX_CLASSES}\"{checked_attr}",
            f"            />",
            f'            <label className="text-sm font-medium text-gray-700">{_field_label(name)}</label>',
            "          </div>",
        ]
    elif itype == "enum-select":
        enum_values: list[str] = spec_enums.get(field.base_type, [])
        default_attr = f"\n            defaultValue={{item.{name}}}" if prefix else ""
        lines += [
            f"          {label_jsx}",
            f"          <select",
            f"            name=\"{name}\"",
            f"            className=\"{_INPUT_CLASSES}\"{default_attr}{req_attr}",
            f"          >",
        ]
        if not required:
            lines.append("            <option value=\"\">-- Sélectionner --</option>")
        for v in enum_values:
            lines.append(f"            <option value=\"{v}\">{v}</option>")
        lines.append("          </select>")
    elif itype == "textarea":
        default_attr = f"\n            defaultValue={{item.{name} ?? \"\"}}" if prefix else ""
        lines += [
            f"          {label_jsx}",
            f"          <textarea",
            f"            name=\"{name}\"",
            f"            className=\"{_TEXTAREA_CLASSES}\"{default_attr}{req_attr}",
            f"          />",
        ]
    elif itype == "datetime-local":
        if prefix:
            default_attr = (
                f"\n            defaultValue={{"
                f"\n              item.{name}"
                f"\n                ? new Date(item.{name}).toISOString().slice(0, 16)"
                f"\n                : \"\""
                f"\n            }}"
            )
        else:
            default_attr = ""
        lines += [
            f"          {label_jsx}",
            f"          <input",
            f"            type=\"datetime-local\"",
            f"            name=\"{name}\"",
            f"            className=\"{_INPUT_CLASSES}\"{default_attr}{req_attr}",
            f"          />",
        ]
    else:
        # text | number
        default_attr = f"\n            defaultValue={{item.{name} ?? \"\"}}" if prefix else ""
        lines += [
            f"          {label_jsx}",
            f"          <input",
            f"            type=\"{itype}\"",
            f"            name=\"{name}\"",
            f"            className=\"{_INPUT_CLASSES}\"{default_attr}{req_attr}",
            f"          />",
        ]

    lines.append("        </div>")
    return lines


def _gen_fk_select(fk: FKFieldInfo, display_field: str, prefix: str = "") -> list[str]:
    """
    Génère un <select> pour un champ FK.
    display_field : premier champ scalaire du modèle lié (ex: "title", "name").
    prefix = "item." pour les formulaires edit.
    Retourne des lignes indentées à 8 espaces.
    """
    label = _field_label(fk.field_name)
    var_name = f"{fk.related_camel}Options"
    default_attr = f"\n            defaultValue={{item.{fk.field_name}}}" if prefix else ""

    return [
        "        <div>",
        f"          <label className=\"block text-sm font-medium text-gray-700 mb-1\">"
        f"{label} <span className=\"text-red-500\">*</span></label>",
        f"          <select",
        f"            name=\"{fk.field_name}\"",
        f"            className=\"{_INPUT_CLASSES}\"",
        f"            required{default_attr}",
        f"          >",
        "            <option value=\"\">-- Sélectionner --</option>",
        f"            {{{var_name}.map(opt => (",
        f"              <option key={{opt.id}} value={{opt.id}}>{{opt.{display_field}}}</option>",
        "            ))}}",
        "          </select>",
        "        </div>",
    ]


def _related_display_field(fk: FKFieldInfo, model_contexts: dict) -> str:
    """Premier champ d'affichage du modèle lié, défaut 'id'."""
    ctx: ModelGenerationContext | None = model_contexts.get(fk.related_model)
    if ctx and ctx.display_fields:
        return ctx.display_fields[0]
    return "id"


# ── Générateurs individuels ───────────────────────────────────────────────────

def _gen_list_client(page, model_ctx: ModelGenerationContext) -> str:
    name = model_ctx.name
    camel = model_ctx.camel
    serialized = model_ctx.serialized_type
    list_path = model_ctx.list_page_path or f"/{model_ctx.kebab}s"
    client_name = path_to_client_component(page.path)
    display = model_ctx.display_fields[:2]

    lines: list[str] = [
        "'use client'",
        "",
        "import Link from 'next/link'",
        f"import {{ {serialized} }} from '@/lib/types'",
        f"import {{ delete{name} }} from './actions'",
        "",
        f"type Props = {{ items: {serialized}[] }}",
        "",
        f"export default function {client_name}({{ items }}: Props) {{",
        "  return (",
        "    <main className=\"container mx-auto p-6\">",
        "      <div className=\"flex justify-between items-center mb-6\">",
        f"        <h1 className=\"text-2xl font-bold text-gray-900\">{name}s</h1>",
        f"        <Link",
        f"          href=\"{list_path}/new\"",
        f"          className=\"px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium\"",
        f"        >",
        "          + Nouveau",
        "        </Link>",
        "      </div>",
        "",
        "      {items.length === 0 ? (",
        "        <div className=\"text-center py-12 text-gray-500\">",
        f"          <p className=\"text-lg\">Aucun {camel} pour le moment.</p>",
        f"          <Link href=\"{list_path}/new\" className=\"mt-4 inline-block text-blue-600 hover:underline text-sm\">",
        "            Créer le premier",
        "          </Link>",
        "        </div>",
        "      ) : (",
        "        <div className=\"overflow-x-auto rounded-lg border border-gray-200\">",
        "          <table className=\"min-w-full divide-y divide-gray-200\">",
        "            <thead>",
        "              <tr className=\"bg-gray-50\">",
    ]

    for df in display:
        lines.append(
            f"                <th className=\"px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider\">"
            f"{_field_label(df)}</th>"
        )
    lines += [
        "                <th className=\"px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider\">Actions</th>",
        "              </tr>",
        "            </thead>",
        "            <tbody className=\"divide-y divide-gray-200\">",
        "              {items.map(item => (",
        "                <tr key={item.id} className=\"hover:bg-gray-50\">",
    ]

    for df in display:
        lines.append(
            f"                  <td className=\"px-4 py-3 text-sm text-gray-700\">"
            f"{{item.{df} != null ? String(item.{df}) : '—'}}</td>"
        )

    lines += [
        "                  <td className=\"px-4 py-3 text-right\">",
        "                    <div className=\"flex justify-end gap-2\">",
        f"                      <Link",
        f"                        href={{`{list_path}/${{item.id}}/edit`}}",
        f"                        className=\"px-3 py-1 text-xs font-medium text-blue-600 border border-blue-600 rounded hover:bg-blue-50\"",
        f"                      >",
        "                        Modifier",
        "                      </Link>",
        f"                      <form action={{delete{name}}}>",
        "                        <input type=\"hidden\" name=\"id\" value={item.id} />",
        "                        <button",
        "                          type=\"submit\"",
        "                          className=\"px-3 py-1 text-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50\"",
        "                        >",
        "                          Supprimer",
        "                        </button>",
        "                      </form>",
        "                    </div>",
        "                  </td>",
        "                </tr>",
        "              ))}",
        "            </tbody>",
        "          </table>",
        "        </div>",
        "      )}",
        "    </main>",
        "  )",
        "}",
        "",
    ]
    return "\n".join(lines)


def _gen_create_client(page, model_ctx: ModelGenerationContext, model_contexts: dict) -> str:
    name = model_ctx.name
    list_path = model_ctx.list_page_path or f"/{model_ctx.kebab}s"
    client_name = path_to_client_component(page.path)
    fk_fields = model_ctx.fk_fields
    editable = model_ctx.editable_fields
    spec_enums = model_ctx.spec_enums

    # Imports des Serialized types pour les FK options
    fk_imports = [f"Serialized{fk.related_model}" for fk in fk_fields]
    type_imports = ", ".join(fk_imports) if fk_imports else ""

    # Type des Props
    fk_prop_fields = ", ".join(
        f"{fk.related_camel}Options: Serialized{fk.related_model}[]"
        for fk in fk_fields
    )
    fk_destructure = ", ".join(f"{fk.related_camel}Options" for fk in fk_fields)

    lines: list[str] = [
        "'use client'",
        "",
        "import Link from 'next/link'",
    ]
    if type_imports:
        lines.append(f"import {{ {type_imports} }} from '@/lib/types'")
    lines += [
        f"import {{ create{name} }} from './actions'",
        "",
    ]

    if fk_prop_fields:
        lines += [
            f"type Props = {{ {fk_prop_fields} }}",
            "",
            f"export default function {client_name}({{ {fk_destructure} }}: Props) {{",
        ]
    else:
        lines += [
            f"export default function {client_name}() {{",
        ]

    lines += [
        "  return (",
        "    <main className=\"container mx-auto p-6 max-w-xl\">",
        "      <div className=\"flex items-center gap-3 mb-6\">",
        f"        <Link href=\"{list_path}\" className=\"text-gray-400 hover:text-gray-600\">←</Link>",
        f"        <h1 className=\"text-2xl font-bold text-gray-900\">Nouveau {name}</h1>",
        "      </div>",
        f"      <form action={{create{name}}} className=\"space-y-4 bg-white rounded-lg border border-gray-200 p-6\">",
    ]

    for fk in fk_fields:
        display_field = _related_display_field(fk, model_contexts)
        for fk_line in _gen_fk_select(fk, display_field, prefix=""):
            lines.append(fk_line)

    for field in editable:
        for fline in _gen_field_input(field, spec_enums, prefix=""):
            lines.append(fline)

    lines += [
        "        <div className=\"pt-2 flex gap-3\">",
        "          <button",
        "            type=\"submit\"",
        "            className=\"px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium\"",
        "          >",
        "            Créer",
        "          </button>",
        f"          <Link",
        f"            href=\"{list_path}\"",
        f"            className=\"px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50\"",
        f"          >",
        "            Annuler",
        "          </Link>",
        "        </div>",
        "      </form>",
        "    </main>",
        "  )",
        "}",
        "",
    ]
    return "\n".join(lines)


def _gen_edit_client(model_ctx: ModelGenerationContext, model_contexts: dict) -> str:
    name = model_ctx.name
    serialized = model_ctx.serialized_type
    list_path = model_ctx.list_page_path or f"/{model_ctx.kebab}s"
    client_name = f"{name}EditClient"
    fk_fields = model_ctx.fk_fields
    editable = model_ctx.editable_fields
    spec_enums = model_ctx.spec_enums

    fk_imports = [f"Serialized{fk.related_model}" for fk in fk_fields]
    all_type_imports = [serialized] + fk_imports
    type_imports_str = ", ".join(all_type_imports)

    fk_prop_fields = ", ".join(
        f"{fk.related_camel}Options: Serialized{fk.related_model}[]"
        for fk in fk_fields
    )
    all_props = f"item: {serialized}" + (f", {fk_prop_fields}" if fk_prop_fields else "")
    fk_destructure = ", ".join(f"{fk.related_camel}Options" for fk in fk_fields)
    all_destructure = "item" + (f", {fk_destructure}" if fk_destructure else "")

    lines: list[str] = [
        "'use client'",
        "",
        "import Link from 'next/link'",
        f"import {{ {type_imports_str} }} from '@/lib/types'",
        f"import {{ update{name} }} from './actions'",
        "",
        f"type Props = {{ {all_props} }}",
        "",
        f"export default function {client_name}({{ {all_destructure} }}: Props) {{",
        "  return (",
        "    <main className=\"container mx-auto p-6 max-w-xl\">",
        "      <div className=\"flex items-center gap-3 mb-6\">",
        f"        <Link href=\"{list_path}\" className=\"text-gray-400 hover:text-gray-600\">←</Link>",
        f"        <h1 className=\"text-2xl font-bold text-gray-900\">Modifier {name}</h1>",
        "      </div>",
        f"      <form action={{update{name}}} className=\"space-y-4 bg-white rounded-lg border border-gray-200 p-6\">",
        "        <input type=\"hidden\" name=\"id\" value={item.id} />",
    ]

    for fk in fk_fields:
        display_field = _related_display_field(fk, model_contexts)
        for fk_line in _gen_fk_select(fk, display_field, prefix="item."):
            lines.append(fk_line)

    for field in editable:
        for fline in _gen_field_input(field, spec_enums, prefix="item."):
            lines.append(fline)

    lines += [
        "        <div className=\"pt-2 flex gap-3\">",
        "          <button",
        "            type=\"submit\"",
        "            className=\"px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium\"",
        "          >",
        "            Enregistrer",
        "          </button>",
        f"          <Link",
        f"            href=\"{list_path}\"",
        f"            className=\"px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50\"",
        f"          >",
        "            Annuler",
        "          </Link>",
        "        </div>",
        "      </form>",
        "    </main>",
        "  )",
        "}",
        "",
    ]
    return "\n".join(lines)


def _gen_detail_client(page, model_ctx: ModelGenerationContext) -> str:
    name = model_ctx.name
    serialized = model_ctx.serialized_type
    list_path = model_ctx.list_page_path or f"/{model_ctx.kebab}s"
    client_name = path_to_client_component(page.path)
    display_fields = model_ctx.display_fields
    editable = model_ctx.editable_fields

    # Champs à afficher : display_fields d'abord, puis les éditables restants
    shown: list[str] = list(display_fields)
    shown_set = set(display_fields)
    for f in editable:
        if f.name not in shown_set:
            shown.append(f.name)
            shown_set.add(f.name)

    lines: list[str] = [
        "'use client'",
        "",
        "import Link from 'next/link'",
        f"import {{ {serialized} }} from '@/lib/types'",
        "",
        f"type Props = {{ item: {serialized} }}",
        "",
        f"export default function {client_name}({{ item }}: Props) {{",
        "  return (",
        "    <main className=\"container mx-auto p-6 max-w-2xl\">",
        "      <div className=\"flex items-center gap-3 mb-6\">",
        f"        <Link href=\"{list_path}\" className=\"text-gray-400 hover:text-gray-600\">←</Link>",
        f"        <h1 className=\"text-2xl font-bold text-gray-900\">{name}</h1>",
        "      </div>",
        "      <div className=\"bg-white rounded-lg border border-gray-200 divide-y divide-gray-100\">",
    ]

    for fname in shown:
        label = _field_label(fname)
        lines += [
            "        <div className=\"px-6 py-4 flex justify-between items-start\">",
            f"          <span className=\"text-sm font-medium text-gray-500\">{label}</span>",
            f"          <span className=\"text-sm text-gray-900 text-right max-w-xs\">{{item.{fname} != null ? String(item.{fname}) : '—'}}</span>",
            "        </div>",
        ]

    lines += [
        "      </div>",
        "      <div className=\"mt-6 flex gap-3\">",
        f"        <Link",
        f"          href={{`{list_path}/${{item.id}}/edit`}}",
        f"          className=\"px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium\"",
        f"        >",
        "          Modifier",
        "        </Link>",
        f"        <Link",
        f"          href=\"{list_path}\"",
        f"          className=\"px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50\"",
        f"        >",
        "          Retour à la liste",
        "        </Link>",
        "      </div>",
        "    </main>",
        "  )",
        "}",
        "",
    ]
    return "\n".join(lines)


# ── Point d'entrée ────────────────────────────────────────────────────────────

def generate_all_page_clients(spec, model_contexts: dict, project_workdir: str) -> dict[str, str]:
    """
    Génère déterministiquement les page-client.tsx pour toutes les pages CRUD standard.
    Retourne {rel_path: content} pour intégration dans template_written.

    Couverture :
      list pages   → list client (table Tailwind + empty state + edit/delete)
      create pages → create form (FK selects + champs éditables)
      detail pages → detail view (display_fields + editable_fields)
      edit pages   → edit form (mêmes champs, defaultValues, hidden id)
    """
    written: dict[str, str] = {}
    pages = getattr(spec, "pages", []) or []

    # Déterminer les modèles CRUD complets (list auth + create) pour l'edit client
    crud_models: set[str] = set()
    has_create_models: set[str] = set()
    for p in pages:
        ptype = getattr(p, "page_type", None)
        pmodel = getattr(p, "model", None)
        if ptype == "list" and pmodel and getattr(p, "auth_required", True):
            crud_models.add(pmodel)
        if ptype == "create" and pmodel:
            has_create_models.add(pmodel)
    crud_models &= has_create_models

    # Pages list / create / detail
    for page in pages:
        model_name = getattr(page, "model", None)
        if not model_name:
            continue
        ctx = model_contexts.get(model_name)
        if ctx is None:
            continue

        page_type = getattr(page, "page_type", None)
        page_path_clean = page.path.strip("/")

        if page_type == "list":
            rel = f"app/{page_path_clean}/page-client.tsx" if page_path_clean else "app/page-client.tsx"
            content = _gen_list_client(page, ctx)
        elif page_type == "create":
            rel = f"app/{page_path_clean}/page-client.tsx"
            content = _gen_create_client(page, ctx, model_contexts)
        elif page_type in ("detail", "detail-slug"):
            rel = f"app/{page_path_clean}/page-client.tsx"
            content = _gen_detail_client(page, ctx)
        else:
            continue

        abs_path = os.path.join(project_workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        written[rel] = content
        logger.info("[form_gen] ✓ %s (model=%s type=%s)", rel, model_name, page_type)

    # Edit clients — générés depuis la liste des modèles CRUD
    for model in spec.models:
        if model.name not in crud_models:
            continue
        ctx = model_contexts.get(model.name)
        if ctx is None:
            continue
        list_path = ctx.list_page_path
        if not list_path:
            continue
        route = list_path.lstrip("/")
        rel = f"app/{route}/[id]/edit/page-client.tsx"
        content = _gen_edit_client(ctx, model_contexts)
        abs_path = os.path.join(project_workdir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        written[rel] = content
        logger.info("[form_gen] ✓ edit page-client : %s (model=%s)", rel, model.name)

    logger.info("[form_gen] %d page-client.tsx générés de manière déterministe", len(written))
    return written
