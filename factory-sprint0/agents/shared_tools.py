"""
shared_tools.py — Tous les @tools LangChain du factory worker.

Re-exporte également les helpers de context.py et observability.py
pour compatibilité avec les imports existants dans tout le pipeline.
"""

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Optional

try:
    from langchain_core.tools import tool
except ModuleNotFoundError:
    # Permet l'import de ce module dans des environnements de test allégés
    # où langchain_core n'est pas installé.
    def tool(func=None, *args, **kwargs):
        if func is None:
            def _decorator(f):
                return f
            return _decorator
        return func
from pydantic import BaseModel, Field

from agents.stack_config import _DEFAULT_STACK_ID
from config.factory_config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL,
    DEFAULT_VECTOR_SEARCH_LIMIT,
    SUBPROCESS_TIMEOUT_SHORT,
    SUBPROCESS_TIMEOUT_MEDIUM,
    SUBPROCESS_TIMEOUT_LONG,
)

# ── Re-exports pour compatibilité avec tous les imports existants ──────────────
from agents.context import set_run_id, get_run_id, set_stack_id, get_stack_id  # noqa: F401
from agents.observability import logger, _append_rag_usage_event, _write_learner_event  # noqa: F401

# ─────────────────────────────────────────────────────────────────────────────
# Qdrant singleton (lazy init)
# ─────────────────────────────────────────────────────────────────────────────
_qdrant_store = None
_qdrant_embeddings = None


def _get_qdrant_store():
    global _qdrant_store, _qdrant_embeddings
    # Vérifie que le client existant est toujours joignable (détecte un restart Qdrant)
    if _qdrant_store is not None:
        try:
            _qdrant_store.client.get_collections()
            return _qdrant_store
        except Exception:
            logger.warning("[qdrant] Store stale — reconnexion forcée")
            _qdrant_store = None
    try:
        from qdrant_client import QdrantClient
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore

        _qdrant_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        client = QdrantClient(url=QDRANT_URL)
        _qdrant_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION_NAME,
            embedding=_qdrant_embeddings,
            content_payload_key="text",
        )
        logger.info(f"[qdrant] Store initialisé: {QDRANT_URL}/{QDRANT_COLLECTION_NAME}")
        return _qdrant_store
    except Exception as e:
        logger.warning(f"[qdrant] Init failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internes
# ─────────────────────────────────────────────────────────────────────────────

def _get_runtime_stack_rules() -> str:
    """Retourne les règles de la stack active comme string (pour injection prompts)."""
    try:
        from agents.stack_config import load_stack_config
        cfg = load_stack_config(get_stack_id())
        prompt_rules = cfg.get("prompt_rules", {})
        lines = []
        for section, rules in prompt_rules.items():
            if isinstance(rules, list):
                for rule in rules:
                    if isinstance(rule, str):
                        lines.append(f"- [{section}] {rule}")
            elif isinstance(rules, dict):
                for k, v in rules.items():
                    lines.append(f"- [{section}] {k}: {v}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"_get_runtime_stack_rules failed: {e}")
        return ""


def _get_node_env() -> dict:
    """Retourne l'environnement pour les sous-processus Node.js."""
    env = os.environ.copy()
    env["CI"] = "true"
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    # Build deterministe: prisma generate nécessite DATABASE_URL même sans DB accessible.
    # Fallback local pour éviter les échecs de config Prisma quand seul .env.local est présent.
    env.setdefault("DATABASE_URL", "postgresql://user:password@localhost:5432/postgres")
    return env


def _json_filter_to_qdrant(filter_dict: dict):
    """
    Traduit un filtre JSON stack (qdrant_filter.filter) en Qdrant Filter model.
    Supporte : must[], should[] imbriqués, FieldCondition key+match.value.
    """
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    def _parse_condition(cond: dict):
        if "should" in cond:
            return Filter(should=[_parse_condition(c) for c in cond["should"]])
        if "must" in cond:
            return Filter(must=[_parse_condition(c) for c in cond["must"]])
        if "key" in cond:
            return FieldCondition(
                key=cond["key"],
                match=MatchValue(value=cond["match"]["value"]),
            )
        raise ValueError(f"[_json_filter_to_qdrant] Condition non reconnue: {cond}")

    must_raw = filter_dict.get("must", [])
    if not must_raw:
        return None
    return Filter(must=[_parse_condition(c) for c in must_raw])


def _build_rag_filter(stack_id: str):
    """
    Construit le filtre Qdrant depuis qdrant_filter.filter du JSON stack.
    Source de vérité : nextjs-clerk-prisma.json (résout Config-Runtime Drift).
    Fallback programmatique si la config est absente ou invalide.
    Retourne None si les modèles Qdrant ne sont pas disponibles.
    """
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        from agents.stack_config import get_qdrant_filter_cfg

        filter_cfg = get_qdrant_filter_cfg(stack_id).get("filter", {})
        if filter_cfg:
            return _json_filter_to_qdrant(filter_cfg)

        # Fallback si qdrant_filter absent du JSON
        logger.warning(
            f"[_build_rag_filter] qdrant_filter absent pour stack '{stack_id}' "
            "— fallback programmatique (ajouter qdrant_filter dans le JSON stack)"
        )
        return Filter(
            must=[
                Filter(
                    should=[
                        FieldCondition(key="metadata.stack", match=MatchValue(value=stack_id)),
                        FieldCondition(key="metadata.stack", match=MatchValue(value="global")),
                    ]
                ),
                FieldCondition(key="metadata.status", match=MatchValue(value="active")),
            ]
        )
    except Exception as e:
        logger.warning(f"[_build_rag_filter] Filtre Qdrant non disponible: {e}")
        return None


def _get_workdir() -> str:
    """
    Retourne le répertoire de travail pour les fichiers générés.
    Lit FACTORY_WORKDIR depuis l'environnement (défaut: '.').
    Crée le répertoire si nécessaire.
    """
    workdir = os.getenv("FACTORY_WORKDIR", ".")
    if workdir != ".":
        os.makedirs(workdir, exist_ok=True)
    return workdir


MAX_FILE_SIZE_BYTES = 500_000
MAX_OUTPUT_CHARS = 4000


def _truncate_output(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n...[TRONQUÉ {len(text)} chars total]...\n" + text[-half:]


def _resolve_safe_path(path: str, base_dir: str) -> str:
    """
    Résout un chemin de façon sécurisée par rapport à base_dir.
    Empêche les path traversal (../../etc/passwd).
    """
    base = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base, path))
    if not candidate.startswith(base):
        raise ValueError(f"Path traversal détecté: {path!r} sort de {base!r}")
    return candidate


def _normalize_guard_path(path: str) -> str:
    """
    Normalise un chemin relatif pour comparaisons de guards (templates, etc.).
    Exemple: './lib//prisma.ts' -> 'lib/prisma.ts'
    """
    p = (path or "").replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    p = str(PurePosixPath(p))
    if p.startswith("/"):
        p = p[1:]
    if p == ".":
        return ""
    return p



# ─────────────────────────────────────────────────────────────────────────────
# Tool: rag_search
# ─────────────────────────────────────────────────────────────────────────────

@tool
def rag_search(query: str, k: int = DEFAULT_VECTOR_SEARCH_LIMIT) -> str:
    """
    Recherche les standards techniques pertinents dans la base RAG (Qdrant).
    Utilise l'embedding pour trouver les k documents les plus similaires à la query.
    Retourne le texte des documents trouvés avec leurs scores et catégories.
    """
    run_id = get_run_id()
    store = _get_qdrant_store()

    if store is None:
        _append_rag_usage_event(
            query=query, k=k, cache_hit=False, run_id=run_id,
            error="Qdrant unavailable"
        )
        return "[RAG] Qdrant indisponible — continuer sans contexte RAG."

    try:
        max_docs = max(1, min(k, int(os.getenv("RAG_MAX_RETURN_DOCS", "4"))))
        max_doc_chars = max(120, int(os.getenv("RAG_DOC_MAX_CHARS", "700")))
        # Filtre sur la stack active + status=active (Config-Runtime Drift #26 résolu)
        qdrant_filter = _build_rag_filter(get_stack_id())
        docs = store.similarity_search_with_score(query, k=k, filter=qdrant_filter)

        # Fallback sans filtre si aucun résultat (ex: collection pas encore migrée)
        if not docs and qdrant_filter is not None:
            logger.warning(
                "[rag_search] Aucun résultat avec filtre stack — fallback sans filtre. "
                "Vérifier: reset_qdrant.py + create_full_standards_v1.py ont-ils été exécutés ?"
            )
            docs = store.similarity_search_with_score(query, k=k)

        if not docs:
            _append_rag_usage_event(
                query=query, k=k, cache_hit=False, run_id=run_id,
                doc_ids=[], scores=[], snippet=""
            )
            return f"[RAG] Aucun résultat pour: {query}"

        # Déduplication sémantique légère pour réduire le bruit contexte.
        # Même document (ou quasi-identique) peut remonter plusieurs fois.
        deduped = []
        seen_keys = set()
        for doc, score in docs:
            key = re.sub(r"\s+", " ", (doc.page_content or "").strip().lower())
            if not key:
                continue
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append((doc, score))
            if len(deduped) >= max_docs:
                break

        doc_ids = []
        scores = []
        results = []
        for doc, score in deduped:
            doc_id = str(getattr(doc, "id", "") or "")
            doc_ids.append(doc_id)
            scores.append(float(score))
            category = doc.metadata.get("category", "general")
            content = (doc.page_content or "")[:max_doc_chars]
            results.append(f"[{category}] score={score:.3f}\n{content}")

        snippet = deduped[0][0].page_content[:180] if deduped else ""
        _append_rag_usage_event(
            query=query, k=k, cache_hit=False, run_id=run_id,
            doc_ids=doc_ids, scores=scores, snippet=snippet
        )
        return "\n\n---\n\n".join(results)

    except Exception as e:
        _append_rag_usage_event(
            query=query, k=k, cache_hit=False, run_id=run_id, error=str(e)
        )
        logger.error(f"[rag_search] Error: {e}")
        return f"[RAG ERROR] {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Sanitizers (appliqués dans write_file)
# ─────────────────────────────────────────────────────────────────────────────

def _is_test_file_path(path: str) -> bool:
    """Retourne True si le chemin correspond à un fichier de test."""
    p = path.replace("\\", "/")
    return (
        "/tests/" in p
        or p.startswith("tests/")
        or ".test." in p
        or ".spec." in p
        or "__tests__" in p
    )


def _apply_import_remaps(content: str, path: str) -> str:
    """Applique les remappings d'imports définis dans la stack config."""
    try:
        from agents.stack_config import get_import_remaps
        remaps = get_import_remaps(get_stack_id())
    except Exception:
        return content

    is_test = _is_test_file_path(path)
    is_ts = path.endswith((".ts", ".tsx", ".js", ".jsx"))

    if is_ts:
        fixes = dict(remaps.get("source_fixes", {}))
        if is_test:
            fixes.update(remaps.get("test_fixes", {}))
        for old, new in fixes.items():
            content = content.replace(old, new)
        for old, new in remaps.get("router_fixes", {}).items():
            content = content.replace(old, new)

    return content


def _apply_package_fixes(content: str) -> str:
    """Applique les remappings de packages dans package.json."""
    try:
        from agents.stack_config import get_import_remaps
        remaps = get_import_remaps(get_stack_id())
        for old, new in remaps.get("package_fixes", {}).items():
            content = content.replace(f'"{old}"', f'"{new}"')
    except Exception:
        pass
    return content


def _fix_json_escaping(content: str) -> str:
    """
    Corrige le contenu JSON sur-échappé par le LLM.
    Symptôme : le LLM passe '\\n' (deux caractères) au lieu d'un vrai saut de ligne,
    ce qui rend le JSON invalide pour npm (EJSONPARSE position 1).
    Stratégie : si le contenu est du JSON invalide mais devient valide après
    décodage unicode_escape, on retourne la version corrigée formatée.
    """
    try:
        json.loads(content)
        return content  # Déjà valide, rien à faire
    except json.JSONDecodeError:
        pass
    try:
        fixed = content.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
        parsed = json.loads(fixed)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception:
        pass
    # Fallback minimal : remplacer les séquences littérales les plus communes
    fixed = content.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
    return fixed


def _ensure_tsconfig_excludes_tests(content: str) -> str:
    """
    Assure que le répertoire tests/ est exclu du build TypeScript (next build).
    Jest compile les tests séparément — les inclure dans next build provoque
    TS5070 'differs from already included file name only in casing' sur Linux.
    """
    try:
        cfg = json.loads(content)
        exclude = cfg.setdefault("exclude", [])
        if "tests/**" not in exclude:
            exclude.append("tests/**")
        return json.dumps(cfg, indent=2, ensure_ascii=False)
    except Exception:
        return content


_CODE_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".scss", ".prisma")


