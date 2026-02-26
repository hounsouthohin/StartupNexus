import codecs
import json
import os
import re
import shutil
import subprocess
import shlex
from datetime import datetime, timezone
import time
from pathlib import Path
from contextvars import ContextVar

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Import central configuration
from config.factory_config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL,
    DEFAULT_VECTOR_SEARCH_LIMIT,
    SUBPROCESS_TIMEOUT_SHORT,
    SUBPROCESS_TIMEOUT_MEDIUM,
    SUBPROCESS_TIMEOUT_LONG
)

# --- Global Configurations & Clients (Singleton Pattern) ---
try:
    qdrant_client = QdrantClient(url=QDRANT_URL, timeout=SUBPROCESS_TIMEOUT_MEDIUM)
    openai_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = QdrantVectorStore(
        client=qdrant_client, 
        collection_name=QDRANT_COLLECTION_NAME, 
        embedding=openai_embeddings
    )
except Exception as e:
    qdrant_client = None
    openai_embeddings = None
    vectorstore = None
    print(f"[ERROR] Failed to initialize global clients: {e}")


# Setup basic logger (can be replaced with a more robust logger)
class Logger:
    def info(self, message):
        print(f"[INFO] {message}")
    def warning(self, message):
        print(f"[WARNING] {message}")
    def error(self, message):
        print(f"[ERROR] {message}")
logger = Logger()


# --- Run ID & Stack ID context (async-safe) ---
DEFAULT_STACK_ID = "nextjs-clerk-prisma"
_run_id_ctx: ContextVar[str] = ContextVar("run_id", default="")
_stack_id_ctx: ContextVar[str] = ContextVar("stack_id", default=DEFAULT_STACK_ID)


def set_run_id(run_id: str) -> None:
    _run_id_ctx.set(run_id or "")


def get_run_id() -> str:
    return _run_id_ctx.get()


def set_stack_id(stack_id: str) -> None:
    _stack_id_ctx.set(stack_id or DEFAULT_STACK_ID)


def get_stack_id() -> str:
    return _stack_id_ctx.get() or DEFAULT_STACK_ID


def _get_runtime_stack_rules(stack_id: str | None = None) -> dict:
    """
    Retourne les règles stack runtime depuis Stack-as-Config, avec fallback local.
    Cela évite les divergences quand stack_id change pendant le run.
    """
    effective_stack_id = stack_id or get_stack_id() or DEFAULT_STACK_ID
    try:
        from agents.stack_config import load_stack_config
        stack_config = load_stack_config(effective_stack_id) or {}
    except Exception as e:
        logger.warning(f"[stack_rules] Config load failed for '{effective_stack_id}': {e}")
        stack_config = {}

    remaps = stack_config.get("import_remaps", {}) if isinstance(stack_config.get("import_remaps"), dict) else {}
    commands = stack_config.get("commands", {}) if isinstance(stack_config.get("commands"), dict) else {}
    testing = stack_config.get("testing", {}) if isinstance(stack_config.get("testing"), dict) else {}

    return {
        "version_pins": stack_config.get("version_pins") or VERSION_PINS,
        "dev_packages": stack_config.get("dev_packages") or JEST_REQUIRED_DEV_DEPS,
        "peer_dependency_minimums": stack_config.get("peer_dependency_minimums") or PEER_DEPENDENCY_MINIMUMS,
        "clerk_package_fixes": remaps.get("package_fixes") or CLERK_PACKAGE_FIXES,
        "test_fixes": remaps.get("test_fixes") or CLERK_TEST_MOCK_FIXES,
        "source_fixes": remaps.get("source_fixes") or CLERK_SOURCE_IMPORT_FIXES,
        "router_fixes": remaps.get("router_fixes") or NEXTJS_APP_ROUTER_IMPORT_FIXES,
        "test_command": commands.get("test") or "npx jest --coverage",
        "testing": testing,
    }


def _get_node_env() -> dict:
    """
    Returns os.environ with explicit Node.js binary paths prepended to PATH.
    Fixes 'npm not found' errors when subprocess.run doesn't inherit the shell PATH.
    """
    env = os.environ.copy()
    env["PATH"] = "/usr/local/bin:/usr/bin:/bin:" + env.get("PATH", "")
    return env


def _log_patch(patch_type: str, before: str, after: str, file: str = "", context: str = "") -> None:
    logger.info(
        f"[write_file] tool_patch_applied: "
        f"type={patch_type} | {before} → {after}"
        + (f" | file={file}" if file else "")
        + (f" | context={context}" if context else "")
    )


# --- Tool Definitions ---

MAX_TOOL_OUTPUT_CHARS = 1800
RAG_CACHE_MAX_SIZE = 50
_rag_cache: dict[str, str] = {}

# Hard rule: remapping des packages Clerk hallucinés par le LLM → @clerk/nextjs.
# La version cible vient uniquement du RAG (jamais hardcodée ici).
CLERK_PACKAGE_FIXES: dict[str, str] = {
    "@clerk/clerk-sdk": "@clerk/nextjs",
    "@clerk/clerk-js": "@clerk/nextjs",
    "@clerk/sdk": "@clerk/nextjs",
    "@clerk/react": "@clerk/nextjs",
}

# Hard rule: versions minimum de dépendances peer requises par next@14+.
# Ce sont des contraintes de compatibilité npm (faits techniques), pas des choix de stack.
# Les versions préférées (ex: react@18.3.1) restent dans le RAG.
PEER_DEPENDENCY_MINIMUMS: dict[str, str] = {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
}

# Hard rule: version pinnée pour next afin d'éviter les breaking changes LLM.
# next@15+ est incompatible avec le setup App Router Sprint 0 (Clerk V5, Prisma 7).
# La version préférée reste dans le RAG ; ici on bloque seulement les versions hors-périmètre.
VERSION_PINS: dict[str, str] = {
    "next": "14.2.25",
    "typescript": "^5.3.3",
}

# Hard rule: dépendances dev requises par jest.config.js + jest.setup.js injectés.
# Injectées dans devDependencies si absentes, pour éviter les échecs npm ci post-génération.
# Les versions préférées (ex: @testing-library/jest-dom@6.4) restent dans le RAG.
JEST_REQUIRED_DEV_DEPS: dict[str, str] = {
    "jest-environment-jsdom": "^29.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/react": "^14.0.0",
    "@babel/runtime": "^7.0.0",
    "node-mocks-http": "^1.14.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "14.2.25",
}


def _version_is_exact_and_below(version_str: str, minimum: str) -> bool:
    """True si version_str est un semver exact (sans ^ ~ > < * x) et numériquement inférieur à minimum."""
    if not isinstance(version_str, str) or not version_str:
        return False
    if any(c in version_str for c in ("^", "~", ">", "<", "*", "x", "X")):
        return False
    minimum_clean = minimum.lstrip("^~>=< ").strip()
    try:
        current_parts = tuple(int(p) for p in version_str.strip().split(".")[:3])
        minimum_parts = tuple(int(p) for p in minimum_clean.split(".")[:3])
        current_parts += (0,) * (3 - len(current_parts))
        minimum_parts += (0,) * (3 - len(minimum_parts))
        return current_parts < minimum_parts
    except (ValueError, AttributeError):
        return False


def _truncate_output(output: str, max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    if len(output) <= max_chars:
        return output
    half = max_chars // 2
    return (
        output[:half]
        + f"\n...[output tronque: {len(output) - max_chars} chars]...\n"
        + output[-half:]
    )


def _resolve_safe_path(path: str, base_dir: str = ".") -> tuple[bool, str]:
    if os.path.isabs(path):
        return False, "Absolute paths are forbidden for security reasons."
    base_abs = os.path.abspath(base_dir)
    candidate_abs = os.path.abspath(os.path.join(base_dir, path))
    if os.path.commonpath([base_abs, candidate_abs]) != base_abs:
        return False, "Path traversal outside project directory is forbidden."
    return True, candidate_abs


def _append_rag_usage_event(
    *,
    query: str,
    k: int,
    cache_hit: bool,
    run_id: str = "",
    doc_ids: list | None = None,
    scores: list | None = None,
    snippet: str = "",
    error: str | None = None,
) -> None:
    """
    Ecrit une trace d'usage RAG exploitable en audit (jsonl).
    Inclut les IDs Qdrant réels, les scores et un snippet du premier résultat.
    """
    try:
        metrics_dir = Path("logs/metrics")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / "rag_usage.jsonl"

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "agent": "dev_tool_rag_search",
            "query": query,
            "k": int(k),
            "cache_hit": bool(cache_hit),
            "result_count": len(doc_ids or []),
            "doc_ids": doc_ids or [],
            "scores": scores or [],
            "snippet": snippet,
            "error": error,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as log_err:
        logger.warning(f"RAG metrics logging failed: {log_err}")


def _is_valid_npm_package_name(name: str) -> bool:
    if not isinstance(name, str) or not name:
        return False
    if name != name.lower():
        return False
    # Scoped: @scope/name (exactly one slash)
    if name.startswith("@"):
        return bool(re.fullmatch(r"@[a-z0-9._-]+/[a-z0-9._-]+", name))
    # Non-scoped: no slash allowed
    if "/" in name:
        return False
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name))


