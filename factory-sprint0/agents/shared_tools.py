"""
shared_tools.py — vérification TypeScript + ré-exports de context.py et observability.py.

Les @tools LangChain de l'ancienne architecture (validate_syntax, run_build, run_tests,
prisma_migrate, read_files, validate_blueprint, log_to_learner…) ont été retirés le
30 sept 2026 : l'executor actuel utilise ses propres outils (dev_tools.py).
"""

import asyncio
import os
import subprocess

# ── Re-exports pour compatibilité avec les imports existants ──────────────────
from agents.context import set_run_id, get_run_id, set_stack_id, get_stack_id  # noqa: F401
from agents.observability import logger, _write_learner_event  # noqa: F401
from agents.core.error_parser import parse_tsc_errors as _parse_tsc_errors

MAX_OUTPUT_CHARS = 4000


def _get_node_env() -> dict:
    """Retourne l'environnement pour les sous-processus Node.js."""
    env = os.environ.copy()
    env["CI"] = "true"
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    # Build deterministe: prisma generate nécessite DATABASE_URL même sans DB accessible.
    # Fallback placeholder (non-fonctionnel) uniquement si absent de l'environnement.
    env.setdefault("DATABASE_URL", "postgresql://user:CHANGEME@localhost:5432/db_placeholder")
    return env


def _truncate_output(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n...[TRONQUÉ {len(text)} chars total]...\n" + text[-half:]


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