def _fix_literal_newlines(path: str, content: str) -> str:
    """
    Corrige les fichiers où le LLM a écrit \\n comme texte littéral (double-escape JSON)
    au lieu de vraies newlines.
    Signature du bug : le contenu n'a aucune vraie newline mais contient des \\n.
    """
    if not any(path.endswith(ext) for ext in _CODE_EXTENSIONS):
        return content
    if "\n" not in content and "\\n" in content:
        content = content.replace("\\n", "\n").replace("\\t", "\t")
    return content


def _fix_escaped_jsx_attr_quotes(path: str, content: str) -> str:
    """
    Corrige un artefact LLM fréquent en JSX/TSX:
      className=\\"...\\"
    qui provoque des erreurs de parsing "Unexpected token `div`".
    """
    if not path.endswith((".tsx", ".jsx")):
        return content
    # Ne corrige que les séquences d'attribut JSX, pas les chaînes arbitraires.
    content = re.sub(r"(\b[A-Za-z_:][A-Za-z0-9_:\-]*=)\\+\"", r'\1"', content)
    content = re.sub(r"\\+\"([>\s])", r'"\1', content)
    return content


def _fix_overescaped_tsx_source(path: str, content: str) -> str:
    """
    Corrige les fichiers TSX/JSX entièrement sur-échappés par le LLM, par exemple:
      \"use client\";\
      import { useState } from 'react';\
    qui provoquent "Expected unicode escape" au build.
    """
    if not path.endswith((".tsx", ".jsx")):
        return content

    if '\\"' not in content and "\\'" not in content:
        return content

    lines = content.splitlines()
    first_non_empty = next((ln.strip() for ln in lines if ln.strip()), "")
    suspicious = 0
    if re.match(r'^\\["\']use client\\["\'];?\\?$', first_non_empty):
        suspicious += 1
    if len(re.findall(r";\\\s*$", content, flags=re.MULTILINE)) >= 2:
        suspicious += 1
    if content.count('\\"') >= 3:
        suspicious += 1

    if suspicious == 0:
        return content

    fixed = content.replace('\\"', '"').replace("\\'", "'").replace("\\`", "`")
    fixed = re.sub(r"\\\s*$", "", fixed, flags=re.MULTILINE)
    return fixed


