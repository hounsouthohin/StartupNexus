"""
supervision_manager.py — supervision inline et corrections build.

Extraction des helpers de supervision depuis dev.py pour isoler:
- le routage par fichier
- la supervision per-file
- la supervision build
"""

from __future__ import annotations

import asyncio
import logging

from .architecture_agent import run_architecture_supervisor
from .conformity_agent import run_conformity_supervisor
from .security_agent import run_security_supervisor
from .shared_tools import run_tsc_check, run_eslint_check, run_prisma_validate

logger = logging.getLogger(__name__)


def _match_supervision_routing_inline(
    file_path: str,
    routing: dict[str, list[str]],
) -> list[str]:
    """
    Match glob supervision routing sans dépendre de dev_test_agent.
    """
    from fnmatch import fnmatch

    norm = (file_path or "").replace("\\", "/")
    for pattern, supervisors in (routing or {}).items():
        if fnmatch(norm, pattern):
            return supervisors or []
    return []


async def _supervise_file_inline(
    file_path: str,
    file_content: str,
    context: dict,
    supervisors: list[str],
    conformity_scores: list,
    security_scores: list,
    architecture_scores: list,
    timeout_ms: int = 30000,
    project_dir: str = "",
) -> tuple[str | None, dict]:
    """
    Niveau 1 — Checks déterministes (tsc, prisma validate) : faits, pas opinions.
    Niveau 2 — Superviseurs LLM sémantiques : contexte enrichi avec résultat outils.
    Retourne (message_correction, résultats_normalisés).
    """
    # ── Niveau 1 : Checks déterministes ──────────────────────────────────────
    norm_path = (file_path or "").replace("\\", "/")
    is_ts_file = norm_path.endswith(".ts") or norm_path.endswith(".tsx")
    is_prisma_schema = norm_path == "prisma/schema.prisma"
    det_errors: list[str] = []
    det_context_str = ""

    if project_dir:
        if is_ts_file:
            tsc_result: dict = {"errors": [], "success": True, "skipped": True}
            eslint_result: dict = {"errors": [], "success": True, "skipped": True}
            try:
                tsc_result, eslint_result = await asyncio.gather(
                    run_tsc_check(project_dir),
                    run_eslint_check(project_dir),
                )
            except Exception as _det_exc:
                logger.debug(f"[det_check] checks TS/ESLint non-bloquants sur {norm_path}: {_det_exc}")

            # Filtrer TSC sur le fichier courant
            tsc_file_errors: list[dict] = []
            try:
                if not tsc_result.get("skipped"):
                    tsc_file_errors = [
                        e for e in tsc_result.get("errors", [])
                        if norm_path in (e.get("file", "") or "").replace("\\", "/")
                    ]
            except Exception as _tsc_exc:
                logger.debug(f"[det_check] tsc non-bloquant sur {norm_path}: {_tsc_exc}")

            # Filtrer ESLint sur le fichier courant
            eslint_file_errors: list[dict] = []
            try:
                if not eslint_result.get("skipped"):
                    eslint_file_errors = [
                        e for e in eslint_result.get("errors", [])
                        if norm_path in (e.get("file", "") or "").replace("\\", "/")
                    ]
            except Exception as _eslint_exc:
                logger.debug(f"[det_check] eslint non-bloquant sur {norm_path}: {_eslint_exc}")

            if tsc_file_errors:
                for err in tsc_file_errors[:5]:
                    det_errors.append(
                        f"  [tsc] L{err.get('line', '')}:{err.get('col', '')} "
                        f"{err.get('code', '')} — {err.get('message', '')}"
                    )
            if eslint_file_errors:
                for err in eslint_file_errors[:5]:
                    det_errors.append(
                        f"  [eslint] L{err.get('line', '')}:{err.get('col', '')} "
                        f"{err.get('code', '')} — {err.get('message', '')}"
                    )

            if tsc_file_errors or eslint_file_errors:
                det_context_str = (
                    f"[tsc] {len(tsc_file_errors)} erreur(s), "
                    f"[eslint] {len(eslint_file_errors)} erreur(s)"
                )
            else:
                det_context_str = "[tsc+eslint] pas d'erreur"
        elif is_prisma_schema:
            # prisma validate --schema est incompatible avec Prisma 7.5.0 (url dans prisma.config.ts,
            # pas dans le schema). La validation réelle se fait à npm run build → prisma generate.
            det_context_str = "[prisma validate] skipped (Prisma 7.5 — url in prisma.config.ts)"

    if det_errors:
        tool_name = "tsc/eslint" if is_ts_file else "prisma validate"
        logger.info(
            f"[det_check] {norm_path} — {len(det_errors)} erreur(s) {tool_name} → correction sans LLM"
        )
        return (
            f"ERREUR {tool_name.upper()} sur {file_path} :\n"
            + "\n".join(det_errors)
            + f"\nCorrige ces erreurs dans {file_path} avec write_file() maintenant.",
            {"deterministic": {"status": "needs_fix", "confidence": 1.0, "tool": tool_name}},
        )

    # ── Niveau 2 : Superviseurs LLM ──────────────────────────────────────────
    # Contexte enrichi avec résultat déterministe si disponible
    if det_context_str:
        context = {**context, "det_tool_result": det_context_str}

    tasks = {}
    _det = context.get("det_tool_result", "")
    if "conformity" in supervisors:
        tasks["conformity"] = run_conformity_supervisor(
            file_path=file_path,
            file_content=file_content,
            requirements=context.get("requirements", []),
            plan=context.get("plan", {}),
            files_so_far=context.get("files_so_far", {}),
            project_name=context.get("project_name", ""),
            run_id=context.get("run_id", ""),
            stack_id=context.get("stack_id", "nextjs-clerk-prisma"),
            det_tool_result=_det,
        )
    if "security" in supervisors:
        tasks["security"] = run_security_supervisor(
            file_path=file_path,
            file_content=file_content,
            prisma_schema=context.get("prisma_schema", ""),
            project_name=context.get("project_name", ""),
            run_id=context.get("run_id", ""),
            stack_id=context.get("stack_id", "nextjs-clerk-prisma"),
            det_tool_result=_det,
        )
    if "architecture" in supervisors:
        tasks["architecture"] = run_architecture_supervisor(
            file_path=file_path,
            file_content=file_content,
            prisma_schema=context.get("prisma_schema", ""),
            plan=context.get("plan", {}),
            files_so_far=context.get("files_so_far", {}),
            project_name=context.get("project_name", ""),
            run_id=context.get("run_id", ""),
            stack_id=context.get("stack_id", "nextjs-clerk-prisma"),
            det_tool_result=_det,
        )

    timeout_s = max(0.001, float(timeout_ms) / 1000.0)

    async def _run_one(name: str, coro):
        try:
            result = await asyncio.wait_for(coro, timeout=timeout_s)
            return name, result
        except asyncio.TimeoutError:
            return name, {"status": "skipped", "confidence": 0.0, "note": "timeout"}
        except Exception:
            return name, {"status": "skipped", "confidence": 0.0}

    corrections: list[str] = []
    results: dict = {}
    gathered = await asyncio.gather(
        *[_run_one(name, coro) for name, coro in tasks.items()],
        return_exceptions=False,
    )
    for name, result in gathered:
        results[name] = result
        conf = float(result.get("confidence", 0.0) or 0.0)
        if name == "conformity":
            conformity_scores.append(conf)
        elif name == "security":
            security_scores.append(conf)
        elif name == "architecture":
            architecture_scores.append(conf)

        status = str(result.get("status", "") or "").lower()
        if status == "needs_fix" and conf > 0.7:
            fix = result.get("fix_instruction", {}) or {}
            if fix.get("problem") and fix.get("fix"):
                corrections.append(
                    f"[SUPERVISEUR {name.upper()}] {fix['problem']}\n"
                    f"Fix obligatoire : {fix['fix']}"
                )

    if corrections:
        return (
            f"CORRECTIONS SUPERVISEURS OBLIGATOIRES sur {file_path} :\n"
            + "\n\n".join(corrections)
            + "\nApplique ces corrections avec write_file() maintenant.",
            results,
        )
    return None, results


