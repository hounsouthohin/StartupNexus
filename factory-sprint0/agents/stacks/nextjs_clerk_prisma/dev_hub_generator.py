"""
dev_hub_generator.py — Génération déterministe de app/dashboard/page.tsx

Deux cas, tous deux déterministes :
  1. Dashboard simple (aucun kpi/liste déclaré) → grille de compteurs par modèle.
  2. Dashboard riche (kpis / filtered_lists déclarés par l'architect) → KPIs calculés
     + listes filtrées, à partir du contrat structuré.

Pourquoi déterministe : le calcul d'un KPI ou d'une liste filtrée a UNE seule réponse
juste. Avant, il était compilé en TypeScript exact puis injecté au LLM en PROSE ; le LLM
réécrivait le dashboard et reprenait `getAll(userId)` paginé → agrégat faux (violation C1).
Ici le calcul est écrit directement, dé-paginé, impossible à corrompre.

Les expressions KPI/liste (compile_kpi_expr / compile_flist_expr / unpaginate_call) vivent
ICI et nulle part ailleurs — dev_graph les importe si besoin.
"""
from __future__ import annotations

import logging
import pathlib
import re

logger = logging.getLogger(__name__)

PAGINATED_METHODS = ("getAll", "getAllWithRelations", "getPublicAll", "getPublished")


# ── Compilation contrat → TypeScript exact (source unique) ────────────────────

def unpaginate_call(call: str) -> str:
    """`svc.getAll(userId)` → `svc.getAll(userId, 1, 100000)` — charge tout pour agréger."""
    m = re.match(r"^(\w+\.(\w+))\((.*)\)\s*$", (call or "").strip())
    if not m or m.group(2) not in PAGINATED_METHODS:
        return call
    args = m.group(3).strip()
    return m.group(1) + "(" + (args + ", 1, 100000" if args else "1, 100000") + ")"


def compile_kpi_expr(kpi: dict) -> str:
    """Contrat KPI → expression TS (count / sum / avg, filtre optionnel). Sans f-string
    pour éviter tout piège d'accolades."""
    src = kpi["source"]
    if kpi.get("filter_field") and kpi.get("filter_value"):
        base = src + ".filter(x => String(x." + kpi["filter_field"] + ") === '" + kpi["filter_value"] + "')"
    else:
        base = src
    agg = kpi.get("agg", "count")
    fld = kpi.get("field", "")
    if agg == "sum" and fld:
        return base + ".reduce((s, x) => s + (Number(x." + fld + ") || 0), 0)"
    if agg == "avg" and fld:
        return ("(" + base + ".length ? " + base + ".reduce((s, x) => s + (Number(x." + fld
                + ") || 0), 0) / " + base + ".length : 0)")
    return base + ".length"


def compile_flist_expr(flist: dict) -> str:
    """Contrat liste filtrée → expression .filter() (eq / within_days / before / after)."""
    src = flist["source"]
    ff = flist["filter_field"]
    op = flist.get("filter_op", "eq")
    val = flist.get("filter_value", "")
    if op == "within_days":
        n = val if str(val).strip().isdigit() else "7"
        pred = ("{ const _d = new Date(x." + ff + " as string); const _now = new Date(); "
                "const _lim = new Date(); _lim.setDate(_now.getDate() + " + n + "); "
                "return _d >= _now && _d <= _lim }")
        return src + ".filter(x => " + pred + ")"
    if op == "before":
        return src + ".filter(x => new Date(x." + ff + " as string) < new Date())"
    if op == "after":
        return src + ".filter(x => new Date(x." + ff + " as string) > new Date())"
    return src + ".filter(x => String(x." + ff + ") === '" + val + "')"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _service_var(camel: str) -> str:
    return camel + "Service"


def _service_import(camel: str, kebab: str) -> str:
    return "import { " + _service_var(camel) + " } from '@/lib/services/" + kebab + ".service'"


def _camel_from_service(service_call: str) -> str | None:
    m = re.match(r"(\w+?)Service\.", service_call or "")
    return m.group(1) if m else None


def _ts_label(s: str) -> str:
    return str(s).replace("{", "").replace("}", "").replace("<", "").replace(">", "")


# ── Générateur principal ──────────────────────────────────────────────────────