def _sanitize_content(path: str, content: str) -> str:
    """Applique tous les sanitizers sur le contenu avant écriture."""
    content = _fix_literal_newlines(path, content)
    content = _fix_overescaped_tsx_source(path, content)
    content = _fix_escaped_jsx_attr_quotes(path, content)
    if path.endswith(".json"):
        content = _fix_json_escaping(content)
    content = _apply_import_remaps(content, path)
    if os.path.basename(path) == "package.json":
        content = _apply_package_fixes(content)
    if os.path.basename(path) == "tsconfig.json":
        content = _ensure_tsconfig_excludes_tests(content)
    return content


# ─────────────────────────────────────────────────────────────────────────────
# Tool: write_file
# ─────────────────────────────────────────────────────────────────────────────

@tool
def write_file(path: str, content: str) -> str:
    """
    Écrit un fichier dans le répertoire de travail du projet généré (FACTORY_WORKDIR).
    Applique les sanitizers (import remaps, etc.) avant l'écriture.
    path: chemin relatif depuis la racine du projet généré (ex: 'app/layout.tsx').
    content: contenu complet du fichier.
    """
    try:
        # Guard : refuser l'écrasement des fichiers gérés par templates
        _norm_path = _normalize_guard_path(path)
        try:
            _templated = load_stack_config(get_stack_id()).get("templated_files", {})
            if _norm_path in _templated:
                logger.info(f"[write_file] ⛔ TEMPLATE_PROTÉGÉ — {path} ignoré")
                return (
                    f"TEMPLATE_PROTÉGÉ: '{path}' est géré par la factory (template validé). "
                    f"Ce fichier est déjà correct sur le disque. Passe au fichier suivant de la liste."
                )
        except Exception:
            pass

        workdir = _get_workdir()

        # Normaliser les chemins des fichiers de test en minuscules.
        # Empêche la coexistence de Layout.test.tsx et layout.test.tsx
        # sur un filesystem Linux case-sensitive (TypeScript lève alors
        # TS5070 "differs from already included file name only in casing").
        if _is_test_file_path(path):
            path = path.lower()

        abs_path = _resolve_safe_path(path, workdir)

        if len(content.encode("utf-8")) > MAX_FILE_SIZE_BYTES:
            return f"ERREUR: Fichier trop grand (> {MAX_FILE_SIZE_BYTES} bytes): {path}"

        sanitized = _sanitize_content(path, content)

        os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(sanitized)

        logger.info(f"[write_file] ✓ {path} ({len(sanitized)} chars)")
        return f"OK: {path} écrit ({len(sanitized)} chars)"

    except ValueError as ve:
        logger.error(f"[write_file] Path traversal: {ve}")
        return f"ERREUR: {ve}"
    except Exception as e:
        logger.error(f"[write_file] Échec {path}: {e}")
        return f"ERREUR write_file({path}): {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Tool: validate_syntax
# ─────────────────────────────────────────────────────────────────────────────

@tool
def validate_syntax(path: str) -> str:
    """
    Valide la syntaxe d'un fichier TypeScript/JavaScript.
    path: chemin relatif depuis la racine du projet généré.
    """
    try:
        workdir = _get_workdir()
        abs_path = _resolve_safe_path(path, workdir)

        if not os.path.exists(abs_path):
            return f"ERREUR: Fichier introuvable pour validation: {path}"

        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--skipLibCheck", abs_path],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SHORT,
            env=_get_node_env(),
            cwd=workdir,
        )
        if result.returncode == 0:
            return f"OK: {path} — syntaxe valide"

        output = (result.stdout + result.stderr).strip()
        return f"ERREUR syntaxe {path}:\n{_truncate_output(output)}"

    except subprocess.TimeoutExpired:
        return f"TIMEOUT: validate_syntax({path})"
    except Exception as e:
        return f"ERREUR validate_syntax({path}): {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Tool: prisma_migrate
# ─────────────────────────────────────────────────────────────────────────────

