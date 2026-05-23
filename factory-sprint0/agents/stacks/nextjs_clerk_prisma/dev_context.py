"""
agents/dev_context.py
─────────────────────────────────────────────────────────────
Contextualisation Phase-Aware : pour chaque rôle de fichier généré,
injecte les dépendances disque + un standard RAG ciblé sur ce type
de fichier (P2.1 — bonne chronologie d'injection).

Séparé de dev_graph.py pour testabilité et ajout de rôles
sans grossir le monolithe executor_node.
"""
from __future__ import annotations

import logging
import os
import re as _re

logger = logging.getLogger(__name__)


# ── RAG ciblé par rôle (P2.1) ─────────────────────────────────────────────────
# Source de vérité : clé "role_rag_queries" dans nextjs-clerk-prisma.json (T0 refactor).
# Ce dict est le fallback statique utilisé si la stack config n'est pas accessible.
_ROLE_RAG_QUERIES_FALLBACK: dict[str, str] = {
    "service": (
        "N+1 prevention include select nested findUnique loop boucle Prisma Promise.all"
    ),
    "actions": (
        "auth userId guard obligatoire Zod validation safeParse revalidatePath throw Unauthorized"
    ),
    "route": (
        "auth guard NextResponse userId ownership API route handler"
    ),
    "page": (
        "Server Component auth redirect notFound dynamic params service getAll getById"
    ),
    "page_client": (
        "'use client' useState FormData handler Client Component interaction interactif"
    ),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_file_safe(path: str, limit: int) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:limit]
    except Exception:
        return ""


def _pascal_to_kebab(name: str) -> str:
    return _re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _find_service_for_segment(segment: str, spec_obj) -> tuple[str, str]:
    """
    Retourne (kebab_name, camelCaseService) en résolvant via spec_obj.pages.
    Compare le segment contre les composants non-dynamiques du chemin des pages
    ayant un modèle déclaré (AppPage.model). Aucune heuristique de pluriel.
    """
    if not spec_obj or not segment:
        return segment, segment + "Service"
    for page in spec_obj.pages:
        if not getattr(page, "model", None):
            continue
        path_segs = [s for s in page.path.split("/") if s and not s.startswith("[")]
        if segment in path_segs:
            kb = _pascal_to_kebab(page.model)
            camel = page.model[0].lower() + page.model[1:] + "Service"
            return kb, camel
    return segment, segment + "Service"


def _rag_for_role(role: str, cache: dict[str, str] | None = None) -> str:
    """Déclenche une requête Qdrant ciblée sur le rôle, retourne le bloc à injecter.

    cache — dict partagé par le run (clé = role). Evite N requêtes Qdrant identiques
    pour N fichiers du même rôle. Lifetime = un run (créé dans run_dev_agent).
    """
    try:
        from agents.stack_config import load_stack_config
        from agents.context import get_stack_id
        _queries = load_stack_config(get_stack_id()).get("role_rag_queries") or _ROLE_RAG_QUERIES_FALLBACK
    except Exception:
        _queries = _ROLE_RAG_QUERIES_FALLBACK
    query = _queries.get(role, "")
    if not query:
        return ""

    # Cache hit — même rôle déjà résolu dans ce run
    if cache is not None and role in cache:
        logger.debug("[role-rag] role=%-12s | cache hit", role)
        return cache[role]

    try:
        from agents.shared_tools import rag_search as _rag_fn
        result = _rag_fn.invoke({"query": query})
        if result and not result.startswith("[RAG]"):
            _n = len([s for s in result.split("---") if s.strip()])
            logger.info("[role-rag] role=%-12s | %d standard(s) injectés (miss)", role, _n)
            block = (
                f"\n\nSTANDARDS PERTINENTS POUR CE RÔLE ({role}) :\n"
                f"{result[:500]}"
            )
            if cache is not None:
                cache[role] = block
            return block
    except Exception:
        pass
    return ""


# ── Point d'entrée public ──────────────────────────────────────────────────────

def build_role_context(
    role: str,
    path: str,
    spec_obj,
    workdir: str,
    service_map_str: str = "",
    cache: dict[str, str] | None = None,
    manifest=None,
) -> str:
    """
    Construit le bloc de dépendances injecté dans le HumanMessage pour un fichier.

    Chaque rôle reçoit :
      - Dépendances disque exactes (types.ts, service.ts, schemas.ts, actions.ts…)
      - Standard RAG ciblé sur ce type de fichier (chronologie correcte)

    cache    — dict partagé pour le run courant (évite N requêtes Qdrant identiques
               pour N fichiers du même rôle). Passé depuis run_dev_agent via closure.
    manifest — LevelAManifest optionnel. Améliore la résolution service pour les
               pages custom (ex: /dashboard) où page.model n'est pas déclaré.
    """
    dep = _build_dep(role, path, spec_obj, workdir, service_map_str, manifest=manifest)

    # P2.1 — standard Qdrant injecté au bon moment (pas au démarrage du run)
    rag_block = _rag_for_role(role, cache=cache)
    if rag_block:
        dep += rag_block

    return dep