async def run_pre_build_deterministic_checks(project_dir: str) -> tuple[bool, str]:
    """
    Gate pré-build déterministe — appelé AVANT PreBuildValidator.check() et run_build().

    Exécute tsc --noEmit sur le projet entier + prisma validate.
    Retourne (blocked: bool, message: str).
    - blocked=True → injecter le message comme correction et ne pas lancer run_build()
    - blocked=False → libre de lancer run_build()

    Non-bloquant si les outils sont absents (skipped=True → blocked=False).
    """
    if not project_dir:
        return False, ""

    blocking_messages: list[str] = []

    # ── tsc --noEmit sur le projet complet ──
    try:
        tsc_result = await run_tsc_check(project_dir)
        if not tsc_result.get("skipped"):
            errors = tsc_result.get("errors", [])
            if errors:
                # Grouper par fichier pour un message lisible
                by_file: dict[str, list] = {}
                for err in errors:
                    f = (err.get("file") or "?").replace("\\", "/")
                    by_file.setdefault(f, []).append(err)
                lines = [f"[tsc] {len(errors)} erreur(s) TypeScript avant build :"]
                for fname, errs in list(by_file.items())[:5]:  # max 5 fichiers
                    lines.append(f"  {fname}:")
                    for e in errs[:3]:
                        lines.append(
                            f"    L{e.get('line','')}:{e.get('col','')} "
                            f"{e.get('code','')} — {e.get('message','')}"
                        )
                blocking_messages.append("\n".join(lines))
                logger.info(f"[pre_build_det] tsc: {len(errors)} erreur(s) dans {len(by_file)} fichier(s)")
            else:
                logger.debug("[pre_build_det] tsc: pas d'erreur")
    except Exception as _tsc_exc:
        logger.debug(f"[pre_build_det] tsc non-bloquant: {_tsc_exc}")

    # ── prisma validate ──
    try:
        prisma_result = await run_prisma_validate(project_dir)
        if not prisma_result.get("skipped") and not prisma_result.get("valid", True):
            errs = prisma_result.get("errors", [])
            lines = ["[prisma validate] Schema invalide avant build :"]
            for e in errs[:3]:
                lines.append(f"  {e}")
            blocking_messages.append("\n".join(lines))
            logger.info(f"[pre_build_det] prisma validate: schema invalide")
    except Exception as _prisma_exc:
        logger.debug(f"[pre_build_det] prisma validate non-bloquant: {_prisma_exc}")

    if blocking_messages:
        full_msg = (
            "ERREURS DÉTERMINISTES PRÉ-BUILD — Corrige avant run_build() :\n\n"
            + "\n\n".join(blocking_messages)
            + "\n\nCorrige les fichiers concernés avec write_file() puis rappelle run_build()."
        )
        return True, full_msg

    return False, ""