@tool
def prisma_migrate(project_dir: str = ".") -> str:
    """
    Exécute `npx prisma migrate dev --name init` dans le répertoire projet.
    À appeler après avoir écrit schema.prisma.
    project_dir: répertoire du projet (relatif depuis FACTORY_WORKDIR ou absolu).
    """
    try:
        workdir = _get_workdir()
        if not os.path.isabs(project_dir):
            cwd = os.path.join(workdir, project_dir) if project_dir != "." else workdir
        else:
            cwd = project_dir

        result = subprocess.run(
            ["npx", "prisma", "migrate", "dev", "--name", "init", "--skip-generate"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_MEDIUM,
            env=_get_node_env(),
            cwd=cwd,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode == 0:
            return f"OK: prisma migrate dev réussi\n{_truncate_output(output)}"
        return f"ERREUR prisma_migrate (code {result.returncode}):\n{_truncate_output(output)}"

    except subprocess.TimeoutExpired:
        return "TIMEOUT: prisma_migrate"
    except Exception as e:
        return f"ERREUR prisma_migrate: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Tool: read_files
# ─────────────────────────────────────────────────────────────────────────────

@tool
def read_files(paths: list) -> str:
    """
    Lit un ou plusieurs fichiers depuis le répertoire de travail du projet.
    paths: liste de chemins relatifs (ex: ['app/layout.tsx', 'package.json']).
    Retourne le contenu de chaque fichier.
    """
    workdir = _get_workdir()
    results = []
    for path in paths:
        try:
            abs_path = _resolve_safe_path(path, workdir)
            if not os.path.exists(abs_path):
                results.append(f"--- {path} ---\nFICHIER ABSENT")
                continue
            content = Path(abs_path).read_text(encoding="utf-8", errors="replace")
            results.append(f"--- {path} ---\n{_truncate_output(content, 3000)}")
        except Exception as e:
            results.append(f"--- {path} ---\nERREUR lecture: {e}")
    return "\n\n".join(results) if results else "Aucun fichier lu."


# ─────────────────────────────────────────────────────────────────────────────
# Pre-build helpers (hooks appelés par run_build)
# ─────────────────────────────────────────────────────────────────────────────

def _remove_pages_tests_router_conflicts(project_path: str) -> list:
    """
    Supprime les fichiers pages/ et src/pages/ qui conflictuent avec App Router.
    Retourne la liste des dossiers supprimés.
    """
    removed = []
    for conflict_dir in ["pages", "src/pages"]:
        full = os.path.join(project_path, conflict_dir)
        if os.path.isdir(full):
            try:
                shutil.rmtree(full)
                removed.append(conflict_dir)
                logger.info(f"[pre-build] Supprimé conflit: {conflict_dir}/")
            except Exception as e:
                logger.warning(f"[pre-build] Impossible de supprimer {conflict_dir}/: {e}")
    return removed


def _remove_stale_tests(project_path: str, source_files: set) -> list:
    """
    Supprime les fichiers de test orphelins (sans fichier source correspondant).
    Retourne la liste des fichiers supprimés.
    """
    removed = []
    tests_dir = os.path.join(project_path, "tests")
    if not os.path.isdir(tests_dir):
        return removed
    for root, _, files in os.walk(tests_dir):
        for fname in files:
            if fname.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
                fpath = os.path.join(root, fname)
                base = fname.replace(".test.", ".").replace(".spec.", ".")
                if not any(sf.endswith(base) for sf in source_files):
                    try:
                        os.remove(fpath)
                        removed.append(os.path.relpath(fpath, project_path))
                        logger.info(f"[pre-build] Test orphelin supprimé: {fpath}")
                    except Exception as e:
                        logger.warning(f"[pre-build] Impossible de supprimer {fpath}: {e}")
    return removed


def _count_test_files(project_path: str) -> int:
    """Compte le nombre de fichiers de test dans le projet."""
    count = 0
    for root, _, files in os.walk(project_path):
        if "node_modules" in root or ".next" in root:
            continue
        for fname in files:
            if _is_test_file_path(os.path.join(root, fname)):
                count += 1
    return count


def _ensure_layout_dynamic(project_path: str) -> bool:
    """
    Injecte 'export const dynamic = "force-dynamic"' dans app/layout.tsx si absent.

    Problème : next build pré-rend statiquement toutes les pages. ClerkProvider
    s'initialise pendant ce prerender et lève une exception si la publishableKey
    ne commence pas par pk_test_ ou pk_live_ (ex: placeholder 'your_publishable_key').
    Solution : force-dynamic désactive la génération statique — Clerk n'est plus
    initialisé pendant le build, seulement à runtime avec de vraies credentials.
    """
    layout_path = os.path.join(project_path, "app", "layout.tsx")
    if not os.path.exists(layout_path):
        return False

    content = Path(layout_path).read_text(encoding="utf-8")
    if "export const dynamic" in content:
        return False  # Déjà présent — pas de mutation

    # Injecter après le dernier import (avant le premier composant/export)
    lines = content.splitlines(keepends=True)
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("import "):
            last_import_idx = i

    dynamic_line = '\nexport const dynamic = "force-dynamic";\n'
    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, dynamic_line)
    else:
        lines.insert(0, dynamic_line + "\n")

    with open(layout_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info("[pre-build] app/layout.tsx: export const dynamic = 'force-dynamic' injecté")
    return True


def _fix_nextconfig_security_headers(project_path: str) -> bool:
    """
    Corrige la section `headers()` de next.config.js si le LLM a généré un
    tableau plat [{key, value}] au lieu du format Next.js valide :
      [{ source: '/(.*)', headers: [{key, value}] }]

    Next.js lève : `source` is missing / `headers` field must be an array.

    NOTE DETTE TECHNIQUE : logique stack-specific hardcodée en Python.
    À migrer vers SanitizerRegistry (Sprint 6-7).
    """
    nextconfig_path = os.path.join(project_path, "next.config.js")
    if not os.path.exists(nextconfig_path):
        return False

    content = Path(nextconfig_path).read_text(encoding="utf-8")

    # Présence d'une fonction headers async dans le fichier
    has_headers_func = bool(re.search(r'headers\s*\(\s*\)\s*\{', content) or
                            re.search(r'headers\s*:\s*async\s*\(\)', content))
    if not has_headers_func:
        return False

    # Si `source:` est déjà présent → format correct, rien à faire
    if re.search(r'["\']?source["\']?\s*:', content):
        return False

    # Réécriture complète avec format valide
    correct_config = (
        "/** @type {import('next').NextConfig} */\n"
        "const nextConfig = {\n"
        "  reactStrictMode: true,\n"
        "  eslint: { ignoreDuringBuilds: true },\n"
        "  typescript: { ignoreBuildErrors: false },\n"
        "  async headers() {\n"
        "    return [\n"
        "      {\n"
        "        source: '/(.*)',\n"
        "        headers: [\n"
        "          { key: 'X-Frame-Options', value: 'DENY' },\n"
        "          { key: 'X-Content-Type-Options', value: 'nosniff' },\n"
        "          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },\n"
        "        ],\n"
        "      },\n"
        "    ];\n"
        "  },\n"
        "};\n\n"
        "module.exports = nextConfig;\n"
    )
    with open(nextconfig_path, "w", encoding="utf-8") as f:
        f.write(correct_config)
    logger.info("[pre-build] next.config.js: headers invalide (pas de source:) → format Next.js corrigé")
    return True


def _ensure_layout_html_body(project_path: str) -> bool:
    """
    Assure que app/layout.tsx contient les balises <html> et <body> requises
    par Next.js 14 App Router. Le LLM génère parfois un composant React.FC
    classique sans ces balises → Next.js lève une erreur de build.

    Si les balises sont absentes, réécrit le fichier avec un layout canonique
    (préserve ClerkProvider si présent, inclut force-dynamic).

    NOTE DETTE TECHNIQUE : logique stack-specific hardcodée en Python.
    À migrer vers SanitizerRegistry (Sprint 6-7).
    """
    layout_path = os.path.join(project_path, "app", "layout.tsx")
    if not os.path.exists(layout_path):
        return False

    content = Path(layout_path).read_text(encoding="utf-8")

    # Si <html> et <body> sont déjà présents → rien à faire
    if "<html" in content and "<body" in content:
        return False

    has_clerk = "ClerkProvider" in content

    canonical = (
        ("import { ClerkProvider } from '@clerk/nextjs';\n" if has_clerk else "")
        + "\nexport const dynamic = \"force-dynamic\";\n\n"
        + "export default function RootLayout({\n"
        + "  children,\n"
        + "}: {\n"
        + "  children: React.ReactNode;\n"
        + "}) {\n"
        + "  return (\n"
        + '    <html lang="en">\n'
        + "      <body>\n"
        + ("        <ClerkProvider>\n" if has_clerk else "")
        + "          {children}\n"
        + ("        </ClerkProvider>\n" if has_clerk else "")
        + "      </body>\n"
        + "    </html>\n"
        + "  );\n"
        + "}\n"
    )

    with open(layout_path, "w", encoding="utf-8") as f:
        f.write(canonical)
    logger.info("[pre-build] app/layout.tsx: balises <html>/<body> manquantes → layout canonique App Router écrit")
    return True


def _ensure_nextconfig_eslint_ignore(project_path: str) -> bool:
    """S'assure que next.config.js ignore les erreurs ESLint lors du build."""
    nextconfig_path = os.path.join(project_path, "next.config.js")
    if not os.path.exists(nextconfig_path):
        content = (
            "/** @type {import('next').NextConfig} */\n"
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "  eslint: { ignoreDuringBuilds: true },\n"
            "  typescript: { ignoreBuildErrors: false },\n"
            "};\n\n"
            "module.exports = nextConfig;\n"
        )
        with open(nextconfig_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("[pre-build] next.config.js créé avec eslint.ignoreDuringBuilds=true")
        return True

    content = Path(nextconfig_path).read_text(encoding="utf-8")
    if "ignoreDuringBuilds" not in content:
        content = content.replace(
            "const nextConfig = {",
            "const nextConfig = {\n  eslint: { ignoreDuringBuilds: true },"
        )
        with open(nextconfig_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("[pre-build] next.config.js: eslint.ignoreDuringBuilds ajouté")
        return True
    return False


def _fix_prisma_named_import(project_path: str) -> list[str]:
    """
    Auto-fix déterministe Prisma:
    Corrige `import { prisma } from '@/lib/prisma'` vers
    `import prisma from '@/lib/prisma'` dans les fichiers .ts/.tsx.
    """
    fixed_files: list[str] = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git")]
        for filename in files:
            if not filename.endswith((".ts", ".tsx")):
                continue
            full_path = os.path.join(root, filename)
            try:
                original = Path(full_path).read_text(encoding="utf-8")
            except Exception:
                continue
            fixed, count = _rewrite_prisma_named_import(original)
            if count > 0 and fixed != original:
                try:
                    Path(full_path).write_text(fixed, encoding="utf-8")
                    fixed_files.append(os.path.relpath(full_path, project_path).replace("\\", "/"))
                except Exception as e:
                    logger.warning(f"[pre-build] Impossible de corriger import Prisma dans {full_path}: {e}")
    if fixed_files:
        logger.info(f"[pre-build] Prisma named import corrigé: {fixed_files}")
    return fixed_files


def _rewrite_prisma_named_import(content: str) -> tuple[str, int]:
    """
    Transforme le contenu en corrigeant l'import nommé Prisma vers import default.
    Retourne (new_content, replacement_count).
    """
    pattern = re.compile(r'import\s*\{\s*prisma\s*\}\s*from\s*([\'"])@/lib/prisma\1')
    return pattern.subn("import prisma from '@/lib/prisma'", content)


def _rewrite_route_prisma_client_usage(content: str) -> tuple[str, int]:
    """
    Normalise l'usage Prisma dans les route handlers App Router:
    - supprime import PrismaClient depuis @prisma/client
    - supprime instantiation locale new PrismaClient(...)
    - garantit import default prisma depuis @/lib/prisma
    """
    updated = content
    replacements = 0

    # Supprimer import PrismaClient (named/default/combiné) depuis @prisma/client.
    updated, count = re.subn(
        r"^\s*import\s+PrismaClient\s+from\s+['\"]@prisma/client['\"]\s*;?\s*\n",
        "",
        updated,
        flags=re.MULTILINE,
    )
    replacements += count

    def _strip_prismaclient_from_named_import(m: re.Match) -> str:
        nonlocal replacements
        names = [n.strip() for n in m.group(1).split(",") if n.strip()]
        filtered = [n for n in names if n.split(" as ")[0].strip() != "PrismaClient"]
        if len(filtered) != len(names):
            replacements += 1
        if not filtered:
            return ""
        return f"import {{ {', '.join(filtered)} }} from '@prisma/client';\n"

    updated = re.sub(
        r"^\s*import\s*\{([^}]*)\}\s*from\s*['\"]@prisma/client['\"]\s*;?\s*\n",
        _strip_prismaclient_from_named_import,
        updated,
        flags=re.MULTILINE,
    )

    # Supprimer instanciations locales de PrismaClient et normaliser vers `prisma`.
    # Supporte les alias (ex: `const db = new PrismaClient(...)`).
    _alias_pat = re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)"
        r"(?:\s*:\s*[^=]+)?\s*=\s*new\s+PrismaClient\s*\((?:.|\n)*?\)\s*;?\s*$",
        re.MULTILINE,
    )
    aliases = [m.group(1) for m in _alias_pat.finditer(updated)]
    updated, count = _alias_pat.subn("", updated)
    replacements += count
    for _alias in aliases:
        if _alias != "prisma":
            updated, alias_count = re.subn(rf"\b{re.escape(_alias)}\b", "prisma", updated)
            replacements += alias_count

    # Si on a supprimé un pattern PrismaClient, injecter import canonical prisma si absent.
    if replacements > 0 and "from '@/lib/prisma'" not in updated:
        updated = "import prisma from '@/lib/prisma';\n" + updated.lstrip("\n")
        replacements += 1

    # Garde-fou: si des appels bruts `new PrismaClient(...)` subsistent, les remplacer.
    updated, count = re.subn(r"new\s+PrismaClient\s*\((?:.|\n)*?\)", "prisma", updated)
    replacements += count

    return updated, replacements


def _fix_route_prisma_client_usage(project_path: str) -> list[str]:
    """Applique _rewrite_route_prisma_client_usage à app/api/**/route.ts."""
    fixed_files: list[str] = []
    api_root = os.path.join(project_path, "app", "api")
    if not os.path.isdir(api_root):
        return fixed_files

    for root, dirs, files in os.walk(api_root):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git")]
        for filename in files:
            if filename != "route.ts":
                continue
            full_path = os.path.join(root, filename)
            rel = os.path.relpath(full_path, project_path).replace("\\", "/")
            try:
                original = Path(full_path).read_text(encoding="utf-8")
            except Exception:
                continue
            fixed, count = _rewrite_route_prisma_client_usage(original)
            if count > 0 and fixed != original:
                try:
                    Path(full_path).write_text(fixed, encoding="utf-8")
                    fixed_files.append(rel)
                except Exception as e:
                    logger.warning(f"[pre-build] Impossible de corriger PrismaClient local dans {full_path}: {e}")

    if fixed_files:
        logger.info(f"[pre-build] Route handlers Prisma normalisés: {fixed_files}")
    return fixed_files


def _fix_global_prisma_client_usage(project_path: str) -> list[str]:
    """
    Normalise Prisma sur tous les fichiers app/**/*.ts(x) hors template lib/prisma.ts.
    Objectif: éliminer les instanciations directes résiduelles non couvertes par route.ts.
    """
    fixed_files: list[str] = []
    app_root = os.path.join(project_path, "app")
    if not os.path.isdir(app_root):
        return fixed_files

    for root, dirs, files in os.walk(app_root):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git")]
        for filename in files:
            if not filename.endswith((".ts", ".tsx")):
                continue
            full_path = os.path.join(root, filename)
            rel = os.path.relpath(full_path, project_path).replace("\\", "/")
            if rel == "lib/prisma.ts":
                continue
            try:
                original = Path(full_path).read_text(encoding="utf-8")
            except Exception:
                continue
            fixed, count = _rewrite_route_prisma_client_usage(original)
            if count > 0 and fixed != original:
                try:
                    Path(full_path).write_text(fixed, encoding="utf-8")
                    fixed_files.append(rel)
                except Exception as e:
                    logger.warning(f"[pre-build] Impossible de normaliser Prisma global dans {full_path}: {e}")

    if fixed_files:
        logger.info(f"[pre-build] Prisma global normalisé: {fixed_files}")
    return fixed_files


def _remove_clerk_auth_routes(project_path: str) -> list[str]:
    """
    Stack Clerk: supprime les routes auth générées par erreur (next-auth/route custom),
    non requises et fréquemment invalides (`auth.signIn` etc.).
    """
    removed: list[str] = []
    if get_stack_id() != "nextjs-clerk-prisma":
        return removed

    auth_dir = os.path.join(project_path, "app", "api", "auth")
    if os.path.isdir(auth_dir):
        try:
            shutil.rmtree(auth_dir)
            removed.append("app/api/auth/")
            logger.info("[pre-build] app/api/auth/ supprimé (stack Clerk)")
        except Exception as e:
            logger.warning(f"[pre-build] Impossible de supprimer app/api/auth/: {e}")

    return removed


def _route_dynamic_param_keys(rel_path: str) -> list[str]:
    """
    Extrait les clés dynamiques d'un chemin route.ts App Router.
    Exemple: app/api/posts/[id]/route.ts -> ["id"]
    """
    keys = re.findall(r"\[([a-zA-Z_][a-zA-Z0-9_]*)\]", rel_path.replace("\\", "/"))
    return [k for k in keys if k]


def _rewrite_untyped_route_handler_signatures(content: str, rel_path: str) -> tuple[str, int]:
    """
    Corrige les signatures TypeScript non typées des route handlers App Router.
    Ex:
      export async function PUT(request, { params }) {
    ->
      export async function PUT(request: Request, { params }: { params: { id: string } }) {
    """
    dynamic_keys = _route_dynamic_param_keys(rel_path)
    if dynamic_keys:
        params_shape = "; ".join(f"{k}: string" for k in dynamic_keys)
        context_type = f"{{ params: {{ {params_shape} }} }}"
    else:
        context_type = "{ params: Record<string, string> }"

    sig_re = re.compile(
        r"export\s+async\s+function\s+(GET|POST|PUT|PATCH|DELETE|HEAD)\s*\(([^)]*)\)",
        re.MULTILINE,
    )
    replacements = 0

    def _repl(m: re.Match) -> str:
        nonlocal replacements
        method = m.group(1)
        args_raw = m.group(2).strip()
        if not args_raw:
            return m.group(0)

        parts = [p.strip() for p in args_raw.split(",", 1)]
        changed = False

        # Cas invalide fréquent:
        # export async function GET({ params }) { ... }
        # -> le 1er arg DOIT être Request/NextRequest.
        first = parts[0]
        if first.startswith("{") and "params" in first:
            if len(parts) == 1:
                parts = ["request: Request", f"{first}: {context_type}"]
            else:
                parts[0] = "request: Request"
            changed = True

        # 1er argument: request/req non typé
        first = parts[0]
        if first and ":" not in first:
            first_name = first or "request"
            parts[0] = f"{first_name}: Request"
            changed = True

        # 2e argument: { params } non typé
        if len(parts) > 1:
            second = parts[1]
            if "params" in second and ":" not in second:
                # Garde le destructuring d'origine si possible, sinon canonical.
                destructuring = second if second.startswith("{") else "{ params }"
                parts[1] = f"{destructuring}: {context_type}"
                changed = True

        if not changed:
            return m.group(0)

        replacements += 1
        return f"export async function {method}({', '.join(parts)})"

    updated = sig_re.sub(_repl, content)
    return updated, replacements


def _fix_untyped_route_handlers(project_path: str) -> list[str]:
    """
    Auto-fix déterministe:
    type les signatures de route handlers dans app/api/**/route.ts.
    """
    fixed_files: list[str] = []
    api_root = os.path.join(project_path, "app", "api")
    if not os.path.isdir(api_root):
        return fixed_files

    for root, dirs, files in os.walk(api_root):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git")]
        for filename in files:
            if filename != "route.ts":
                continue
            full_path = os.path.join(root, filename)
            rel = os.path.relpath(full_path, project_path).replace("\\", "/")
            try:
                original = Path(full_path).read_text(encoding="utf-8")
            except Exception:
                continue
            fixed, count = _rewrite_untyped_route_handler_signatures(original, rel)
            if count > 0 and fixed != original:
                try:
                    Path(full_path).write_text(fixed, encoding="utf-8")
                    fixed_files.append(rel)
                except Exception as e:
                    logger.warning(f"[pre-build] Impossible de typer route handler {full_path}: {e}")
    if fixed_files:
        logger.info(f"[pre-build] Route handlers typés automatiquement: {fixed_files}")
    return fixed_files


def _rewrite_untyped_map_callback_params(content: str) -> tuple[str, int]:
    """
    Ajoute un type explicite `any` aux callbacks map non typés.
    Exemple:
      posts.map((post) => ...)
    ->
      posts.map((post: any) => ...)
    Objectif: éliminer TS7006 (implicit any) de façon déterministe.
    """
    methods = r"(map|filter|find|some|every|forEach|flatMap)"

    # Cas courant : arr.map((item) => ...)
    pattern_paren = re.compile(
        rf"\.{methods}\(\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*=>"
    )
    updated, count1 = pattern_paren.subn(r".\1((\2: any) =>", content)

    # Variante : arr.map(item => ...)
    pattern_plain = re.compile(
        rf"\.{methods}\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*=>"
    )
    updated, count2 = pattern_plain.subn(r".\1(\2: any =>", updated)

    # reduce((acc, item) => ...)
    reduce_paren = re.compile(
        r"\.reduce\(\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*=>"
    )
    updated, count3 = reduce_paren.subn(r".reduce((\1: any, \2: any) =>", updated)

    # reduce(acc, item => ...) forme rare mais tolérée
    reduce_plain = re.compile(
        r"\.reduce\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*=>"
    )
    updated, count4 = reduce_plain.subn(r".reduce((\1: any, \2: any) =>", updated)

    return updated, (count1 + count2 + count3 + count4)


def _fix_untyped_map_callbacks(project_path: str) -> list[str]:
    """
    Auto-fix déterministe:
    type les callbacks map non typés dans les composants TS/TSX.
    """
    fixed_files: list[str] = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".next", ".git")]
        for filename in files:
            if not filename.endswith((".ts", ".tsx")):
                continue
            full_path = os.path.join(root, filename)
            try:
                original = Path(full_path).read_text(encoding="utf-8")
            except Exception:
                continue
            fixed, count = _rewrite_untyped_map_callback_params(original)
            if count > 0 and fixed != original:
                try:
                    Path(full_path).write_text(fixed, encoding="utf-8")
                    fixed_files.append(os.path.relpath(full_path, project_path).replace("\\", "/"))
                except Exception as e:
                    logger.warning(f"[pre-build] Impossible de typer callbacks map dans {full_path}: {e}")
    if fixed_files:
        logger.info(f"[pre-build] Map callbacks typés automatiquement: {fixed_files}")
    return fixed_files