# ── Logique par rôle ───────────────────────────────────────────────────────────

def _build_dep(
    role: str,
    path: str,
    spec_obj,
    workdir: str,
    service_map_str: str,
    manifest=None,
) -> str:
    if role == "service":
        return _dep_service(workdir)
    elif role == "actions":
        return _dep_actions(path, spec_obj, workdir, service_map_str)
    elif role == "route":
        return _dep_route(path, workdir)
    elif role == "page_client":
        return _dep_page_client(path, spec_obj, workdir)
    elif role == "page":
        return _dep_page(path, spec_obj, workdir, manifest=manifest)
    return ""


def _dep_service(workdir: str) -> str:
    dep = ""
    for rel, limit in [("lib/types.ts", 800), ("lib/prisma.ts", 250)]:
        content = _read_file_safe(os.path.join(workdir, rel), limit)
        if content:
            dep += f"\n{rel} :\n```typescript\n{content}\n```"
    return dep


def _dep_actions(path: str, spec_obj, workdir: str, service_map_str: str) -> str:
    dep = ""
    if service_map_str:
        dep += f"\n{service_map_str}"

    schemas_content = _read_file_safe(os.path.join(workdir, "lib", "schemas.ts"), 600)
    if schemas_content:
        dep += f"\nlib/schemas.ts :\n```typescript\n{schemas_content}\n```"

    act_seg = path.split("/")[-2] if "/" in path else ""
    kb, _ = _find_service_for_segment(act_seg, spec_obj)
    svc_content = _read_file_safe(os.path.join(workdir, "lib", "services", f"{kb}.service.ts"), 500)
    if svc_content:
        dep += f"\nlib/services/{kb}.service.ts :\n```typescript\n{svc_content}\n```"

    return dep


def _dep_route(path: str, workdir: str) -> str:
    dep = ""
    types_content = _read_file_safe(os.path.join(workdir, "lib", "types.ts"), 800)
    if types_content:
        dep = f"\nlib/types.ts :\n```typescript\n{types_content}\n```"
    return dep