def _normalize_npm_package_name(raw_name: str, fallback: str = "generated-app") -> str:
    candidate = (raw_name or "").strip().lower()
    candidate = re.sub(r"[^a-z0-9._-]+", "-", candidate).strip("-.")
    if _is_valid_npm_package_name(candidate):
        return candidate
    safe_fallback = re.sub(r"[^a-z0-9._-]+", "-", fallback.lower()).strip("-.") or "generated-app"
    if _is_valid_npm_package_name(safe_fallback):
        return safe_fallback
    return "generated-app"


def _sanitize_package_json(package_json_path: str, project_name: str) -> bool:
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
    except Exception as e:
        logger.warning(f"Impossible de sanitiser package.json: {e}")
        return False

    raw_content = _normalize_json_string(raw_content)
    try:
        package_data = json.loads(raw_content)
    except json.JSONDecodeError:
        # Tentative : décoder les escape sequences littérales (\n → newline)
        try:
            fixed = raw_content.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '')
            package_data = json.loads(fixed)
            # Réécrire le fichier décodé sur disque immédiatement
            with open(package_json_path, "w", encoding="utf-8") as f:
                f.write(fixed)
            logger.info("_sanitize_package_json: package.json double-encodé corrigé sur disque")
        except Exception as e:
            logger.warning(f"Impossible de sanitiser package.json: {e}")
            return False

    if not isinstance(package_data, dict):
        return False

    modified = False

    pkg_name = package_data.get("name")
    if isinstance(pkg_name, str) and not _is_valid_npm_package_name(pkg_name):
        new_name = _normalize_npm_package_name(project_name or "generated-app", "generated-app")
        package_data["name"] = new_name
        modified = True
        try:
            _write_learner_event(
                event_type="tool_patch_applied",
                payload={
                    "project_name": project_name or "default-project",
                    "success": True,
                    "file": "package.json",
                    "patch": "invalid_npm_package_name_fixed",
                    "field": "name",
                    "old_value": pkg_name,
                    "new_value": new_name,
                    "reason": "Nom de package npm invalide corrige (cause: EINVALIDPACKAGENAME)",
                },
                run_id=get_run_id(),
            )
        except Exception as e:
            logger.warning(f"Learner logging failed: {e}")

    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = package_data.get(section)
        if not isinstance(deps, dict):
            continue
        invalid_names = [name for name in list(deps.keys()) if not _is_valid_npm_package_name(name)]
        for name in invalid_names:
            deps.pop(name, None)
            modified = True
            try:
                _write_learner_event(
                    event_type="tool_patch_applied",
                    payload={
                        "project_name": project_name,
                        "success": True,
                        "file": "package.json",
                        "patch": "invalid_npm_package_removed",
                        "package_name": name,
                        "package_type": section,
                        "reason": "Package npm invalide supprimé (cause: EINVALIDPACKAGENAME)",
                    },
                    run_id=get_run_id(),
                )
            except Exception as e:
                logger.warning(f"Learner logging failed: {e}")

    stack_rules = _get_runtime_stack_rules()
    clerk_package_fixes = stack_rules["clerk_package_fixes"]

    # Hard rule: remapping packages Clerk invalides → @clerk/nextjs.
    # La version cible = celle déjà déclarée pour @clerk/nextjs dans le fichier,
    # ou "*" si absente. Ne jamais hériter la version du package invalide remplacé.
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = package_data.get(section)
        if not isinstance(deps, dict):
            continue
        # Capturer la version @clerk/nextjs AVANT toute suppression
        existing_nextjs_version = deps.get("@clerk/nextjs")
        for invalid_clerk_pkg, correct_pkg in clerk_package_fixes.items():
            if invalid_clerk_pkg in deps:
                deps.pop(invalid_clerk_pkg)
                modified = True
                if correct_pkg not in deps:
                    deps[correct_pkg] = existing_nextjs_version or "*"
                try:
                    _write_learner_event(
                        event_type="tool_patch_applied",
                        payload={
                            "project_name": project_name,
                            "success": True,
                            "type": "clerk_package_fix",
                            "file": "package.json",
                            "patch": "clerk_package_remapped",
                            "from": invalid_clerk_pkg,
                            "to": correct_pkg,
                            "version_set": deps.get(correct_pkg),
                            "package_type": section,
                            "reason": "Package Clerk invalide remappé vers @clerk/nextjs (hallucination LLM)",
                        },
                        run_id=get_run_id(),
                    )
                except Exception as e:
                    logger.warning(f"Learner logging failed: {e}")

    if modified:
        with open(package_json_path, "w", encoding="utf-8") as f:
            json.dump(package_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return modified


def _normalize_json_string(raw: str) -> str:
    """Nettoie une string JSON avant parsing :
    1. Strip whitespace
    2. Retire les wrappers markdown (```json ... ``` ou ``` ... ```)
    3. Si json.loads échoue → tente de décoder les escape sequences littérales (\\n → newline)
    Retourne le contenu nettoyé (peut encore être invalide si le JSON est vraiment cassé).
    """
    content = raw.strip()
    # Retirer wrapper markdown si présent
    if content.startswith("```"):
        lines = content.split('\n')
        start = 1
        end = len(lines) - 1 if lines and lines[-1].strip() == '```' else len(lines)
        content = '\n'.join(lines[start:end]).strip()
    return content


def _sanitize_package_json_content(content: str) -> str:
    """Applique CLERK_PACKAGE_FIXES et PEER_DEPENDENCY_MINIMUMS sur le contenu JSON brut.
    Retourne le JSON corrigé (indenté, avec \\n final).
    Gère le double-encodage (\\n littéraux) et les wrappers markdown générés par le LLM.
    Si le parse échoue après toutes les tentatives → retourne le contenu inchangé.
    Appelée par write_file() pour intercepter les hallucinations LLM à l'écriture.
    """
    content = _normalize_json_string(content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Tentative : décoder les escape sequences littérales (\n → newline)
        try:
            content_fixed = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '')
            data = json.loads(content_fixed)
            content = content_fixed
            logger.info("_sanitize_package_json_content: JSON double-encodé corrigé (\\\\n → newline)")
        except json.JSONDecodeError as e2:
            logger.warning(f"_sanitize_package_json_content: parse JSON échoué → contenu inchangé. {e2}")
            return content

    if not isinstance(data, dict):
        return content

    modified = False

    stack_rules = _get_runtime_stack_rules()
    clerk_package_fixes = stack_rules["clerk_package_fixes"]
    peer_dependency_minimums = stack_rules["peer_dependency_minimums"]
    version_pins = stack_rules["version_pins"]
    jest_required_dev_deps = stack_rules["dev_packages"]

    # Fix Clerk: remapping packages invalides → @clerk/nextjs sans hériter leur version.
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(section)
        if not isinstance(deps, dict):
            continue
        # Capturer la version @clerk/nextjs AVANT toute suppression
        existing_nextjs_version = deps.get("@clerk/nextjs")
        for invalid_clerk_pkg, correct_pkg in clerk_package_fixes.items():
            if invalid_clerk_pkg in deps:
                deps.pop(invalid_clerk_pkg)
                modified = True
                if correct_pkg not in deps:
                    deps[correct_pkg] = existing_nextjs_version or "*"
                _log_patch(
                    patch_type="clerk_package_fix",
                    before=invalid_clerk_pkg,
                    after=correct_pkg,
                    file="package.json",
                    context=f"section={section},version={deps.get(correct_pkg)}",
                )

    # Fix peer deps: versions exactes trop basses corrigées au minimum requis.
    for section in ("dependencies", "devDependencies"):
        deps = data.get(section)
        if not isinstance(deps, dict):
            continue
        for pkg, min_version in peer_dependency_minimums.items():
            current = deps.get(pkg)
            if isinstance(current, str) and _version_is_exact_and_below(current, min_version):
                _log_patch(
                    patch_type="peer_dep_fix",
                    before=f"{pkg}@{current}",
                    after=f"{pkg}@{min_version}",
                    file="package.json",
                )
                deps[pkg] = min_version
                modified = True

    # Fix version pins: force les versions critiques pour éviter breaking changes.
    for section in ("dependencies", "devDependencies"):
        deps = data.get(section)
        if not isinstance(deps, dict):
            continue
        for pkg, pinned_version in version_pins.items():
            if pkg in deps and deps[pkg] != pinned_version:
                _log_patch(
                    patch_type="version_pin",
                    before=f"{pkg}@{deps[pkg]}",
                    after=f"{pkg}@{pinned_version}",
                    file="package.json",
                )
                deps[pkg] = pinned_version
                modified = True

    # Inject jest required dev deps: ajoute si absent de devDependencies.
    dev_deps = data.setdefault("devDependencies", {})
    if isinstance(dev_deps, dict):
        for pkg, version in jest_required_dev_deps.items():
            if pkg not in dev_deps:
                _log_patch(
                    patch_type="dev_dependency_injected",
                    before=f"{pkg}=absent",
                    after=f"{pkg}@{version}",
                    file="package.json",
                )
                dev_deps[pkg] = version
                modified = True

    if not modified:
        return content
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


# Template Clerk V5 injecté quand withClerkMiddleware (V3/V4) est détecté.
_CLERK_V5_MIDDLEWARE_TEMPLATE = (
    "import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';\n\n"
    "const isProtectedRoute = createRouteMatcher(['/dashboard(.*)']);\n\n"
    "export default clerkMiddleware((auth, req) => {\n"
    "  if (isProtectedRoute(req)) auth().protect();\n"
    "});\n\n"
    "export const config = {\n"
    "  matcher: [\n"
    "    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',\n"
    "    '/(api|trpc)(.*)',\n"
    "  ],\n"
    "};\n"
)


def _sanitize_middleware_content(content: str) -> str:
    """Remplace les middlewares Clerk V3/V4 (withClerkMiddleware) par le template Clerk V5.
    Si withClerkMiddleware n'est pas présent → retourne le contenu inchangé.
    """
    if (
        "withClerkMiddleware" not in content
        and "withAuth(" not in content
        and "@clerk/nextjs/middleware" not in content
    ):
        return content
    _log_patch(
        patch_type="clerk_v4_to_v5_middleware",
        before="withClerkMiddleware|withAuth",
        after="clerkMiddleware",
        file="middleware.ts",
    )
    return _CLERK_V5_MIDDLEWARE_TEMPLATE


# Hard rule: remapping des imports Clerk invalides dans les fichiers de test.
# Le LLM hallucine @clerk/clerk-sdk et @clerk/nextjs/middleware dans les jest.mock().
CLERK_TEST_MOCK_FIXES: dict[str, str] = {
    "@clerk/clerk-sdk": "@clerk/nextjs",
    "@clerk/nextjs/api": "@clerk/nextjs/server",
    "@clerk/nextjs/middleware": "@clerk/nextjs/server",
}

# Hard rule: remapping imports Clerk legacy dans les fichiers source app.
CLERK_SOURCE_IMPORT_FIXES: dict[str, str] = {
    "@clerk/clerk-sdk": "@clerk/nextjs",
    "@clerk/clerk-sdk-react": "@clerk/nextjs",
    "@clerk/nextjs/api": "@clerk/nextjs/server",
    "@clerk/nextjs/middleware": "@clerk/nextjs/server",
}

# Hard rule: remapping imports Next.js Pages Router → App Router.
# next/router n'existe pas dans app/ — provoque un crash de compilation.
NEXTJS_APP_ROUTER_IMPORT_FIXES: dict[str, str] = {
    "next/router": "next/navigation",
}

# Les constantes ci-dessus restent des fallbacks.
# La config stack est désormais lue au runtime via _get_runtime_stack_rules().

# Template next.config.js canonique injecté si absent ou incomplet.
# eslint.ignoreDuringBuilds évite que les erreurs de lint LLM bloquent le build.
_NEXTCONFIG_TEMPLATE = """\
/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
}
module.exports = nextConfig
"""


def _sanitize_nextconfig_content(content: str) -> str:
    """
    Garantit que next.config.js a eslint.ignoreDuringBuilds = true.
    - Si déjà présent → retourne inchangé.
    - Si bloc eslint absent → injecte après le premier { de nextConfig ou module.exports.
    - Fallback → remplace par le template canonique.
    """
    if re.search(r"ignoreDuringBuilds\s*:\s*true", content):
        return content
    if re.search(r"ignoreDuringBuilds\s*:\s*false", content):
        _log_patch(
            patch_type="next_config_eslint_ignore",
            before="ignoreDuringBuilds:false",
            after="ignoreDuringBuilds:true",
            file="next.config.js",
        )
        return re.sub(r"ignoreDuringBuilds\s*:\s*false", "ignoreDuringBuilds: true", content)
    eslint_block = "\n  eslint: {\n    ignoreDuringBuilds: true,\n  },"
    for pattern in (r"(const nextConfig\s*=\s*\{)", r"(module\.exports\s*=\s*\{)"):
        m = re.search(pattern, content)
        if m:
            insert_pos = m.end()
            patched = content[:insert_pos] + eslint_block + content[insert_pos:]
            _log_patch(
                patch_type="next_config_eslint_ignore",
                before="eslint block missing",
                after="eslint.ignoreDuringBuilds:true",
                file="next.config.js",
            )
            return patched
    _log_patch(
        patch_type="next_config_eslint_ignore",
        before="unrecognized next.config.js",
        after="canonical template with eslint.ignoreDuringBuilds:true",
        file="next.config.js",
    )
    return _NEXTCONFIG_TEMPLATE


def _ensure_nextconfig_eslint_ignore(project_dir: str) -> None:
    """
    Appelle avant npm run build : s'assure que next.config.js a ignoreDuringBuilds = true.
    Crée le fichier si absent, le patche si présent.
    """
    config_path = os.path.join(project_dir, "next.config.js")
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                current = f.read()
            if re.search(r"ignoreDuringBuilds\s*:\s*true", current):
                return
            patched = _sanitize_nextconfig_content(current)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(patched)
            logger.info("[sanitize] next_config: eslint.ignoreDuringBuilds=true injecté")
        except Exception as e:
            logger.warning(f"[ensure_nextconfig] Impossible de patcher {config_path}: {e}")
    else:
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(_NEXTCONFIG_TEMPLATE)
            logger.info("[sanitize] next_config: eslint.ignoreDuringBuilds=true injecté")
        except Exception as e:
            logger.warning(f"[ensure_nextconfig] Impossible de créer {config_path}: {e}")


def _sanitize_test_content(content: str, path: str) -> str:
    """Corrige les imports Clerk invalides dans les fichiers de test/spec.
    Applique CLERK_TEST_MOCK_FIXES sur toutes les occurrences string dans le fichier.
    Si aucune occurrence → retourne le contenu inchangé.
    """
    modified_content = content
    test_fixes = _get_runtime_stack_rules().get("test_fixes", CLERK_TEST_MOCK_FIXES)
    for old, new in test_fixes.items():
        if old in modified_content:
            _log_patch(
                patch_type="clerk_mock_fix",
                before=old,
                after=new,
                file=path,
            )
            modified_content = modified_content.replace(old, new)
    return modified_content


def _sanitize_source_content(content: str, path: str) -> str:
    """
    Corrige les imports legacy Clerk dans les fichiers source et normalise
    les contenus one-line avec '\\n' litteraux emis par le LLM.
    """
    modified = content
    source_fixes = _get_runtime_stack_rules().get("source_fixes", CLERK_SOURCE_IMPORT_FIXES)
    router_fixes = _get_runtime_stack_rules().get("router_fixes", NEXTJS_APP_ROUTER_IMPORT_FIXES)
    for old, new in source_fixes.items():
        if old in modified:
            _log_patch(
                patch_type="clerk_import_fix",
                before=old,
                after=new,
                file=path,
            )
            modified = modified.replace(old, new)

    for old, new in router_fixes.items():
        if old in modified:
            _log_patch(
                patch_type="nextjs_router_fix",
                before=old,
                after=new,
                file=path,
            )
            modified = modified.replace(old, new)

    code_exts = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")
    if path.endswith(code_exts) and "\\n" in modified and "\n" not in modified:
        try:
            decoded = codecs.decode(modified, "unicode_escape")
            if "\n" in decoded:
                logger.info(f"[sanitize_source] escaped_newlines_decoded in {path}")
                modified = decoded
        except Exception:
            pass
    return modified


@tool
def rag_search(query: str) -> str:
    """
    Searches for development standards in the 'factory_standards' Qdrant collection.
    Uses a global, cached client for high performance and reliability.
    Example: rag_search("How to implement Clerk authentication?")
    """
    logger.info(f"Executing rag_search with query: '{query}'")
    if query in _rag_cache:
        _append_rag_usage_event(
            query=query,
            k=DEFAULT_VECTOR_SEARCH_LIMIT,
            cache_hit=True,
            run_id=get_run_id(),
            doc_ids=[],
            scores=[],
            snippet="",
            error=None,
        )
        return _rag_cache[query]
    if not qdrant_client or not openai_embeddings:
        logger.error("RAG search failed: Qdrant client or embeddings not initialized.")
        _append_rag_usage_event(
            query=query,
            k=DEFAULT_VECTOR_SEARCH_LIMIT,
            cache_hit=False,
            run_id=get_run_id(),
            doc_ids=[],
            scores=[],
            snippet="",
            error="vectorstore_not_initialized",
        )
        return "Aucun résultat (erreur de recherche)."

    try:
        query_vector = openai_embeddings.embed_query(query)
        qdrant_filter = None
        try:
            from agents.stack_config import load_stack_config
            stack_id = get_stack_id()
            qdrant_filter = load_stack_config(stack_id).get("qdrant_filter", {}).get("filter")
        except Exception as _filter_err:
            logger.warning(f"[rag_search] stack filter unavailable: {_filter_err}")

        search_hits = []
        if hasattr(qdrant_client, "search"):
            search_hits = qdrant_client.search(
                collection_name=QDRANT_COLLECTION_NAME,
                query_vector=query_vector,
                limit=DEFAULT_VECTOR_SEARCH_LIMIT,
                with_payload=True,
                query_filter=qdrant_filter,
            )
        elif hasattr(qdrant_client, "search_points"):
            search_result = qdrant_client.search_points(
                collection_name=QDRANT_COLLECTION_NAME,
                vector=query_vector,
                limit=DEFAULT_VECTOR_SEARCH_LIMIT,
                with_payload=True,
                query_filter=qdrant_filter,
            )
            search_hits = getattr(search_result, "points", search_result)
        elif vectorstore:
            search_hits = vectorstore.similarity_search_with_score(
                query, k=DEFAULT_VECTOR_SEARCH_LIMIT, filter=qdrant_filter
            )

        if search_hits and isinstance(search_hits[0], tuple):
            doc_ids = [str(i) for i, _ in enumerate(search_hits)]
            scores = [float(score) for _, score in search_hits]
            result = "\n\n".join(str(doc.page_content) for doc, _ in search_hits)
            snippet = str(search_hits[0][0].page_content)[:180]
        else:
            doc_ids = [str(h.id) for h in search_hits]
            scores = [float(h.score) for h in search_hits]
            result = "\n\n".join(
                str(h.payload.get("page_content", "")) for h in search_hits
            )
            snippet = str(search_hits[0].payload.get("page_content", ""))[:180] if search_hits else ""
        _append_rag_usage_event(
            query=query,
            k=DEFAULT_VECTOR_SEARCH_LIMIT,
            cache_hit=False,
            run_id=get_run_id(),
            doc_ids=doc_ids,
            scores=scores,
            snippet=snippet,
            error=None,
        )
        if len(_rag_cache) >= RAG_CACHE_MAX_SIZE:
            _rag_cache.pop(next(iter(_rag_cache)))
        _rag_cache[query] = result
        return result
    except Exception as e:
        logger.error(f"RAG search encountered an error: {e}")
        _append_rag_usage_event(
            query=query,
            k=DEFAULT_VECTOR_SEARCH_LIMIT,
            cache_hit=False,
            run_id=get_run_id(),
            doc_ids=[],
            scores=[],
            snippet="",
            error=str(e),
        )
        return "Aucun résultat (erreur de recherche)."

class WriteFileArgs(BaseModel):
    path: str = Field(description="The relative project path for the file. E.g., 'src/components/Button.tsx'. Absolute paths are not allowed.")
    content: str = Field(description="The complete and final content to be written to the file.")

@tool(args_schema=WriteFileArgs)
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file at a specified relative path. Overwrites existing files.
    For security, absolute paths are prohibited.
    """
    # Security check: prevent writing outside the project directory.
    is_safe, safe_path_or_err = _resolve_safe_path(path)
    if not is_safe:
        return f"Error: {safe_path_or_err}"

    try:
        safe_path = safe_path_or_err
        normalized_path = path.replace("\\", "/")
        if normalized_path.startswith(("pages/", "src/pages/")):
            app_router_present = os.path.isdir("app") or os.path.isdir(os.path.join("src", "app"))
            if app_router_present:
                logger.info(
                    f"[sanitize] pages_router_blocked: '{path}' ignoré — App Router détecté"
                )
                return (
                    f"Skipped file '{path}': App Router detected, pages router paths are blocked."
                )
        # Log if the file already exists to track overwrites.
        if os.path.exists(safe_path):
            logger.warning(f"File '{path}' already exists and will be overwritten.")
        
        parent_dir = os.path.dirname(safe_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        if path in ("next.config.js", "middleware.ts", "app/middleware.ts"):
            # Logger le patch avant de l'appliquer
            if "source: '/protected/**'" in content or 'source: "/protected/**"' in content:
                try:
                    _write_learner_event(
                        event_type="tool_patch_applied",
                        payload={
                            "project_name": os.path.basename(os.path.dirname(path) or path),
                            "success": True,
                            "file": os.path.basename(path),
                            "patch": "middleware_matcher_fix",
                            "from": "/protected/**",
                            "to": "/protected/(.*)",
                            "reason": "Next.js 14 App Router incompatibility",
                        },
                        run_id=get_run_id(),
                    )
                except Exception as e:
                    logger.warning(f"Learner logging failed: {e}")
            content = content.replace(
                "source: '/protected/**'",
                "source: '/protected/(.*)'"
            )
            content = content.replace(
                'source: "/protected/**"',
                'source: "/protected/(.*)"'
            )
            # Clerk V4 → V5 : remplace withClerkMiddleware par clerkMiddleware
            if os.path.basename(path) == "middleware.ts":
                content = _sanitize_middleware_content(content)
            elif os.path.basename(path) == "next.config.js":
                content = _sanitize_nextconfig_content(content)
        # Clerk package fix: remplace les packages Clerk invalides avant toute écriture disque.
        # Ceci intercepte les hallucinations LLM (@clerk/clerk-sdk, etc.) même si le LLM
        # appelle write_file plusieurs fois au cours de la boucle ReAct.
        filename = os.path.basename(path)
        if filename == "package.json":
            content = _sanitize_package_json_content(content)
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                return f"Error writing file '{path}': package.json invalide généré : {e}"
        elif path.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
            content = _sanitize_source_content(content, path)
        # Sanitize test files: corrige les imports Clerk invalides dans les fichiers test/spec.
        if any(x in path for x in ("test", "spec", "__tests__")):
            content = _sanitize_test_content(content, path)
        with open(safe_path, "w", encoding='utf-8') as f:
            f.write(content)
        return f"File '{path}' was written successfully."
    except Exception as e:
        return f"Error writing file '{path}': {e}"

class ValidateSyntaxArgs(BaseModel):
    file_path: str = Field(description="The relative path of the file to validate. Supported extensions: .js, .ts, .tsx, .prisma.")

@tool(args_schema=ValidateSyntaxArgs)
def validate_syntax(file_path: str) -> str:
    """
    Validates the syntax of a file using external tools (ESLint for JS/TS, Prisma for schema).
    It relies on a central .eslintrc.json file for robust validation rules.
    Includes a timeout to prevent indefinite hangs.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    working_dir = '.' 

    try:
        if file_path.endswith((".js", ".ts", ".tsx")):
            command = ['npx', 'eslint', file_path]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=SUBPROCESS_TIMEOUT_SHORT,
                cwd=working_dir,
                env=_get_node_env(),
            )
            return f"ESLint validation for {file_path} successful."
        
        elif file_path.endswith(".prisma"):
            command = ['npx', 'prisma', 'validate', '--schema', file_path]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=SUBPROCESS_TIMEOUT_SHORT,
                cwd=working_dir,
                env=_get_node_env(),
            )
            return f"Prisma validation for {file_path} successful."
            
        else:
            return f"Validation not supported for file type: {file_path}. Skipping."
            
    except subprocess.TimeoutExpired:
        return f"Validation timed out for '{file_path}' after {SUBPROCESS_TIMEOUT_SHORT} seconds."
    except subprocess.CalledProcessError as e:
        return _truncate_output(
            f"Validation error for '{file_path}' (Exit Code: {e.returncode}):\n"
            f"STDOUT:\n{e.stdout}\n"
            f"STDERR:\n{e.stderr}"
        )
    except FileNotFoundError:
        return "Error: 'npx' not found. Please ensure Node.js and npm are installed."
    except Exception as e:
        return f"An unexpected error occurred during validation of '{file_path}': {e}"

