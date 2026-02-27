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
from agents.stack_config import _DEFAULT_STACK_ID

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
_run_id_ctx: ContextVar[str] = ContextVar("run_id", default="")
_stack_id_ctx: ContextVar[str] = ContextVar("stack_id", default=_DEFAULT_STACK_ID)


def set_run_id(run_id: str) -> None:
    _run_id_ctx.set(run_id or "")


def get_run_id() -> str:
    return _run_id_ctx.get()


def set_stack_id(stack_id: str) -> None:
    _stack_id_ctx.set(stack_id or _DEFAULT_STACK_ID)


def get_stack_id() -> str:
    return _stack_id_ctx.get() or _DEFAULT_STACK_ID


def _get_runtime_stack_rules(stack_id: str | None = None) -> dict:
    """
    Retourne les règles stack runtime depuis Stack-as-Config, avec fallback local.
    Cela évite les divergences quand stack_id change pendant le run.
    """
    effective_stack_id = stack_id or get_stack_id() or _DEFAULT_STACK_ID
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
        "version_pins":             stack_config.get("version_pins") or {},
        "dev_packages":             stack_config.get("dev_packages") or {},
        "peer_dependency_minimums": stack_config.get("peer_dependency_minimums") or {},
        "clerk_package_fixes":      remaps.get("package_fixes") or {},
        "test_fixes":               remaps.get("test_fixes") or {},
        "source_fixes":             remaps.get("source_fixes") or {},
        "router_fixes":             remaps.get("router_fixes") or {},
        "test_command":             commands.get("test") or "npx jest --coverage",
        "testing":                  testing,
        "framework":                stack_config.get("framework", "nextjs"),
    }


def _get_node_env() -> dict:
    """
    Returns os.environ with explicit Node.js binary paths prepended to PATH.
    Fixes 'npm not found' errors when subprocess.run doesn't inherit the shell PATH.
    """
    env = os.environ.copy()
    env["PATH"] = "/usr/local/bin:/usr/bin:/bin:" + env.get("PATH", "")
    return env



# --- Tool Definitions ---

MAX_TOOL_OUTPUT_CHARS = 1800
RAG_CACHE_MAX_SIZE = 50
_rag_cache: dict[str, str] = {}




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








def _load_stack_template(template_name: str, stack_id: str | None = None) -> str:
    """
    Charge un template stack depuis templates_folder + template_files mapping.
    Lève StackConfigError si le mapping ou le fichier est manquant.
    """
    from agents.stack_config import StackConfigError, load_stack_config

    effective_stack_id = stack_id or get_stack_id() or _DEFAULT_STACK_ID
    stack_cfg = load_stack_config(effective_stack_id) or {}
    templates_folder = stack_cfg.get("templates_folder")
    if not templates_folder:
        raise StackConfigError(
            f"[stack_config] templates_folder manquant pour stack '{effective_stack_id}'"
        )
    template_files = stack_cfg.get("template_files", {})
    if not isinstance(template_files, dict):
        raise StackConfigError(
            f"[stack_config] template_files invalide pour stack '{effective_stack_id}'"
        )
    filename = template_files.get(template_name)
    if not filename:
        raise StackConfigError(
            f"[stack_config] template '{template_name}' non mappé pour stack '{effective_stack_id}'"
        )

    project_root = Path(__file__).parent.parent
    template_path = project_root / templates_folder / filename
    if not template_path.exists():
        raise StackConfigError(
            f"[stack_config] fichier template absent: {template_path}"
        )
    return template_path.read_text(encoding="utf-8")




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
        if os.path.basename(path) == "package.json":
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                return f"Error writing file '{path}': package.json invalide généré : {e}"
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
        stack_id = get_stack_id()
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
                        with open(safe_path, "r", encoding="utf-8") as tmp_f:
                            content_to_write = tmp_f.read()
                    except Exception as e:
                        logger.warning(f"Pré-écriture package.json ignorée: {e}")

                with open(safe_path, "w", encoding='utf-8') as f:
                    f.write(content_to_write)
                logger.info(f"Successfully wrote file: {path}")
            except Exception as e:
                error_msg = f"Error writing file '{path}' at the start of run_tests: {e}"
                logger.error(error_msg)
                return error_msg
    
    # Ensure critical config files for tests using stack-driven templates.
    test_command = str(stack_rules.get("test_command", "npx jest --coverage") or "").lower()
    if "jest" in test_command:
        # jest.config.js from stack template when available
        jest_config_path = os.path.join(project_dir, "jest.config.js")
        if not os.path.exists(jest_config_path):
            try:
                template = _load_stack_template("jest.config.js")
                with open(jest_config_path, "w", encoding="utf-8") as f:
                    f.write(template.rstrip() + "\n")
                logger.info(f"Successfully wrote file: {jest_config_path}")
            except Exception as e:
                logger.warning(f"Impossible de générer jest.config.js depuis template stack: {e}")
        # Generic jest setup file for jest-dom matchers.
        jest_setup_path = os.path.join(project_dir, "jest.setup.js")
        if not os.path.exists(jest_setup_path):
            try:
                with open(jest_setup_path, "w", encoding="utf-8") as f:
                    f.write("import '@testing-library/jest-dom';\n")
                logger.info(f"Successfully wrote file: {jest_setup_path}")
            except Exception as e:
                error_msg = f"Error writing default jest.setup.js: {e}"
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
        logger.info(f"package.json found in '{project_dir}'. Installing dev dependencies...")
        lock_path = os.path.join(project_dir, 'package-lock.json')
        dev_packages = stack_rules.get("dev_packages", {})
        fallback_pkgs = []
        if isinstance(dev_packages, dict):
            for pkg, version in dev_packages.items():
                if isinstance(version, str) and version.strip():
                    fallback_pkgs.append(f"{pkg}@{version}")
                else:
                    fallback_pkgs.append(str(pkg))
        npm_install_fallback = ['npm', 'install', '--save-dev', '--legacy-peer-deps']
        npm_install_fallback.extend(fallback_pkgs)
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
    effective_stack_id = stack_id or get_stack_id() or _DEFAULT_STACK_ID
    try:
        from agents.stack_config import get_blueprint
        blueprint = get_blueprint(effective_stack_id)
    except Exception:
        blueprint = {}
    required = blueprint.get("required_files", [])
    missing = [f for f in required if not os.path.exists(os.path.join(project_dir, f))]

    critical_cfg = blueprint.get("critical_files", required)
    if not isinstance(critical_cfg, list) or not critical_cfg:
        critical_cfg = required
    critical_files = set(str(f) for f in critical_cfg)
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