def generate_hub_page(spec_obj, model_contexts: dict, project_workdir: str,
                      pages_detail: dict | None = None) -> dict[str, str]:
    """Génère app/dashboard/page.tsx (compteurs ou KPIs+listes). {path: content} ou {}."""
    if spec_obj is None or not model_contexts:
        return {}

    dash = None
    if pages_detail and isinstance(pages_detail, dict):
        dash = pages_detail.get("/dashboard") or pages_detail.get("dashboard")
    dash = dash if isinstance(dash, dict) else {}

    kpis = [k for k in (dash.get("kpis") or []) if isinstance(k, dict) and k.get("source")]
    flists = [f for f in (dash.get("filtered_lists") or [])
              if isinstance(f, dict) and f.get("source") and f.get("filter_field")]
    fetches = [f for f in (dash.get("data_fetches") or []) if isinstance(f, dict)]

    # Cas custom non couvert (data_fetches sans kpi ni liste : dashboard-liste libre) →
    # laisser le LLM. Le checker C1/C2 reste en garde-fou.
    if fetches and not kpis and not flists:
        logger.info("[hub_generator] /dashboard : data_fetches sans kpi/liste → LLM (checker en garde)")
        return {}

    if kpis or flists:
        content = _render_rich_dashboard(model_contexts, fetches, kpis, flists)
    else:
        content = _render_simple_dashboard(model_contexts)

    if not content:
        return {}

    dest = "app/dashboard/page.tsx"
    abs_path = pathlib.Path(project_workdir) / "app" / "dashboard" / "page.tsx"
    try:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        logger.info("[hub_generator] app/dashboard/page.tsx généré (%s)",
                    "riche" if (kpis or flists) else "compteurs")
    except Exception as _e:
        logger.warning("[hub_generator] écriture échouée : %s", _e)
        return {}
    return {dest: content}


def _public_detail_link(spec_obj, model_name: str) -> str | None:
    """Trouve la page détail PUBLIQUE d'un modèle → template de lien JS, ou None.
    Ex: page '/run-events/[id]' (auth=false) → "/run-events/${item.id}"."""
    for p in getattr(spec_obj, "pages", []) or []:
        if getattr(p, "model", None) != model_name:
            continue
        if getattr(p, "auth_required", True):
            continue
        _pt = getattr(p, "page_type", "") or ""
        _path = getattr(p, "path", "") or ""
        if _pt == "detail-slug" and "[slug]" in _path:
            return _path.replace("[slug]", "${item.slug}")
        if _pt in ("detail", "detail-slug") and "[id]" in _path:
            return _path.replace("[id]", "${item.id}")
    return None


def generate_public_home(spec_obj, model_contexts: dict, project_workdir: str,
                         pages_detail: dict | None = None) -> dict[str, str]:
    """Génère app/page.tsx PUBLIC de façon déterministe quand la home publique a une
    liste filtrée / des KPIs (ex: club « prochaines sorties »).

    Jumeau public de generate_hub_page : fetch dé-paginé (getPublicAll) + filtre compilé
    (compile_flist_expr) → C1 ne peut plus se déclencher (le LLM n'écrit plus cette page,
    et la source est dé-paginée + filtrée correctement). Retourne {} si non applicable.
    """
    if spec_obj is None or not model_contexts:
        return {}
    home = None
    if isinstance(pages_detail, dict):
        home = pages_detail.get("/") or pages_detail.get("")
    home = home if isinstance(home, dict) else {}

    flists = [f for f in (home.get("filtered_lists") or [])
              if isinstance(f, dict) and f.get("source") and f.get("filter_field")]
    kpis = [k for k in (home.get("kpis") or []) if isinstance(k, dict) and k.get("source")]
    fetches = [f for f in (home.get("data_fetches") or []) if isinstance(f, dict)]
    # Home publique statique ou sans agrégat → laissé aux autres générateurs (hero/redirect/LLM).
    if not (flists or kpis) or not fetches:
        return {}

    content = _render_public_home(model_contexts, spec_obj, fetches, kpis, flists)
    if not content:
        return {}
    dest = "app/page.tsx"
    abs_path = pathlib.Path(project_workdir) / "app" / "page.tsx"
    try:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        logger.info("[hub_generator] app/page.tsx PUBLIC déterministe (liste filtrée dé-paginée)")
    except Exception as _e:
        logger.warning("[hub_generator] écriture home publique échouée : %s", _e)
        return {}
    return {dest: content}