class PrismaMigrateArgs(BaseModel):
    schema_path: str = Field(description="The relative path to the 'schema.prisma' file.")

@tool(args_schema=PrismaMigrateArgs)
def prisma_migrate(schema_path: str) -> str:
    """
    Executes a Prisma migration conditionally. It first checks the migration status.
    If the database is out of sync or does not exist, it runs 'migrate dev'.
    Includes a retry mechanism to handle filesystem sync delays.
    """
    # --- START MODIFICATION ---
    # Retry loop to wait for the file to be available
    max_retries = 5
    retry_delay = 0.5 # seconds
    for attempt in range(max_retries):
        if os.path.exists(schema_path):
            logger.info(f"Schema file found at '{schema_path}' on attempt {attempt + 1}.")
            break
        logger.warning(f"Schema file not found at '{schema_path}' on attempt {attempt + 1}. Retrying in {retry_delay}s...")
        time.sleep(retry_delay)
    else:
        # This 'else' belongs to the 'for' loop and runs if the loop completes without a 'break'
        logger.error(f"Schema file not found at '{schema_path}' after {max_retries} retries.")
        return f"Error: Schema file not found at '{schema_path}' after multiple retries."
    # --- END MODIFICATION ---

    schema_dir = os.path.dirname(schema_path) or '.'

    # Prisma 7 hard rule: la propriété url dans datasource de schema.prisma est supprimée.
    # Détecter et corriger automatiquement avant toute commande Prisma.
    try:
        with open(schema_path, "r", encoding="utf-8") as _sf:
            _schema_content = _sf.read()
        if "datasource" in _schema_content and re.search(r'url\s*=\s*env\(', _schema_content):
            logger.warning(
                "Prisma 7 breaking change détecté: url dans datasource → génération prisma.config.ts"
            )
            _env_match = re.search(r'url\s*=\s*env\(["\']([^"\']+)["\']\)', _schema_content)
            _env_var = _env_match.group(1) if _env_match else "DATABASE_URL"
            _prisma_config_content = (
                "import { defineConfig } from 'prisma'\n"
                "export default defineConfig({\n"
                "  datasource: {\n"
                f"    url: process.env.{_env_var},\n"
                "  },\n"
                "})\n"
            )
            _prisma_config_path = os.path.join(schema_dir, "prisma.config.ts")
            with open(_prisma_config_path, "w", encoding="utf-8") as _cf:
                _cf.write(_prisma_config_content)
            _fixed_schema = re.sub(
                r'\n[ \t]*url\s*=\s*env\(["\'][^"\']+["\']\)[^\n]*', '', _schema_content
            )
            with open(schema_path, "w", encoding="utf-8") as _sf2:
                _sf2.write(_fixed_schema)
            try:
                _write_learner_event(
                    event_type="tool_patch_applied",
                    payload={
                        "project_name": os.path.basename(schema_dir),
                        "success": True,
                        "type": "prisma7_datasource_fix",
                        "file": "schema.prisma",
                        "patch": "datasource_url_removed",
                        "env_var": _env_var,
                        "prisma_config_generated": _prisma_config_path,
                        "reason": "Prisma 7: url dans datasource supprimé, prisma.config.ts généré",
                    },
                    run_id=get_run_id(),
                )
            except Exception as _le:
                logger.warning(f"Learner logging failed: {_le}")
    except Exception as _pe:
        logger.warning(f"Vérification Prisma 7 datasource échouée: {_pe}")

    try:
        # Step 1: Check current migration status...
        logger.info(f"Checking Prisma migration status for '{schema_path}'...")
        status_command = ['npx', 'prisma', 'migrate', 'status', '--schema', schema_path]
        status_result = subprocess.run(
            status_command,
            capture_output=True,
            text=True,
            cwd=schema_dir,
            timeout=SUBPROCESS_TIMEOUT_MEDIUM,
            env=_get_node_env(),
        )

        # Step 2: Decide if migration is needed.
        # Run migration if status command failed (e.g., DB not found) or if schema is out of sync.
        run_migration = False
        if status_result.returncode != 0:
            logger.warning(f"Prisma migrate status failed (Exit Code: {status_result.returncode}). A migration is likely needed.\nSTDERR: {status_result.stderr}")
            run_migration = True
        elif "Database schema is not in sync" in status_result.stdout or "migrations to apply" in status_result.stdout:
            logger.info("Database schema is out of sync. A migration is needed.")
            run_migration = True
        else:
            logger.info("Prisma migration check: Database is up to date. No migration needed.")
            return f"Prisma migration check for '{schema_path}': Database is up to date."

        if run_migration:
            # Step 3: Generate a unique migration name and run the migration.
            logger.info("Executing prisma migrate dev...")
            migration_name = 'init_' + datetime.now().strftime("%Y%m%d_%H%M%S")
            migrate_command = ['npx', 'prisma', 'migrate', 'dev', '--name', migration_name, '--schema', schema_path]
            
            # Using check=True here because failure at this stage is a genuine error for the agent.
            result = subprocess.run(
                migrate_command,
                capture_output=True,
                text=True,
                check=True,
                cwd=schema_dir,
                timeout=SUBPROCESS_TIMEOUT_MEDIUM,
                env=_get_node_env(),
            )
            return _truncate_output(
                f"Prisma migration '{migration_name}' for '{schema_path}' successful:\n{result.stdout}"
            )
        
        # This part should not be reached due to the logic above, but as a safeguard:
        return "Prisma migration check completed with no action taken."

    except subprocess.TimeoutExpired:
        return f"Prisma migration timed out for '{schema_path}' after {SUBPROCESS_TIMEOUT_MEDIUM} seconds."
    except subprocess.CalledProcessError as e:
        return _truncate_output(
            f"Error during Prisma migration for '{schema_path}' (Exit Code: {e.returncode}):\n"
            f"STDOUT:\n{e.stdout}\n"
            f"STDERR:\n{e.stderr}"
        )
    except FileNotFoundError:
        return "Error: 'npx' or 'prisma' not found. Please ensure Node.js and npm are installed."
    except Exception as e:
        return f"An unexpected error occurred during Prisma migration: {e}"