def _fix_prisma_generator_provider(project_path: str) -> bool:
    """
    Garantit la compatibilité Prisma de la stack:
      generator client { provider = "prisma-client-js" }
    Le LLM produit parfois "prisma-client", ce qui casse le runtime client.
    """
    schema_path = os.path.join(project_path, "prisma", "schema.prisma")
    if not os.path.isfile(schema_path):
        return False
    try:
        original = Path(schema_path).read_text(encoding="utf-8")
    except Exception:
        return False

    fixed = re.sub(
        r"(generator\s+client\s*\{[^}]*?\bprovider\s*=\s*)[\"']prisma-client[\"']",
        r'\1"prisma-client-js"',
        original,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fixed == original:
        return False
    try:
        Path(schema_path).write_text(fixed, encoding="utf-8")
        logger.warning("[pre-build deterministic fix] prisma generator provider -> prisma-client-js")
        return True
    except Exception as e:
        logger.warning(f"[pre-build] Impossible de corriger prisma generator provider: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Tool: run_build
# ─────────────────────────────────────────────────────────────────────────────

@tool
def run_build(project_dir: str = ".") -> str:
    """
    Lance npm install puis npm run build dans le répertoire du projet généré.
    Applique les pre-build hooks: suppression pages/ conflicts, eslint ignore.
    project_dir: répertoire du projet (relatif depuis FACTORY_WORKDIR ou absolu).
    """
    try:
        workdir = _get_workdir()
        if not os.path.isabs(project_dir):
            project_path = os.path.join(workdir, project_dir) if project_dir != "." else workdir
        else:
            project_path = project_dir
        project_path = os.path.normpath(project_path)

        if not os.path.isdir(project_path):
            return f"ERREUR: Répertoire projet introuvable: {project_path}"

        # ── Lire commandes depuis la stack config (résout Config-Runtime Drift) ─
        from agents.stack_config import get_commands, get_root_file
        stack_id = get_stack_id()
        cmds = get_commands(stack_id)
        root_file = get_root_file(stack_id)
        install_cmd = cmds.get("install_legacy", "npm install --legacy-peer-deps").split()
        build_cmd = cmds.get("build", "npm run build").split()

        # ── Guard ENOENT : fichier racine doit exister avant install ────────
        root_file_path = os.path.join(project_path, root_file)
        if not os.path.isfile(root_file_path):
            msg = (
                f"ERREUR CRITIQUE: {root_file} introuvable dans le répertoire de build.\n"
                f"Chemin attendu: {root_file_path}\n"
                f"ACTION REQUISE: générer {root_file} en PREMIER avec write_file avant d'appeler run_build.\n"
                "Fichiers obligatoires manquants: package.json, app/layout.tsx, middleware.ts, next.config.js, tsconfig.json"
            )
            logger.error(f"[run_build] {msg}")
            return msg

        logger.info(f"[run_build] project_path={project_path} install={install_cmd} build={build_cmd}")

        # ── Pre-build hooks ─────────────────────────────────────────────────
        removed = _remove_pages_tests_router_conflicts(project_path)
        if removed:
            logger.info(f"[run_build] Conflits App/Pages Router supprimés: {removed}")
        removed_auth = _remove_clerk_auth_routes(project_path)
        if removed_auth:
            logger.warning(f"[pre-build deterministic fix] routes auth non-Clerk supprimées: {removed_auth}")
        prisma_import_fixes = _fix_prisma_named_import(project_path)
        if prisma_import_fixes:
            logger.warning(
                f"[pre-build deterministic fix] prisma named import -> default import: {prisma_import_fixes}"
            )
        route_prisma_fixes = _fix_route_prisma_client_usage(project_path)
        if route_prisma_fixes:
            logger.warning(
                f"[pre-build deterministic fix] route prisma client usage normalized: {route_prisma_fixes}"
            )
        global_prisma_fixes = _fix_global_prisma_client_usage(project_path)
        if global_prisma_fixes:
            logger.warning(
                f"[pre-build deterministic fix] global prisma client usage normalized: {global_prisma_fixes}"
            )
        route_handler_fixes = _fix_untyped_route_handlers(project_path)
        if route_handler_fixes:
            logger.warning(
                f"[pre-build deterministic fix] route handler signatures typed: {route_handler_fixes}"
            )
        map_callback_fixes = _fix_untyped_map_callbacks(project_path)
        if map_callback_fixes:
            logger.warning(
                f"[pre-build deterministic fix] map callbacks typed: {map_callback_fixes}"
            )
        _prisma_provider_fixed = _fix_prisma_generator_provider(project_path)
        if _prisma_provider_fixed:
            logger.warning("[pre-build deterministic fix] prisma schema provider normalized")
        # Clerk + Next.js: éviter le prerender build-time avec clé publishable placeholder.
        # On force le layout en dynamic pour ne pas invalider le run sur un secret runtime absent.
        if stack_id == "nextjs-clerk-prisma":
            _layout_dynamic_fixed = _ensure_layout_dynamic(project_path)
            if _layout_dynamic_fixed:
                logger.warning("[pre-build deterministic fix] app/layout.tsx force-dynamic ensured for Clerk stack")

        # FACTORY_STRICT_PREBUILD="1" (défaut) → valider sans réécrire (métriques honnêtes).
        # FACTORY_STRICT_PREBUILD="0" → mutations actives (mode dégradé explicite).
        _strict = os.getenv("FACTORY_STRICT_PREBUILD", "1") == "1"
        _mutations = []
        if not _strict:
            if _ensure_nextconfig_eslint_ignore(project_path):
                _mutations.append("next.config.js: eslint.ignoreDuringBuilds injecté")
            if _fix_nextconfig_security_headers(project_path):
                _mutations.append("next.config.js: headers format corrigé")
            if _ensure_layout_html_body(project_path):
                _mutations.append("app/layout.tsx: balises html/body réécrites")
            if _ensure_layout_dynamic(project_path):
                _mutations.append("app/layout.tsx: force-dynamic injecté")
            if _mutations:
                logger.warning(f"[pre-build mutations] LLM output corrigé automatiquement : {_mutations}")

        # ── Install (commande lue depuis stack JSON) ─────────────────────────
        install_result = subprocess.run(
            install_cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_LONG,
            env=_get_node_env(),
            cwd=project_path,
        )
        if install_result.returncode != 0:
            stderr = (install_result.stdout + install_result.stderr).strip()
            return (
                f"Build failed at install (code {install_result.returncode}).\n"
                f"Command failed (code {install_result.returncode}): {install_cmd}\n"
                f"STDERR:\n{_truncate_output(stderr)}"
            )

        # ── Prisma generate (Prisma 7 : postinstall ne génère plus le client auto) ──
        # Si prisma/schema.prisma est présent, on génère le client AVANT le build.
        # prisma generate ne nécessite pas de connexion DB — génère uniquement les types TS.
        _schema_path = os.path.join(project_path, "prisma", "schema.prisma")
        if os.path.isfile(_schema_path):
            _gen_result = subprocess.run(
                ["npx", "prisma", "generate"],
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT_LONG,
                env=_get_node_env(),
                cwd=project_path,
            )
            if _gen_result.returncode != 0:
                _gen_out = ((_gen_result.stdout or "") + "\n" + (_gen_result.stderr or "")).strip()
                logger.warning(f"[run_build] prisma generate échoué (code {_gen_result.returncode})")
                return (
                    f"Build failed at prisma generate (code {_gen_result.returncode}).\n"
                    f"Command failed (code {_gen_result.returncode}): npx prisma generate\n"
                    f"STDERR:\n{_truncate_output(_gen_out)}"
                )
            else:
                logger.info("[run_build] prisma generate OK — client TS généré")

        # ── Build (commande lue depuis stack JSON) ───────────────────────────
        build_result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_LONG,
            env=_get_node_env(),
            cwd=project_path,
        )
        stdout = build_result.stdout.strip()
        stderr = build_result.stderr.strip()

        if build_result.returncode == 0:
            logger.info(f"[run_build] Build successful: {project_path}")
            return f"Build successful!\nSTDOUT:\n{_truncate_output(stdout)}"

        return (
            f"Build failed (code {build_result.returncode}).\n"
            f"Command failed (code {build_result.returncode}): {build_cmd}\n"
            f"STDERR:\n{_truncate_output(stderr)}"
        )

    except subprocess.TimeoutExpired:
        return "TIMEOUT: run_build (> 600s)"
    except Exception as e:
        return f"ERREUR run_build: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Build error helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_build_error_signature(output: str) -> str:
    """Extrait la signature principale d'une erreur de build (première ligne clé)."""
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Error:") or stripped.startswith("⨯") or "error TS" in stripped:
            return stripped[:200]
    return output[:200] if output else ""


# ─────────────────────────────────────────────────────────────────────────────
# Tool: run_tests
# ─────────────────────────────────────────────────────────────────────────────

@tool
def run_tests(project_dir: str = ".", files: dict = {}) -> str:
    """
    Écrit les fichiers fournis puis lance jest dans le répertoire projet.
    project_dir: répertoire du projet (relatif depuis FACTORY_WORKDIR ou absolu).
    files: dict {path: content} de fichiers à écrire avant les tests (optionnel).
    """
    try:
        workdir = _get_workdir()
        if not os.path.isabs(project_dir):
            project_path = os.path.join(workdir, project_dir) if project_dir != "." else workdir
        else:
            project_path = project_dir
        project_path = os.path.normpath(project_path)

        # Charger la liste des fichiers protégés par templates (ne pas écraser)
        try:
            _templated_protected = load_stack_config(get_stack_id()).get("templated_files", {})
        except Exception:
            _templated_protected = {}

        # Écrire les fichiers fournis (sauf les templates protégés déjà sur disque)
        if files:
            for path, content in files.items():
                _norm = path.replace("\\", "/")
                if _norm.startswith("./"):
                    _norm = _norm[2:]
                if _norm in _templated_protected:
                    logger.info(f"[run_tests] ⛔ TEMPLATE_PROTÉGÉ — {path} non écrasé")
                    continue
                try:
                    abs_path = _resolve_safe_path(path, project_path)
                    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
                    with open(abs_path, "w", encoding="utf-8") as f:
                        f.write(str(content))
                except Exception as e:
                    logger.warning(f"[run_tests] Impossible d'écrire {path}: {e}")

        # Vérifier le minimum de tests requis
        test_count = _count_test_files(project_path)
        try:
            from agents.stack_config import load_stack_config
            cfg = load_stack_config(get_stack_id())
            min_tests = cfg.get("testing", {}).get("min_required_tests", 1)
            allow_zero = cfg.get("testing", {}).get("allow_zero_tests_debug", False)
        except Exception:
            min_tests = 1
            allow_zero = False

        if test_count < min_tests and not allow_zero:
            return f"Tests skipped: aucun fichier de test trouvé dans {project_path} (requis: {min_tests})"

        # Lire la commande test depuis le JSON stack (Config-Runtime Drift fix Sprint 3)
        try:
            from agents.stack_config import get_commands
            test_cmd_str = get_commands(get_stack_id()).get("test", "npx jest --coverage")
            test_cmd = test_cmd_str.split()
            if "--passWithNoTests" not in test_cmd:
                test_cmd.append("--passWithNoTests")
        except Exception:
            test_cmd = "npx jest --coverage --passWithNoTests".split()

        # Lancer les tests
        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_MEDIUM,
            env=_get_node_env(),
            cwd=project_path,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        combined = (stdout + "\n" + stderr).strip()

        if result.returncode == 0:
            return f"Tests passed!\n{_truncate_output(combined)}"

        return (
            f"Tests failed (code {result.returncode}).\n"
            f"STDERR:\n{_truncate_output(stderr)}"
        )

    except subprocess.TimeoutExpired:
        return "TIMEOUT: run_tests (> 60s)"
    except Exception as e:
        return f"ERREUR run_tests: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Version management helpers
# ─────────────────────────────────────────────────────────────────────────────

def _major_from_version(version: str) -> Optional[int]:
    """Extrait le numéro de version majeure depuis une chaîne semver."""
    m = re.search(r"(\d+)", version.lstrip("^~>=<"))
    return int(m.group(1)) if m else None


def _collect_package_version_mismatches(package_json_content: str, stack_id: str) -> list:
    """
    Compare les versions dans package.json avec les version_pins et compatibility_matrix.
    Retourne une liste de messages de mismatch.
    """
    try:
        pkg = json.loads(package_json_content)
    except Exception:
        return []

    from agents.stack_config import get_version_pins, get_compatibility_matrix
    pins = get_version_pins(stack_id)
    matrix = get_compatibility_matrix(stack_id)
    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    mismatches = []

    for pkg_name, required_version in pins.items():
        actual = all_deps.get(pkg_name)
        if actual and actual != required_version:
            mismatches.append(f"{pkg_name}: attendu={required_version}, trouvé={actual}")

    for pkg_name, compat in matrix.items():
        actual = all_deps.get(pkg_name)
        if not actual:
            continue
        actual_major = _major_from_version(actual)
        req_major = compat.get("required_major")
        min_major = compat.get("min_major")
        max_major = compat.get("max_major")

        if req_major and actual_major != req_major:
            mismatches.append(
                f"{pkg_name}: major requis={req_major}, trouvé={actual_major} "
                f"({compat.get('reason', '')})"
            )
        if min_major and actual_major is not None and actual_major < min_major:
            mismatches.append(f"{pkg_name}: major minimum={min_major}, trouvé={actual_major}")
        if max_major and actual_major is not None and actual_major > max_major:
            mismatches.append(f"{pkg_name}: major maximum={max_major}, trouvé={actual_major}")

    return mismatches


# ─────────────────────────────────────────────────────────────────────────────
# Tool: log_to_learner
# ─────────────────────────────────────────────────────────────────────────────

@tool
def log_to_learner(event_type: str, payload: str) -> str:
    """
    Enregistre un événement dans le shadow log du Learner.
    event_type: type de l'événement (ex: 'build_success', 'build_failure').
    payload: données JSON sérialisées de l'événement.
    """
    try:
        run_id = get_run_id()
        data = json.loads(payload) if isinstance(payload, str) else payload
        _write_learner_event(event_type=event_type, payload=data, run_id=run_id)
        return f"OK: Événement '{event_type}' loggé"
    except Exception as e:
        logger.warning(f"[log_to_learner] failed: {e}")
        return f"ERREUR log_to_learner: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Tool: validate_blueprint
# ─────────────────────────────────────────────────────────────────────────────

@tool
def validate_blueprint(files: dict) -> str:
    """
    Vérifie que tous les fichiers requis par le blueprint de la stack sont présents.
    files: dict {path: content} des fichiers générés.
    Retourne un rapport de validation (OK ou liste des manquants).
    """
    try:
        from agents.stack_config import get_blueprint
        blueprint = get_blueprint(get_stack_id())
        required = blueprint.get("required_files", [])
        critical = blueprint.get("critical_files", required)
    except Exception as e:
        return f"ERREUR validate_blueprint (impossible de charger le blueprint): {e}"

    present = set(files.keys())
    missing_critical = [f for f in critical if f not in present]
    missing_required = [f for f in required if f not in present]

    if missing_critical:
        return (
            f"ÉCHEC BLUEPRINT: Fichiers critiques manquants: {missing_critical}\n"
            f"Fichiers présents: {sorted(present)}"
        )
    if missing_required:
        return (
            f"AVERTISSEMENT BLUEPRINT: Fichiers requis manquants: {missing_required}\n"
            f"Fichiers présents: {sorted(present)}"
        )
    return f"OK: Blueprint validé — {len(present)} fichiers présents, tous les requis OK."
