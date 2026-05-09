"""
shared_tools.py — Tous les @tools LangChain du factory worker.

Re-exporte également les helpers de context.py et observability.py
pour compatibilité avec les imports existants dans tout le pipeline.
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Optional

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
try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    class BaseModel:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Field(default=None, **kwargs):  # type: ignore[override]
        return default

from config.factory_config import (
    SUBPROCESS_TIMEOUT_SHORT,
    SUBPROCESS_TIMEOUT_MEDIUM,
    SUBPROCESS_TIMEOUT_LONG,
)

# ── Re-exports pour compatibilité avec tous les imports existants ──────────────
from agents.context import set_run_id, get_run_id, set_stack_id, get_stack_id  # noqa: F401
from agents.observability import logger, _append_rag_usage_event, _write_learner_event  # noqa: F401
from agents.rag_client import rag_search  # noqa: F401
from agents.core.error_parser import parse_tsc_errors as _parse_tsc_errors, parse_eslint_errors_json as _parse_eslint_errors_json  # noqa: F401


def _get_node_env() -> dict:
    """Retourne l'environnement pour les sous-processus Node.js."""
    env = os.environ.copy()
    env["CI"] = "true"
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    # Build deterministe: prisma generate nécessite DATABASE_URL même sans DB accessible.
    # Fallback placeholder (non-fonctionnel) uniquement si absent de l'environnement.
    env.setdefault("DATABASE_URL", "postgresql://user:CHANGEME@localhost:5432/db_placeholder")
    return env


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


def _parse_prisma_blocks(text: str) -> dict:
    """
    Parse un texte de schema Prisma et retourne {NomBloc: texte_complet_du_bloc}
    pour les blocs `model` et `enum`. Utilisé par scaffold_extends pour accumuler
    les modèles entre plusieurs writes successifs du LLM.
    """
    blocks: dict = {}
    lines = (text or "").splitlines(keepends=True)
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if (stripped.startswith("model ") or stripped.startswith("enum ")) and "{" in stripped:
            parts = stripped.split()
            name = parts[1] if len(parts) > 1 else ""
            block: list = [lines[i]]
            depth = lines[i].count("{") - lines[i].count("}")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
            if name:
                blocks[name] = "".join(block).rstrip()
        else:
            i += 1
    return blocks


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
# Helpers de normalisation déterministe (write_file)
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


_CODE_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".scss", ".prisma")


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
# Critique phase helpers (Sprint 4.6)
# ─────────────────────────────────────────────────────────────────────────────


async def run_tsc_check(project_dir: str) -> dict:
    """Lance tsc --noEmit. Retourne skipped=True (success=None) si outil absent."""
    try:
        if not project_dir:
            return {"errors": [], "success": None, "skipped": True, "skip_reason": "no_project_dir"}
        tsconfig_path = os.path.join(project_dir, "tsconfig.json")
        if not os.path.exists(tsconfig_path):
            return {"errors": [], "success": None, "skipped": True, "skip_reason": "no_tsconfig"}

        def _run() -> subprocess.CompletedProcess:
            return subprocess.run(
                ["npx", "tsc", "--noEmit", "--pretty", "false"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env=_get_node_env(),
            )

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _run)
        output = "\n".join([result.stdout or "", result.stderr or ""]).strip()
        errors = _parse_tsc_errors(output)
        if result.returncode != 0 and not errors:
            errors = [
                {
                    "file": "",
                    "line": 0,
                    "col": 0,
                    "code": "TS_UNKNOWN",
                    "message": _truncate_output(output),
                }
            ]
        return {"errors": errors, "success": result.returncode == 0, "skipped": False}
    except FileNotFoundError:
        return {"errors": [], "success": None, "skipped": True, "skip_reason": "tsc_not_found"}
    except subprocess.TimeoutExpired:
        return {"errors": [], "success": None, "skipped": True, "skip_reason": "timeout"}
    except Exception as e:
        logger.warning(f"[run_tsc_check] non-bloquant: {e}")
        return {"errors": [], "success": None, "skipped": True, "skip_reason": str(e)[:80]}


async def run_eslint_check(project_dir: str) -> dict:
    """Lance eslint en format JSON. Retourne skipped=True (success=None) si outil absent."""
    try:
        if not project_dir:
            return {"errors": [], "success": None, "skipped": True, "skip_reason": "no_project_dir"}
        pkg_path = os.path.join(project_dir, "package.json")
        if not os.path.exists(pkg_path):
            return {"errors": [], "success": None, "skipped": True, "skip_reason": "no_package_json"}

        def _run() -> subprocess.CompletedProcess:
            return subprocess.run(
                ["npx", "eslint", ".", "--ext", ".ts,.tsx", "--format", "json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60,
                env=_get_node_env(),
            )

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _run)
        output = (result.stdout or "").strip()
        errors = _parse_eslint_errors_json(output)
        if result.returncode != 0 and not errors:
            stderr = (result.stderr or "").strip()
            if stderr:
                errors = [
                    {
                        "file": "",
                        "line": 0,
                        "col": 0,
                        "code": "ESLINT_UNKNOWN",
                        "message": _truncate_output(stderr),
                    }
                ]
        return {"errors": errors, "success": len(errors) == 0, "skipped": False}
    except FileNotFoundError:
        return {"errors": [], "success": None, "skipped": True, "skip_reason": "eslint_not_found"}
    except subprocess.TimeoutExpired:
        return {"errors": [], "success": None, "skipped": True, "skip_reason": "timeout"}
    except Exception as e:
        logger.warning(f"[run_eslint_check] non-bloquant: {e}")
        return {"errors": [], "success": None, "skipped": True, "skip_reason": str(e)[:80]}


async def run_prisma_validate(project_dir: str) -> dict:
    """Lance npx prisma validate. Non bloquant si schema absent."""
    try:
        if not project_dir:
            return {"valid": True, "errors": [], "skipped": True}
        schema_rel = os.path.join("prisma", "schema.prisma")
        schema_path = os.path.join(project_dir, schema_rel)
        if not os.path.exists(schema_path):
            return {"valid": True, "errors": [], "skipped": True}

        def _run() -> subprocess.CompletedProcess:
            return subprocess.run(
                ["npx", "prisma", "validate", "--schema", schema_rel],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=30,
                env=_get_node_env(),
            )

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _run)
        stderr = (result.stderr or "").strip()
        if result.returncode == 0:
            return {"valid": True, "errors": []}
        msg = _truncate_output(stderr or (result.stdout or ""))
        return {"valid": False, "errors": [msg] if msg else ["prisma validate failed"]}
    except FileNotFoundError:
        return {"valid": None, "errors": [], "skipped": True, "skip_reason": "prisma_not_found"}
    except subprocess.TimeoutExpired:
        return {"valid": None, "errors": [], "skipped": True, "skip_reason": "timeout"}
    except Exception as e:
        logger.warning(f"[run_prisma_validate] non-bloquant: {e}")
        return {"valid": None, "errors": [], "skipped": True, "skip_reason": str(e)[:80]}


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