class ReadFileArgs(BaseModel):
    path: str = Field(description="The relative project path for the file to read. E.g., 'src/components/Button.tsx'.")

@tool(args_schema=ReadFileArgs)
def read_files(path: str) -> str:
    """
    Reads the content of a file at a specified relative path and returns it as a string.
    """
    is_safe, safe_path_or_err = _resolve_safe_path(path)
    if not is_safe:
        return f"Error: {safe_path_or_err}"
    safe_path = safe_path_or_err

    if not os.path.exists(safe_path):
        return f"Error: File not found at '{path}'"
    try:
        with open(safe_path, "r", encoding='utf-8') as f:
            content = f.read()
        return _truncate_output(content)
    except Exception as e:
        return f"Error reading file '{path}': {e}"

class RunBuildArgs(BaseModel):
    project_dir: str = Field(description="Répertoire racine du projet (défaut: '.')", default='.')


def _remove_pages_router_conflicts(project_dir: str) -> None:
    app_dir = os.path.join(project_dir, "app")
    pages_dir = os.path.join(project_dir, "pages")
    src_pages_dir = os.path.join(project_dir, "src", "pages")
    if os.path.isdir(app_dir) and os.path.isdir(pages_dir):
        shutil.rmtree(pages_dir)
        logger.info("[sanitize] pages_router_conflict: dossier pages/ supprimé — App Router prime")
    if os.path.isdir(app_dir) and os.path.isdir(src_pages_dir):
        shutil.rmtree(src_pages_dir)
        logger.info("[sanitize] pages_router_conflict: dossier src/pages/ supprimé — App Router prime")