def _dep_page_client(path: str, spec_obj, workdir: str) -> str:
    dep = ""
    client_dir_parts = path.split("/")[:-1]  # ex: ['app', 'dashboard', 'recipes', 'new']

    # ── Route et modèle associé à ce page-client ────────────────────────────────
    _page_route = "/" + "/".join(client_dir_parts[1:])  # ex: '/dashboard/recipes/new'
    _client_model = None
    if spec_obj:
        for _pg in spec_obj.pages:
            if _pg.path.rstrip("/") == _page_route.rstrip("/"):
                if getattr(_pg, "model", None):
                    _client_model = next(
                        (m for m in spec_obj.models if m.name == _pg.model), None
                    )
                break

    # ── Injection page.tsx sibling (Bug 2B) ─────────────────────────────────────
    # Le Server Component parent est déjà sur disque (généré déterministe).
    # Le LLM voit exactement quelles props il passe → évite TS2322 sur FK props.
    _sibling_page_rel = "/".join(client_dir_parts) + "/page.tsx"
    _sibling_content = _read_file_safe(os.path.join(workdir, _sibling_page_rel), 500)
    if _sibling_content:
        dep += (
            f"\npage.tsx parent (Server Component qui rend ce Client Component) :\n"
            f"```typescript\n{_sibling_content}\n```\n"
            f"⚠️  Tes props DOIVENT correspondre EXACTEMENT à ce que page.tsx passe "
            f"(props manquantes ou en trop = TS2322 fatal).\n"
        )

    # ── Remonte l'arborescence pour trouver le actions.ts parent ────────────────
    for depth in range(len(client_dir_parts), 1, -1):
        act_rel = "/".join(client_dir_parts[:depth]) + "/actions.ts"
        act_abs = os.path.join(workdir, act_rel)
        if not os.path.exists(act_abs):
            continue

        depth_diff = len(client_dir_parts) - depth
        rel_import = ("../" * depth_diff + "actions") if depth_diff > 0 else "./actions"
        actions_content = _read_file_safe(act_abs, 600)
        dep += (
            f"\nactions.ts (chemin d'import relatif EXACT : '{rel_import}') :\n"
            f"```typescript\n{actions_content}\n```\n"
            f"⚠️  IMPORT OBLIGATOIRE : import {{ createXxx, deleteXxx }} from '{rel_import}'\n"
            f"⚠️  APPELS CORRECTS :\n"
            f"  create/update → FormData : const fd = new FormData(); fd.set('field', val); await createXxx(fd)\n"
            f"  delete → ID string : await deleteXxx(item.id)   ← PAS FormData, PAS objet plain"
        )

        # SerializedXxx type — champs EXACTS pour éviter TS2339
        if spec_obj and _client_model is None:
            act_segment = act_rel.split("/")[-2]
            for page in spec_obj.pages:
                if not getattr(page, "model", None):
                    continue
                path_segs = [s for s in page.path.split("/") if s and not s.startswith("[")]
                if act_segment in path_segs:
                    _client_model = next(
                        (m for m in spec_obj.models if m.name == page.model), None
                    )
                    break

        if _client_model:
            _types_raw = _read_file_safe(os.path.join(workdir, "lib", "types.ts"), 9999)
            _serial_key = f"export type Serialized{_client_model.name}"
            _t_start = _types_raw.find(_serial_key)
            if _t_start >= 0:
                _t_end = _types_raw.find("export type ", _t_start + len(_serial_key))
                _serial_type = _types_raw[
                    _t_start: _t_end if _t_end > _t_start else _t_start + 800
                ].strip()
                dep += (
                    f"\n\nType disponible (CHAMPS EXACTS — ne pas inventer d'autres) :\n"
                    f"```typescript\n{_serial_type}\n```"
                )
        break  # actions.ts trouvé

    else:
        # ── Fallback pages publiques (Bug 3) ────────────────────────────────────
        # Pas d'actions.ts → page publique. Injecter SerializedXxx depuis types.ts
        # directement + avertissement explicite : pas d'import ./actions.
        if _client_model:
            _types_raw = _read_file_safe(os.path.join(workdir, "lib", "types.ts"), 9999)
            _serial_key = f"export type Serialized{_client_model.name}"
            _t_start = _types_raw.find(_serial_key)
            if _t_start >= 0:
                _t_end = _types_raw.find("export type ", _t_start + len(_serial_key))
                _serial_type = _types_raw[
                    _t_start: _t_end if _t_end > _t_start else _t_start + 800
                ].strip()
                dep += (
                    f"\nType disponible (CHAMPS EXACTS — ne pas inventer d'autres) :\n"
                    f"```typescript\n{_serial_type}\n```\n"
                    f"⚠️  PAGE PUBLIQUE : PAS d'import depuis './actions' — "
                    f"ce fichier n'existe pas ici. NE PAS importer deleteXxx ni createXxx.\n"
                )

    # ── pages_detail hint — injecté pour TOUS les page-client (Trou B fix) ───────
    # Précédemment injecté seulement quand actions.ts trouvé → pages publiques l'ignoraient.
    if spec_obj is not None:
        try:
            from .dev_prompts import get_page_detail_hint
            detail_hint = get_page_detail_hint(spec_obj, _page_route)
            if detail_hint:
                dep += f"\n\n{detail_hint}"
        except Exception:
            pass

    return dep


def _dep_page(path: str, spec_obj, workdir: str, manifest=None) -> str:
    dep = ""
    seg = path.split("/")[-2] if path.count("/") >= 2 else ""

    if seg:
        kb, camel = _find_service_for_segment(seg, spec_obj)
        svc_content = _read_file_safe(
            os.path.join(workdir, "lib", "services", f"{kb}.service.ts"), 400
        )

        # Fallback manifest : si _find_service_for_segment n'a pas trouvé de service sur disque,
        # chercher via list_page_path (ex: /dashboard → Project si list_page_path=/dashboard/projects).
        if not svc_content and manifest is not None:
            try:
                from .level_a_manifest import find_model_for_path_segment
                mm = find_model_for_path_segment(manifest, seg)
                if mm is not None:
                    kb = mm.kebab
                    camel = mm.service_var
                    svc_content = _read_file_safe(
                        os.path.join(workdir, "lib", "services", f"{kb}.service.ts"), 400
                    )
            except Exception:
                pass

        if svc_content:
            dep = (
                f"\nlib/services/{kb}.service.ts"
                f" (import : import {{ {camel} }} from '@/lib/services/{kb}.service') :\n"
                f"```typescript\n{svc_content}\n```"
            )

    # page-client.tsx sibling — injecté si présent pour que page.tsx passe les bonnes props
    client_sibling = path.replace("/page.tsx", "/page-client.tsx")
    client_content = _read_file_safe(os.path.join(workdir, client_sibling), 500)
    if client_content:
        dep += (
            f"\npage-client.tsx (props à passer depuis ce Server Component) :\n"
            f"```typescript\n{client_content}\n```"
        )

    # page_detail_hint — contenu attendu pour cette page spécifiquement
    if spec_obj is not None:
        try:
            from .dev_prompts import get_page_detail_hint
            page_route = "/" + "/".join(path.split("/")[1:-1])
            detail_hint = get_page_detail_hint(spec_obj, page_route)
            if detail_hint:
                dep += f"\n\n{detail_hint}"
        except Exception:
            pass

    return dep