def _render_public_home(model_contexts: dict, spec_obj, fetches: list, kpis: list, flists: list) -> str:
    by_camel = {c.camel: c for c in model_contexts.values()}
    src_meta: dict[str, tuple] = {}
    for f in fetches:
        camel = _camel_from_service(f.get("service", ""))
        if f.get("as") and camel:
            ctx = by_camel.get(camel)
            src_meta[f["as"]] = (_service_var(camel), (ctx.kebab if ctx else camel), ctx, f.get("service", ""))

    used_sources = [s for s in ({k["source"] for k in kpis} | {f["source"] for f in flists}) if s in src_meta]
    if not used_sources:
        return ""

    imports = "\n".join(
        "import { " + src_meta[s][0] + " } from '@/lib/services/" + src_meta[s][1] + ".service'"
        for s in sorted(used_sources)
    )
    fetch_lines = "\n  ".join(
        "const " + s + " = await " + unpaginate_call(src_meta[s][3]) for s in sorted(used_sources)
    )

    kpi_consts, kpi_cards = [], []
    for i, k in enumerate(kpis):
        kpi_consts.append("const kpi" + str(i) + " = " + compile_kpi_expr(k))
        kpi_cards.append(
            '<div className="bg-card border border-border rounded-lg p-6">\n'
            '          <p className="text-sm text-muted-foreground mb-1">' + _ts_label(k.get("label", "")) + '</p>\n'
            '          <p className="text-3xl font-bold text-foreground">{kpi' + str(i) + '}</p>\n'
            '        </div>'
        )

    _needs_format_date = False
    list_consts, list_sections = [], []
    for i, f in enumerate(flists):
        list_consts.append("const list" + str(i) + " = " + compile_flist_expr(f))
        ctx = src_meta.get(f["source"], (None, None, None, None))[2]
        _date_names = {df.name for df in (ctx.datetime_fields or [])} if ctx else set()
        fields = (ctx.display_fields[:3] if ctx and ctx.display_fields else [])
        _detail = _public_detail_link(spec_obj, ctx.name) if ctx else None
        _cells = []
        for j, fld in enumerate(fields):
            if fld in _date_names:
                _needs_format_date = True
                _val = "{formatDate(item." + fld + ")}"
            else:
                _val = "{String(item." + fld + " ?? '')}"
            if j == 0 and _detail:
                _cells.append('<Link href={`' + _detail + '`} className="font-medium text-primary hover:underline">' + _val + '</Link>')
            else:
                _cells.append(_val)
        cells = " — ".join(_cells) if _cells else "{item.id}"
        list_sections.append(
            '<section className="mb-8">\n'
            '        <h2 className="text-lg font-semibold text-foreground mb-3">' + _ts_label(f.get("label", "")) + '</h2>\n'
            '        {list' + str(i) + '.length === 0 ? (\n'
            '          <p className="text-muted-foreground text-sm">Aucun élément.</p>\n'
            '        ) : (\n'
            '          <ul className="space-y-2">\n'
            '            {list' + str(i) + '.map(item => (\n'
            '              <li key={item.id} className="bg-card border border-border rounded-md p-4 text-sm text-foreground">' + cells + '</li>\n'
            '            ))}\n'
            '          </ul>\n'
            '        )}\n'
            '      </section>'
        )

    _fd_import = "\nimport { formatDate } from '@/lib/utils'" if _needs_format_date else ""
    consts_block = "\n  ".join(kpi_consts + list_consts)
    kpi_grid = (
        '<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">\n        '
        + "\n        ".join(kpi_cards) + "\n      </div>"
        if kpi_cards else ""
    )
    lists_block = "\n      ".join(list_sections)

    return f"""import Link from 'next/link'
{imports}{_fd_import}

export const dynamic = 'force-dynamic'

export default async function HomePage() {{
  {fetch_lines}

  {consts_block}

  return (
    <main className="container mx-auto p-8">
      {kpi_grid}
      {lists_block}
    </main>
  )
}}
"""


def _render_simple_dashboard(model_contexts: dict) -> str:
    """Grille de compteurs par modèle. Compteur = agrégat → getAll dé-paginé."""
    models = [c for c in model_contexts.values() if c.list_page_path]
    if not models:
        return ""

    imports = "\n".join(_service_import(c.camel, c.kebab) for c in models)
    promise_vars = ", ".join(c.camel + "Items" for c in models)
    promise_calls = ",\n    ".join(
        _service_var(c.camel) + ".getAll(userId, 1, 100000)" for c in models
    )
    count_lines = "\n  ".join(
        "const " + c.camel + "Count = " + c.camel + "Items.length" for c in models
    )
    cards = "\n        ".join(
        '<div className="bg-card border border-border rounded-lg p-6">\n'
        '          <p className="text-sm text-muted-foreground mb-1">' + _ts_label(c.title_plural) + '</p>\n'
        '          <p className="text-3xl font-bold text-foreground mb-4">{' + c.camel + 'Count}</p>\n'
        '          <Link href="' + c.list_page_path + '" className="text-sm text-primary hover:underline">Gérer →</Link>\n'
        '        </div>'
        for c in models
    )
    return f"""import Link from 'next/link'
import {{ auth }} from '@clerk/nextjs/server'
import {{ redirect }} from 'next/navigation'
{imports}

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {{
  const {{ userId }} = await auth()
  if (!userId) redirect('/sign-in')

  const [{promise_vars}] = await Promise.all([
    {promise_calls},
  ])

  {count_lines}

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards}
      </div>
    </main>
  )
}}
"""