def _remove_problematic_babel_config(project_dir: str) -> None:
    """
    Next.js 14 + Clerk compile plus stablement sans Babel custom genere par le LLM.
    On force SWC en supprimant les fichiers Babel custom avant build.
    """
    for rel in (".babelrc", "babel.config.js", "babel.config.cjs", "babel.config.mjs"):
        p = os.path.join(project_dir, rel)
        if os.path.isfile(p):
            os.remove(p)
            logger.info(f"[sanitize] babel_config_removed: '{rel}' supprimé — SWC par défaut")


def _apply_clerk_middleware_v5(project_dir: str) -> None:
    """
    Applique le template Clerk v5 sur middleware.ts si nécessaire.
    Utilise _sanitize_middleware_content() pour détecter et corriger.
    """
    path = os.path.join(project_dir, "middleware.ts")
    if not os.path.exists(path):
        return
    try:
        current = Path(path).read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"[sanitize] Failed reading middleware.ts: {e}")
        return
    updated = _sanitize_middleware_content(current)
    if updated != current:
        try:
            Path(path).write_text(updated, encoding="utf-8")
            logger.info("[sanitize] middleware.ts updated to Clerk v5 template.")
        except Exception as e:
            logger.warning(f"[sanitize] Failed writing middleware.ts: {e}")


# Minimal sanitizer registry (Sprint 3 compromise)
SANITIZER_REGISTRY = {
    "remove_pages_conflicts": _remove_pages_router_conflicts,
    "clerk_middleware_v5": _apply_clerk_middleware_v5,
    "remove_problematic_babel": _remove_problematic_babel_config,
    "ensure_nextconfig": _ensure_nextconfig_eslint_ignore,
}


def apply_sanitizers(project_dir: str, sanitizer_names: list[str]) -> None:
    """Applique les sanitizers listés par nom (no-op si inconnu)."""
    for name in sanitizer_names or []:
        sanitizer = SANITIZER_REGISTRY.get(name)
        if sanitizer:
            sanitizer(project_dir)
        else:
            logger.warning(f"[sanitize] Sanitizer unknown: {name}")


def _remove_pages_tests_router_conflicts(project_dir: str, incoming_files: dict | None = None) -> None:
    """
    Si App Router est present, supprime les tests legacy pages/ quand ils ne sont
    pas explicitement regénérés par l'itération courante.
    """
    app_dir = os.path.join(project_dir, "app")
    pages_tests_dir = os.path.join(project_dir, "tests", "pages")
    if not (os.path.isdir(app_dir) and os.path.isdir(pages_tests_dir)):
        return

    incoming_paths = set((incoming_files or {}).keys())
    regenerates_pages_tests = any(
        p.replace("\\", "/").startswith("tests/pages/")
        for p in incoming_paths
    )
    if not regenerates_pages_tests:
        shutil.rmtree(pages_tests_dir)
        logger.info("[sanitize] pages_tests_conflict: dossier tests/pages/ supprimé — App Router prime")


def _remove_stale_tests(
    project_dir: str,
    incoming_files: dict | None = None,
    force_cleanup_without_generated_tests: bool = False,
) -> None:
    """
    Supprime les tests existants qui ne sont pas regénérés par l'itération courante.
    Évite les tests obsolètes qui cassent le run.
    """
    if not incoming_files:
        return
    incoming_paths = set(incoming_files.keys())
    if (
        not force_cleanup_without_generated_tests
        and not any(p.startswith("tests/") for p in incoming_paths)
    ):
        return
    tests_dir = os.path.join(project_dir, "tests")
    if not os.path.isdir(tests_dir):
        return
    removed = 0
    for root, _, files in os.walk(tests_dir):
        for name in files:
            rel_path = os.path.relpath(os.path.join(root, name), project_dir).replace("\\", "/")
            if rel_path.startswith("tests/") and rel_path not in incoming_paths:
                try:
                    os.remove(os.path.join(project_dir, rel_path))
                    removed += 1
                except Exception:
                    pass
    if removed:
        logger.info(f"[sanitize] stale_tests_removed: {removed} fichiers obsoletes")


def _is_test_file_path(path: str) -> bool:
    rel = path.replace("\\", "/").lower()
    return (
        rel.startswith("tests/")
        or "/__tests__/" in f"/{rel}"
        or rel.endswith(".test.ts")
        or rel.endswith(".test.tsx")
        or rel.endswith(".test.js")
        or rel.endswith(".test.jsx")
        or rel.endswith(".spec.ts")
        or rel.endswith(".spec.tsx")
        or rel.endswith(".spec.js")
        or rel.endswith(".spec.jsx")
    )


def _count_test_files(project_dir: str) -> int:
    count = 0
    for root, _, files in os.walk(project_dir):
        for name in files:
            rel_path = os.path.relpath(os.path.join(root, name), project_dir).replace("\\", "/")
            if _is_test_file_path(rel_path):
                count += 1
    return count


