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
# Une requête Qdrant par type de fichier, injectée dans le HumanMessage
# au moment exact où le LLM écrit ce fichier — pas au démarrage du run.
_ROLE_RAG_QUERIES: dict[str, str] = {
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
    Retourne (kebab_name, camelCase_name) du service correspondant à un segment d'URL.
    Utilise _find_list_page (SSoT) pour une résolution stable — gère les pluriels
    irréguliers et les segments composés (leave-request → leaves, company → companies).
    Retourne (segment, segment+"Service") en fallback si aucun modèle trouvé.
    """
    try:
        from agents.dev_actions_generator import _find_list_page as _flp
        match = next(
            (m for m in (spec_obj.models if spec_obj else [])
             if _flp(m.name, spec_obj).lstrip("/") == segment),
            None,
        )
        if match:
            kb = _pascal_to_kebab(match.name)
            camel = _re.sub(r"-(.)", lambda m: m.group(1).upper(), kb) + "Service"
            return kb, camel
    except Exception:
        pass
    return segment, segment + "Service"


def _rag_for_role(role: str, cache: dict[str, str] | None = None) -> str:
    """Déclenche une requête Qdrant ciblée sur le rôle, retourne le bloc à injecter.

    cache — dict partagé par le run (clé = role). Evite N requêtes Qdrant identiques
    pour N fichiers du même rôle. Lifetime = un run (créé dans run_dev_agent).
    """
    query = _ROLE_RAG_QUERIES.get(role, "")
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
) -> str:
    """
    Construit le bloc de dépendances injecté dans le HumanMessage pour un fichier.

    Chaque rôle reçoit :
      - Dépendances disque exactes (types.ts, service.ts, schemas.ts, actions.ts…)
      - Standard RAG ciblé sur ce type de fichier (chronologie correcte)

    cache — dict partagé pour le run courant (évite N requêtes Qdrant identiques
    pour N fichiers du même rôle). Passé depuis run_dev_agent via closure.
    """
    dep = _build_dep(role, path, spec_obj, workdir, service_map_str)

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
        return _dep_page(path, spec_obj, workdir)
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

    # Service correspondant via SSoT _find_list_page
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

    # Service correspondant : app/api/{seg}/route.ts → lib/services/{seg}.service.ts
    route_segs = [
        s for s in path.split("/")
        if s not in ("app", "api", "route.ts", "") and not s.startswith("[")
    ]
    for seg in reversed(route_segs):
        for sv in [seg, seg.rstrip("s")]:
            svc_content = _read_file_safe(
                os.path.join(workdir, "lib", "services", f"{sv}.service.ts"), 600
            )
            if svc_content:
                dep += f"\nlib/services/{sv}.service.ts :\n```typescript\n{svc_content}\n```"
                return dep
    return dep


def _dep_page_client(path: str, spec_obj, workdir: str) -> str:
    dep = ""
    client_dir_parts = path.split("/")[:-1]  # ['app', 'projects', 'new']

    # Remonte l'arborescence pour trouver le actions.ts parent
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

        # SerializedXxx type — champs EXACTS pour éviter les hallucinations (TS2339)
        try:
            from agents.dev_actions_generator import _find_list_page as _flp
            act_segment = act_rel.split("/")[-2]
            client_model = next(
                (m for m in (spec_obj.models if spec_obj else [])
                 if _flp(m.name, spec_obj).lstrip("/") == act_segment),
                None,
            )
            if client_model:
                types_content = _read_file_safe(os.path.join(workdir, "lib", "types.ts"), 9999)
                serial_key = f"export type Serialized{client_model.name}"
                t_start = types_content.find(serial_key)
                if t_start >= 0:
                    t_end = types_content.find("export type ", t_start + len(serial_key))
                    serial_type = types_content[
                        t_start: t_end if t_end > t_start else t_start + 400
                    ].strip()
                    dep += (
                        f"\n\nType disponible (CHAMPS EXACTS — ne pas inventer d'autres) :\n"
                        f"```typescript\n{serial_type}\n```"
                    )
        except Exception:
            pass

        # page_detail_hint pour ce page-client
        if spec_obj is not None:
            try:
                from agents.dev_prompts import get_page_detail_hint
                page_route = "/" + "/".join(path.split("/")[1:-1])
                page_route = page_route.replace("/page-client", "")
                detail_hint = get_page_detail_hint(spec_obj, page_route)
                if detail_hint:
                    dep += f"\n\n{detail_hint}"
            except Exception:
                pass
        break  # actions.ts trouvé, pas besoin de remonter plus haut

    return dep


def _dep_page(path: str, spec_obj, workdir: str) -> str:
    dep = ""
    seg = path.split("/")[-2] if path.count("/") >= 2 else ""

    if seg:
        kb, camel = _find_service_for_segment(seg, spec_obj)
        svc_content = _read_file_safe(
            os.path.join(workdir, "lib", "services", f"{kb}.service.ts"), 400
        )
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
            from agents.dev_prompts import get_page_detail_hint
            page_route = "/" + "/".join(path.split("/")[1:-1])
            detail_hint = get_page_detail_hint(spec_obj, page_route)
            if detail_hint:
                dep += f"\n\n{detail_hint}"
        except Exception:
            pass

    return dep