def _render_rich_dashboard(model_contexts: dict, fetches: list, kpis: list, flists: list) -> str:
    """KPIs calculés + listes filtrées, à partir du contrat. Calcul déterministe,
    présentation cohérente (cartes + listes). La justesse est garantie ; la variété
    de l'app vient des KPIs choisis par l'architect, pas de la mise en page."""
    by_camel = {c.camel: c for c in model_contexts.values()}

    # source (as) -> (service_var, kebab, ctx, call)
    src_meta: dict[str, tuple] = {}
    for f in fetches:
        camel = _camel_from_service(f.get("service", ""))
        if f.get("as") and camel:
            ctx = by_camel.get(camel)
            src_meta[f["as"]] = (_service_var(camel), (ctx.kebab if ctx else camel), ctx, f.get("service", ""))

    used_sources = {k["source"] for k in kpis} | {f["source"] for f in flists}
    used_sources = [s for s in used_sources if s in src_meta]
    if not used_sources:
        return ""

    imports = "\n".join(
        "import { " + src_meta[s][0] + " } from '@/lib/services/" + src_meta[s][1] + ".service'"
        for s in sorted(used_sources)
    )
    fetch_lines = "\n  ".join(
        "const " + s + " = await " + unpaginate_call(src_meta[s][3]) for s in sorted(used_sources)
    )

    # KPIs — une const par KPI, puis une carte.
    kpi_consts, kpi_cards = [], []
    for i, k in enumerate(kpis):
        kpi_consts.append("const kpi" + str(i) + " = " + compile_kpi_expr(k))
        kpi_cards.append(
            '<div className="bg-card border border-border rounded-lg p-6">\n'
            '          <p className="text-sm text-muted-foreground mb-1">' + _ts_label(k.get("label", "")) + '</p>\n'
            '          <p className="text-3xl font-bold text-foreground">{kpi' + str(i) + '}</p>\n'
            '        </div>'
        )

    # Listes filtrées — une const par liste, puis une section.
    list_consts, list_sections = [], []
    _needs_format_date = False
    for i, f in enumerate(flists):
        list_consts.append("const list" + str(i) + " = " + compile_flist_expr(f))
        ctx = src_meta.get(f["source"], (None, None, None, None))[2]
        _date_names = {df.name for df in (ctx.datetime_fields or [])} if ctx else set()
        fields = (ctx.display_fields[:2] if ctx and ctx.display_fields else [])
        if fields:
            _cell_parts = []
            for fld in fields:
                if fld in _date_names:
                    _needs_format_date = True
                    _cell_parts.append("{formatDate(item." + fld + ")}")
                else:
                    _cell_parts.append("{String(item." + fld + " ?? '')}")
            cells = " — ".join(_cell_parts)
        else:
            cells = "{item.id}"
        list_sections.append(
            '<section className="mb-8">\n'
            '        <h2 className="text-lg font-semibold text-foreground mb-3">' + _ts_label(f.get("label", "")) + '</h2>\n'
            '        {list' + str(i) + '.length === 0 ? (\n'
            '          <p className="text-muted-foreground text-sm">Aucun élément.</p>\n'
            '        ) : (\n'
            '          <ul className="space-y-2">\n'
            '            {list' + str(i) + '.map(item => (\n'
            '              <li key={item.id} className="bg-card border border-border rounded-md p-3 text-sm text-foreground">' + cells + '</li>\n'
            '            ))}\n'
            '          </ul>\n'
            '        )}\n'
            '      </section>'
        )

    # Liens de gestion vers chaque entité.
    action_links = "\n        ".join(
        '<Link href="' + c.list_page_path + '" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer ' + _ts_label(c.title_plural) + '</Link>'
        for c in model_contexts.values() if c.list_page_path
    )

    if _needs_format_date:
        imports += "\nimport { formatDate } from '@/lib/utils'"

    consts_block = "\n  ".join(kpi_consts + list_consts)
    kpi_grid = (
        '<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">\n        '
        + "\n        ".join(kpi_cards) + "\n      </div>"
        if kpi_cards else ""
    )
    lists_block = "\n      ".join(list_sections)

    return f"""import Link from 'next/link'
import {{ auth }} from '@clerk/nextjs/server'
import {{ redirect }} from 'next/navigation'
{imports}

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {{
  const {{ userId }} = await auth()
  if (!userId) redirect('/sign-in')

  {fetch_lines}

  {consts_block}

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      {kpi_grid}
      {lists_block}
      <div className="flex flex-wrap gap-3">
        {action_links}
      </div>
    </main>
  )
}}
"""