@tool(args_schema=RunBuildArgs)
def run_build(project_dir: str = '.') -> str:
    """
    Executes 'npm install' then 'npm run build' in the specified project directory to validate the build process.
    Returns a detailed error message if the build or install fails, for use in ReAct loops.
    """
    logger.info(f"Executing 'npm install' and 'npm run build' in directory '{project_dir}'...")

    package_json_path = os.path.join(project_dir, 'package.json')
    if not os.path.exists(package_json_path):
        root_package_json = os.path.join('.', 'package.json')
        if project_dir != '.' and os.path.exists(root_package_json):
            logger.warning(
                f"package.json absent dans '{project_dir}', fallback automatique vers '.'."
            )
            project_dir = '.'
            package_json_path = root_package_json
        else:
            return f"Error: package.json not found at '{package_json_path}'. Cannot run build."
    project_name = os.path.basename(project_dir) or "default-project"
    sanitized = _sanitize_package_json(package_json_path, project_name)
    if sanitized:
        logger.info("package.json sanitized")

    try:
        # Step 1: Run npm install (strict first, fallback to --legacy-peer-deps)
        logger.info(f"Running npm install in '{project_dir}'...")
        install_result = subprocess.run(
            ['npm', 'install'],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=SUBPROCESS_TIMEOUT_LONG,
            env=_get_node_env(),
        )
        if install_result.returncode != 0:
            logger.warning(
                f"npm install failed (code {install_result.returncode}), "
                "retrying with --legacy-peer-deps...\n"
                f"STDERR: {install_result.stderr[:400]}"
            )
            install_result2 = subprocess.run(
                ['npm', 'install', '--legacy-peer-deps'],
                capture_output=True,
                text=True,
                cwd=project_dir,
                timeout=SUBPROCESS_TIMEOUT_LONG,
                env=_get_node_env(),
            )
            if install_result2.returncode != 0:
                error_message = _truncate_output(
                    f"npm install --legacy-peer-deps failed (code {install_result2.returncode}):\n"
                    f"STDOUT:\n{install_result2.stdout}\nSTDERR:\n{install_result2.stderr}"
                )
                logger.error(error_message)
                return error_message
            logger.info("npm install --legacy-peer-deps completed successfully.")
        else:
            logger.info("npm install completed successfully.")

        # Step 2: Run npm run build
        try:
            from agents.stack_config import load_stack_config
            stack_id = get_stack_id()
            sanitizers = load_stack_config(stack_id).get("sanitizers", [])
            apply_sanitizers(project_dir, sanitizers)
        except Exception as sanit_err:
            logger.warning(f"[sanitize] apply_sanitizers failed: {sanit_err}")
        _ensure_nextconfig_eslint_ignore(project_dir)
        try:
            validate_blueprint(project_dir, stack_id=stack_id)
        except ValueError as e:
            return f"Blueprint validation failed: {e}"
        logger.info(f"Running npm run build in '{project_dir}'...")
        build_command = ['npm', 'run', 'build']
        result = subprocess.run(
            build_command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
            timeout=SUBPROCESS_TIMEOUT_LONG,
            env=_get_node_env(),
        )
        logger.info(f"Build successful in '{project_dir}'.")
        return _truncate_output(f"Build successful: {result.stdout}")
    except subprocess.TimeoutExpired as e:
        return f"Command timed out in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds: {e.cmd}"
    except subprocess.CalledProcessError as e:
        try:
            error_signature = _extract_build_error_signature(e.stderr or "")
            _write_learner_event(
                event_type="build_failed",
                payload={
                    "success": False,
                    "error_signature": error_signature,
                    "return_code": e.returncode,
                    "stack_id": get_stack_id(),
                    "stderr_full": e.stderr or "",
                    "stdout_full": e.stdout or "",
                    "stderr_snippet": (e.stderr or "")[-500:],
                    "stdout_snippet": (e.stdout or "")[-500:],
                },
                run_id=get_run_id(),
            )
        except Exception as log_err:
            logger.warning(f"[build_failed] Learner logging failed: {log_err}")
        error_message = _truncate_output(
            f"Command failed (code {e.returncode}): {e.cmd}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        )
        logger.error(error_message)
        return error_message
    except FileNotFoundError:
        return "Error: 'npm' not found. Please ensure Node.js and npm are installed and in the PATH."
    except Exception as e:
        return f"An unexpected error occurred during build process: {e}"


def _extract_build_error_signature(stderr: str) -> str:
    """
    Extrait une signature compacte d'erreur pour anti-patterns (Sprint 4).
    """
    if not stderr:
        return "unknown"

    ts_match = re.search(r"(TS\\d+):\\s*([^\\n]+)", stderr)
    if ts_match:
        return f"typescript_{ts_match.group(1)}_{ts_match.group(2)[:80]}"

    next_match = re.search(r"Error:\\s*([^\\n]+)", stderr)
    if next_match:
        return f"nextjs_{next_match.group(1)[:80]}"

    npm_match = re.search(r"npm error\\s+([A-Z0-9_]+)", stderr)
    if npm_match:
        return f"npm_{npm_match.group(1)}"

    return f"build_error_{stderr.strip()[:80]}"
class RunTestsArgs(BaseModel):
    project_dir: str = Field(description="Répertoire racine du projet (défaut: '.')", default='.')
    files: dict = Field(description="A dictionary of files to write to disk before running tests, with path as key and content as value.")


def _major_from_version(version: str) -> int | None:
    if not isinstance(version, str):
        return None
    match = re.search(r"(\d+)", version)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _collect_package_version_mismatches(package_json: dict) -> list[dict]:
    mismatches: list[dict] = []
    deps = package_json.get("dependencies", {}) if isinstance(package_json, dict) else {}
    dev_deps = package_json.get("devDependencies", {}) if isinstance(package_json, dict) else {}

    ts_jest_version = dev_deps.get("ts-jest")
    if isinstance(ts_jest_version, str):
        ts_jest_major = _major_from_version(ts_jest_version)
        if ts_jest_major is not None and ts_jest_major != 29:
            mismatches.append(
                {
                    "package": "ts-jest",
                    "current": ts_jest_version,
                    "expected": "29.x",
                    "issue": "incompatible_version",
                }
            )

    # Hard rule: jest@30 est incompatible avec ts-jest@29 → bloquer en amont.
    jest_version = dev_deps.get("jest") or deps.get("jest")
    if isinstance(jest_version, str):
        jest_major = _major_from_version(jest_version)
        if jest_major is not None and jest_major >= 30:
            mismatches.append(
                {
                    "package": "jest",
                    "current": jest_version,
                    "expected": "29.x",
                    "issue": "incompatible_version",
                }
            )

    next_version = deps.get("next")
    if isinstance(next_version, str):
        next_major = _major_from_version(next_version)
        if next_major is not None and next_major < 14:
            mismatches.append(
                {
                    "package": "next",
                    "current": next_version,
                    "expected": ">=14",
                    "issue": "incompatible_version",
                }
            )

    return mismatches


@tool(args_schema=RunTestsArgs)
def run_tests(project_dir: str = '.', files: dict = None) -> str:
    """
    Writes a dictionary of files to disk, then executes 'npx jest --coverage' in the specified project directory.
    Installs dependencies using 'npm ci' or 'npm install' if a package.json is found.
    Returns a detailed error message if tests fail, for use in ReAct loops.
    """
    logger.info(f"Executing tests in directory '{project_dir}'...")

    stack_rules = _get_runtime_stack_rules()
    testing_cfg = stack_rules.get("testing", {})
    cleanup_stale_tests = str(testing_cfg.get("cleanup_stale_tests", "if_tests_generated")).lower()
    force_cleanup = cleanup_stale_tests == "always"
    min_required_tests = int(testing_cfg.get("min_required_tests", 1))
    allow_zero_tests_debug = bool(testing_cfg.get("allow_zero_tests_debug", False))

    _remove_pages_router_conflicts(project_dir)
    _remove_pages_tests_router_conflicts(project_dir, files)
    _remove_stale_tests(
        project_dir,
        files,
        force_cleanup_without_generated_tests=force_cleanup,
    )

    if files:
        logger.info(f"Writing {len(files)} files to disk before running tests...")
        for path, content in files.items():
            try:
                # Ensure parent directories exist
                is_safe, safe_path_or_err = _resolve_safe_path(path, project_dir)
                if not is_safe:
                    return f"Error writing file '{path}': {safe_path_or_err}"
                safe_path = safe_path_or_err
                parent_dir = os.path.dirname(safe_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                
                content_to_write = content
                try:
                    # Decode escaped characters like \\n into \n for all files
                    content_to_write = codecs.decode(content, 'unicode_escape')
                except Exception as e:
                    # Log but don't fail if decoding fails for non-package.json files
                    logger.warning(f"Warning: Failed to decode unicode escape for '{path}'. Details: {e}. Original content: {content}")
                    # Fallback to original content if decoding fails
                    content_to_write = content

                # Sanitize package.json specifically
                if path == 'package.json':
                    logger.info("Sanitizing package.json before writing...")
                    try:
                        parsed_package_json = json.loads(content_to_write)
                        mismatches = _collect_package_version_mismatches(parsed_package_json)
                        if mismatches:
                            try:
                                _write_learner_event(
                                    event_type="version_mismatch_detected",
                                    payload={
                                        "project_name": os.path.basename(project_dir),
                                        "success": False,
                                        "file": "package.json",
                                        "mismatches": mismatches,
                                        "mode": "report_only",
                                    },
                                    run_id=get_run_id(),
                                )
                            except Exception as e:
                                logger.warning(f"Learner logging failed: {e}")
                            return (
                                "Version mismatches detected in package.json: "
                                f"{json.dumps(mismatches, ensure_ascii=False)}. "
                                "Fix suggestion: update package.json using RAG standards, then rerun tests."
                            )
                        with open(safe_path, "w", encoding="utf-8") as tmp_f:
                            json.dump(parsed_package_json, tmp_f, ensure_ascii=False, indent=2)
                            tmp_f.write("\n")
                        _sanitize_package_json(
                            safe_path,
                            os.path.basename(project_dir) or "default-project",
                        )
                        with open(safe_path, "r", encoding="utf-8") as tmp_f:
                            content_to_write = tmp_f.read()
                    except Exception as e:
                        logger.warning(f"Pré-sanitize package.json ignoré: {e}")
                # Keep Clerk/Jest imports compatible when tests are written by run_tests
                if any(x in path for x in ("test", "spec", "__tests__")):
                    content_to_write = _sanitize_test_content(content_to_write, path)

                with open(safe_path, "w", encoding='utf-8') as f:
                    f.write(content_to_write)
                logger.info(f"Successfully wrote file: {path}")
            except Exception as e:
                error_msg = f"Error writing file '{path}' at the start of run_tests: {e}"
                logger.error(error_msg)
                return error_msg
    
    # --- Ensure critical config files exist for testing ---
    # Grok's recommendation: Inject standard tsconfig.json and jest.setup.js if they don't exist.
    
    # tsconfig.json content
    tsconfig_content = """{
  "compilerOptions": {
    "target": "es2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "baseUrl": ".",
    "paths": { "@/*": ["./*"] }
  },
  "include": ["**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}"""
    tsconfig_path = os.path.join(project_dir, 'tsconfig.json')
    if not os.path.exists(tsconfig_path):
        logger.info(f"Writing default tsconfig.json to '{tsconfig_path}'...")
        try:
            try:
                _write_learner_event(
                    event_type="tool_patch_applied",
                    payload={
                        "project_name": os.path.basename(project_dir),
                        "success": True,
                        "file": "tsconfig.json",
                        "patch": "config_injection",
                        "reason": "Missing config file generated by tool",
                    },
                    run_id=get_run_id(),
                )
            except Exception as e:
                logger.warning(f"Learner logging failed: {e}")
            with open(tsconfig_path, "w", encoding='utf-8') as f:
                f.write(tsconfig_content)
            logger.info(f"Successfully wrote file: {tsconfig_path}")
        except Exception as e:
            error_msg = f"Error writing default tsconfig.json: {e}"
            logger.error(error_msg)
            return error_msg

    # jest.setup.js content
    jest_setup_content = """import '@testing-library/jest-dom';"""
    jest_setup_path = os.path.join(project_dir, 'jest.setup.js')
    if not os.path.exists(jest_setup_path):
        logger.info(f"Writing default jest.setup.js to '{jest_setup_path}'...")
        try:
            try:
                _write_learner_event(
                    event_type="tool_patch_applied",
                    payload={
                        "project_name": os.path.basename(project_dir),
                        "success": True,
                        "file": "jest.setup.js",
                        "patch": "config_injection",
                        "reason": "Missing config file generated by tool",
                    },
                    run_id=get_run_id(),
                )
            except Exception as e:
                logger.warning(f"Learner logging failed: {e}")
            with open(jest_setup_path, "w", encoding='utf-8') as f:
                f.write(jest_setup_content)
            logger.info(f"Successfully wrote file: {jest_setup_path}")
        except Exception as e:
            error_msg = f"Error writing default jest.setup.js: {e}"
            logger.error(error_msg)
            return error_msg

    # jest.config.js content
    jest_config_content = """module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@clerk/nextjs/middleware$': '<rootDir>/__mocks__/clerk-middleware.js',
  },
};"""
    jest_config_path = os.path.join(project_dir, 'jest.config.js')
    if not os.path.exists(jest_config_path):
        logger.info(f"Writing default jest.config.js to '{jest_config_path}'...")
        try:
            try:
                _write_learner_event(
                    event_type="tool_patch_applied",
                    payload={
                        "project_name": os.path.basename(project_dir),
                        "success": True,
                        "file": "jest.config.js",
                        "patch": "config_injection",
                        "reason": "Missing config file generated by tool",
                    },
                    run_id=get_run_id(),
                )
            except Exception as e:
                logger.warning(f"Learner logging failed: {e}")
            with open(jest_config_path, "w", encoding='utf-8') as f:
                f.write(jest_config_content)
            logger.info(f"Successfully wrote file: {jest_config_path}")
        except Exception as e:
            error_msg = f"Error writing default jest.config.js: {e}"
            logger.error(error_msg)
            return error_msg
            
    # Clerk middleware mock content (updated per Grok's suggestion)
    clerk_middleware_mock_content = """module.exports = {
  withClerkMiddleware: (handler) => handler,
  clerkMiddleware: (handler) => handler, // Added per Grok's suggestion
};"""
    clerk_middleware_mock_path = os.path.join(project_dir, '__mocks__', 'clerk-middleware.js')
    os.makedirs(os.path.dirname(clerk_middleware_mock_path), exist_ok=True)
    if not os.path.exists(clerk_middleware_mock_path):
        logger.info(f"Writing clerk middleware mock to '{clerk_middleware_mock_path}'...")
        try:
            try:
                _write_learner_event(
                    event_type="tool_patch_applied",
                    payload={
                        "project_name": os.path.basename(project_dir),
                        "success": True,
                        "file": "clerk-middleware.js",
                        "patch": "config_injection",
                        "reason": "Missing config file generated by tool",
                    },
                    run_id=get_run_id(),
                )
            except Exception as e:
                logger.warning(f"Learner logging failed: {e}")
            with open(clerk_middleware_mock_path, "w", encoding='utf-8') as f:
                f.write(clerk_middleware_mock_content)
            logger.info(f"Successfully wrote file: {clerk_middleware_mock_path}")
        except Exception as e:
            error_msg = f"Error writing clerk middleware mock: {e}"
            logger.error(error_msg)
            return error_msg
    
    total_tests_count = _count_test_files(project_dir)
    if not allow_zero_tests_debug and total_tests_count < min_required_tests:
        message = (
            f"TESTS_INSUFFICIENTS: {total_tests_count} test file(s) detected, "
            f"minimum required is {min_required_tests} for stack '{get_stack_id()}'."
        )
        try:
            _write_learner_event(
                event_type="tests_insufficient",
                payload={
                    "project_name": os.path.basename(project_dir) or "default-project",
                    "success": False,
                    "stack_id": get_stack_id(),
                    "test_files_count": total_tests_count,
                    "min_required_tests": min_required_tests,
                },
                run_id=get_run_id(),
            )
        except Exception as e:
            logger.warning(f"Learner logging failed: {e}")
        logger.error(message)
        return message

    package_json_path = os.path.join(project_dir, 'package.json')
    if os.path.exists(package_json_path):
        project_name = os.path.basename(project_dir) or "default-project"
        sanitized = _sanitize_package_json(package_json_path, project_name)
        if sanitized:
            logger.info("package.json sanitized")
        logger.info(f"package.json found in '{project_dir}'. Installing dev dependencies...")
        lock_path = os.path.join(project_dir, 'package-lock.json')
        # Hard rule: jest@29 + ts-jest@29 + jest-environment-jsdom@29 — versions verrouillées.
        # jest@30 (latest 2026) est INCOMPATIBLE avec ts-jest@29 → cycle d'erreur infini.
        npm_install_fallback = [
            'npm', 'install', '--save-dev', '--legacy-peer-deps',
            'jest@29', '@testing-library/react', '@testing-library/jest-dom',
            'babel-jest', '@babel/preset-env', '@babel/preset-react',
            'ts-jest@29', 'typescript', 'zod', 'node-mocks-http',
            'identity-obj-proxy', 'jest-environment-jsdom@29'
        ]
        npm_command = ['npm', 'ci'] if os.path.exists(lock_path) else npm_install_fallback

        try:
            if npm_command == ['npm', 'ci']:
                logger.info("package-lock.json found. Trying 'npm ci' first.")
            else:
                logger.info("package-lock.json not found. Using 'npm install --save-dev --legacy-peer-deps'.")

            install_result = subprocess.run(
                npm_command,
                capture_output=True,
                text=True,
                check=True,
                cwd=project_dir,
                timeout=SUBPROCESS_TIMEOUT_LONG,
                env=_get_node_env(),
            )
            logger.info(
                _truncate_output(
                    f"npm command completed successfully. STDOUT:\n{install_result.stdout}\nSTDERR:\n{install_result.stderr}"
                )
            )

            # Explicitly check if jest executable is present after npm install
            jest_bin_path = os.path.join(project_dir, 'node_modules', '.bin', 'jest')
            if not os.path.exists(jest_bin_path):
                return _truncate_output(
                    f"Error: Jest executable not found at '{jest_bin_path}' after npm command. Installation might have failed or been incomplete. npm STDOUT:\n{install_result.stdout}\nnpm STDERR:\n{install_result.stderr}"
                )

            # Hard rule: jest-environment-jsdom@29 est requis par jest.config.js injecté
            # (testEnvironment: 'jsdom'). npm ci n'installe que ce qui est dans package.json —
            # si le LLM ne l'a pas inclus, on l'ajoute silencieusement.
            jsdom_path = os.path.join(project_dir, 'node_modules', 'jest-environment-jsdom')
            if not os.path.exists(jsdom_path):
                logger.warning("jest-environment-jsdom absent après install → ajout forcé @29")
                subprocess.run(
                    ['npm', 'install', '--save-dev', '--legacy-peer-deps', 'jest-environment-jsdom@29'],
                    capture_output=True, text=True, check=False,
                    cwd=project_dir, timeout=SUBPROCESS_TIMEOUT_LONG, env=_get_node_env(),
                )

            # Hard rule: @testing-library/jest-dom requis par jest.setup.js injecté
            # (import '@testing-library/jest-dom'). npm ci ne l'installe pas si absent du package.json.
            jest_dom_path = os.path.join(project_dir, 'node_modules', '@testing-library', 'jest-dom')
            if not os.path.exists(jest_dom_path):
                logger.warning("@testing-library/jest-dom absent après install → ajout forcé")
                subprocess.run(
                    ['npm', 'install', '--save-dev', '--legacy-peer-deps', '@testing-library/jest-dom'],
                    capture_output=True, text=True, check=False,
                    cwd=project_dir, timeout=SUBPROCESS_TIMEOUT_LONG, env=_get_node_env(),
                )

            # Hard rule: @testing-library/react requis par les tests de composants générés.
            testing_library_react_path = os.path.join(
                project_dir, 'node_modules', '@testing-library', 'react'
            )
            if not os.path.exists(testing_library_react_path):
                logger.warning("@testing-library/react absent après install → ajout forcé")
                subprocess.run(
                    ['npm', 'install', '--save-dev', '--legacy-peer-deps', '@testing-library/react'],
                    capture_output=True, text=True, check=False,
                    cwd=project_dir, timeout=SUBPROCESS_TIMEOUT_LONG, env=_get_node_env(),
                )

            # Hard rule: node-mocks-http requis par des tests API générés.
            node_mocks_http_path = os.path.join(project_dir, 'node_modules', 'node-mocks-http')
            if not os.path.exists(node_mocks_http_path):
                logger.warning("node-mocks-http absent après install → ajout forcé")
                subprocess.run(
                    ['npm', 'install', '--save-dev', '--legacy-peer-deps', 'node-mocks-http'],
                    capture_output=True, text=True, check=False,
                    cwd=project_dir, timeout=SUBPROCESS_TIMEOUT_LONG, env=_get_node_env(),
                )

        except subprocess.TimeoutExpired:
            return f"npm command timed out in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds."
        except subprocess.CalledProcessError as e:
            stderr_text = (e.stderr or "")
            should_fallback = (
                npm_command == ['npm', 'ci']
                and (
                    "EUSAGE" in stderr_text
                    or "can only install packages when your package.json and package-lock.json" in stderr_text
                    or "Invalid: lock file" in stderr_text
                )
            )
            if should_fallback:
                logger.warning("npm ci failed due to lockfile mismatch. Falling back to npm install --legacy-peer-deps.")
                try:
                    if os.path.exists(lock_path):
                        os.remove(lock_path)
                        try:
                            _write_learner_event(
                                event_type="tool_patch_applied",
                                payload={
                                    "project_name": os.path.basename(project_dir),
                                    "success": True,
                                    "file": "package-lock.json",
                                    "patch": "lockfile_reset",
                                    "reason": "npm ci lockfile mismatch fallback",
                                },
                                run_id=get_run_id(),
                            )
                        except Exception as e:
                            logger.warning(f"Learner logging failed: {e}")
                        logger.info("package-lock.json removed before fallback install.")
                    install_result = subprocess.run(
                        npm_install_fallback,
                        capture_output=True,
                        text=True,
                        check=True,
                        cwd=project_dir,
                        timeout=SUBPROCESS_TIMEOUT_LONG,
                        env=_get_node_env(),
                    )
                    logger.info(
                        _truncate_output(
                            f"npm fallback install completed successfully. STDOUT:\n{install_result.stdout}\nSTDERR:\n{install_result.stderr}"
                        )
                    )
                except subprocess.CalledProcessError as e2:
                    error_message = _truncate_output(
                        f"npm fallback install failed (code {e2.returncode}): {e2.cmd}\nSTDOUT:\n{e2.stdout}\nSTDERR:\n{e2.stderr}"
                    )
                    logger.error(error_message)
                    return error_message
                except Exception as e2:
                    return f"An unexpected error occurred during npm fallback install: {e2}"
            else:
                error_message = _truncate_output(
                    f"npm command failed (code {e.returncode}): {e.cmd}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
                )
                logger.error(error_message)
                return error_message
        except FileNotFoundError:
            return "Error: 'npm' not found during dependency installation. Please ensure Node.js and npm are installed and in the PATH."
        except Exception as e:
            return f"An unexpected error occurred during npm command: {e}"

    logger.info(f"Attempting to run Jest tests in '{project_dir}'...")
    try:
        command = shlex.split(stack_rules.get("test_command", "npx jest --coverage"))
        logger.info(f"Executing Jest command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
            timeout=SUBPROCESS_TIMEOUT_LONG, # Using SUBPROCESS_TIMEOUT_LONG for 120s
            env=_get_node_env(),
        )
        logger.info(
            _truncate_output(
                f"Jest tests command completed. STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        )
        logger.info(f"Tests passed in '{project_dir}'.")
        return _truncate_output(f"Tests passed: {result.stdout}")
    except subprocess.TimeoutExpired:
        cmd_text = " ".join(command) if 'command' in locals() else "npx jest --coverage"
        logger.error(f"Test run timed out for '{cmd_text}' in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds.")
        return f"Test run timed out for '{cmd_text}' in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds."
    except subprocess.CalledProcessError as e:
        error_message = _truncate_output(
            f"Tests failed (code {e.returncode}):\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        )
        logger.error(error_message)
        return error_message
    except FileNotFoundError:
        logger.error("Error: 'npx' not found during test execution. Please ensure Node.js and npm are installed and in the PATH.")
        return "Error: 'npx' not found during test execution. Please ensure Node.js and npm are installed and in the PATH."
    except Exception as e:
        logger.error(f"An unexpected error occurred during tests: {e}")
        return f"An unexpected error occurred during tests: {e}"


class LogToLearnerArgs(BaseModel):
    project_name: str = Field(description="Nom du projet (ex: demo-saas)")
    metric: str = Field(description="Nom de la metrique (ex: build_success)")
    value: str = Field(description="Valeur serialisee de la metrique")


def _write_learner_event(event_type: str, payload: dict, run_id: str = "") -> None:
    log_path = Path("logs/shadow/learner_shadow_log.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        log = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        log = {"total_suggestions": 0, "suggested_standards": []}

    log.setdefault("suggested_standards", [])
    log.setdefault("total_suggestions", 0)

    log["suggested_standards"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "event_type": event_type,
            "payload": payload,
        }
    )
    log["total_suggestions"] += 1

    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


@tool(args_schema=LogToLearnerArgs)
def log_to_learner(project_name: str, metric: str, value: str) -> str:
    """
    Appends a learner shadow metric to logs/shadow/learner_shadow_log.json.
    """
    try:
        parsed_value = json.loads(value) if isinstance(value, str) else value
        if not isinstance(parsed_value, dict):
            parsed_value = {"raw_value": parsed_value}
        success = bool(parsed_value.get("success", False))
        _write_learner_event(
            event_type=metric,
            payload={**parsed_value, "project_name": project_name, "success": success},
            run_id=get_run_id(),
        )
        return f"Learner log updated: {metric} for {project_name}"
    except Exception as e:
        return f"Error updating learner log: {e}"


def validate_blueprint(project_dir: str, stack_id: str | None = None) -> dict:
    """
    Vérifie que les fichiers requis par le blueprint stack sont présents.
    Mode WARNING uniquement (Sprint 3) : ne bloque jamais le build.
    Retourne {"missing_required": [...], "complete": bool}.
    """
    effective_stack_id = stack_id or get_stack_id() or DEFAULT_STACK_ID
    try:
        from agents.stack_config import get_blueprint
        blueprint = get_blueprint(effective_stack_id)
    except Exception:
        blueprint = {}
    required = blueprint.get("required_files", [])
    missing = [f for f in required if not os.path.exists(os.path.join(project_dir, f))]

    critical_files = {
        "app/layout.tsx",
        "middleware.ts",
        "package.json",
        "schema.prisma",
    }
    missing_critical = [f for f in missing if f in critical_files]
    missing_optional = [f for f in missing if f not in critical_files]

    if missing_critical:
        logger.error(f"[blueprint] Fichiers critiques manquants dans '{project_dir}': {missing_critical}")
        raise ValueError(f"Blueprint validation failed (missing critical files): {missing_critical}")
    if missing_optional:
        logger.warning(f"[blueprint] Fichiers requis manquants dans '{project_dir}': {missing_optional}")
    else:
        logger.info(f"[blueprint] Blueprint OK — tous les fichiers requis présents ({project_dir})")

    return {
        "missing_required": missing,
        "missing_critical": missing_critical,
        "missing_optional": missing_optional,
        "complete": len(missing) == 0,
    }
