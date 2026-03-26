"""
dev_loop.py — helpers de boucle dev et état d'itération.
"""

from __future__ import annotations

import ast
import asyncio
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .dev_compat import HumanMessage, SystemMessage, ToolMessage
from .dev_path_utils import allowed_paths_for_blocker, find_project_dir, path_is_allowed_for_objective
from .dev_reflection import ProgressSummary, build_iteration_brief
from .requirements_engine import gate_check as _engine_gate_check
from .shared_tools import _write_learner_event, run_build
from .stack_config import get_root_file
from .supervision_manager import (
    _match_supervision_routing_inline,
    _supervise_file_inline,
    run_pre_build_deterministic_checks,
)

try:
    from .build_supervisor_agent import run_build_supervisor
except ModuleNotFoundError:
    async def run_build_supervisor(*args, **kwargs):  # type: ignore[override]
        return {"status": "skipped"}


logger = logging.getLogger(__name__)


@dataclass
class DevLoopState:
    iteration: int = 0
    stagnant_iterations: int = 0
    build_attempts: int = 0
    build_attempted: bool = False
    build_success: bool = False
    last_build_succeeded: bool = False
    last_build_error: str = ""
    last_build_error_full: str = ""
    last_test_error: str = ""
    last_test_error_full: str = ""
    last_failed_command: str = ""
    final_message: str = ""
    files: dict = field(default_factory=dict)
    final_gate_source: str = ""
    final_blocking_guard_id: str = ""
    final_gate_message: str = ""
    final_missing_required_files: list[str] = field(default_factory=list)
    sup_files_reviewed: int = 0
    sup_corrections_count: int = 0
    build_corrections_count: int = 0
    conformity_scores: list[float] = field(default_factory=list)
    security_scores: list[float] = field(default_factory=list)
    architecture_scores: list[float] = field(default_factory=list)


async def _run_build_supervisor_inline(
    build_stderr: str,
    files: dict,
    run_id: str,
    stack_id: str,
) -> str | None:
    result = await run_build_supervisor(
        build_stderr=build_stderr,
        combined_files=files,
        run_id=run_id or "",
        stack_id=stack_id or "nextjs-clerk-prisma",
    )
    if str(result.get("status", "")).lower() == "needs_fix":
        fix = result.get("fix_instruction", {}) or {}
        if fix.get("problem") and fix.get("fix"):
            return (
                f"[BUILD SUPERVISOR] Erreur identifiée dans {fix.get('file', '?')}:\n"
                f"{fix['problem']}\n"
                f"Fix minimal : {fix['fix']}\n"
                "Applique ce fix avec write_file() puis rappelle run_build()."
            )
    return None


def run_dev_loop(
    llm,
    runner,
    messages,
    tools_phase1,
    tools_phase2,
    tool_map,
    files,
    run_state_computer,
    supervision_loop,
    pre_build_validator,
    stack_cfg,
    *,
    max_iterations,
    phase1_limit,
    max_build_attempts,
    project_name,
    run_id,
    stack_id,
    effective_stack_id,
    plan,
    requirements,
    scaffold_extends_paths,
    packages,
    supervision_routing,
    supervision_batch_size,
    supervisor_timeout_ms,
    workdir,
    required_files,
    templated_names,
) -> DevLoopState:
    _final_gate_source = ""
    _final_blocking_guard_id = ""
    _final_gate_message = ""
    _final_missing_required_files: list[str] = []
    build_attempts = 0
    build_attempted = False
    build_success = False
    _sup_files_reviewed = 0
    _sup_corrections_count = 0
    _conformity_scores: list[float] = []
    _security_scores: list[float] = []
    _architecture_scores: list[float] = []
    _build_corrections_count = 0
    last_build_succeeded = False
    last_build_error = ""
    last_build_error_full = ""
    last_test_error = ""
    last_test_error_full = ""
    last_failed_command = ""
    final_message = ""

    def _extract_stderr(output: str) -> str:
        if not output:
            return ""
        marker = "STDERR:\n"
        if marker in output:
            return output.split(marker, 1)[1].strip()
        return ""

    def _extract_failed_command(output: str) -> str:
        match = re.search(r"Command failed \(code \d+\):\s*(\[[^\]]+\])", output)
        if not match:
            return ""
        raw_cmd = match.group(1)
        try:
            parsed = ast.literal_eval(raw_cmd)
            if isinstance(parsed, list):
                return " ".join(str(x) for x in parsed)
        except Exception:
            pass
        return raw_cmd

    _progress = ProgressSummary()
    stagnant_iterations = 0
    key_files = required_files or ["package.json"]

    _SM_GEN = "GEN"
    _SM_STRUCT_GATES = "STRUCT_GATES"
    _SM_REQ_GATES = "REQ_GATES"
    _SM_BUILD = "BUILD"
    _SM_FINAL = "FINAL"
    _state = _SM_GEN
    logger.info(f"[STATE] initial → {_state}")

    _token_budgets = stack_cfg.get("token_budgets", {})
    _PHASE1_MAX_CHARS = int(_token_budgets.get("phase1_tokens", 6000) * 4)
    _PHASE2_MAX_CHARS = int(_token_budgets.get("phase2_tokens", 14000) * 4)
    logger.info(f"[STATE] token budgets — phase1={_PHASE1_MAX_CHARS} chars, phase2={_PHASE2_MAX_CHARS} chars")

    def _append_aggregated_gate_warnings(msgs: list[str]) -> None:
        if not msgs:
            return
        unique_msgs = list(dict.fromkeys([m.strip() for m in msgs if str(m).strip()]))
        if not unique_msgs:
            return
        preview = unique_msgs[:3]
        more = len(unique_msgs) - len(preview)
        body = "\n\n".join(preview)
        if more > 0:
            body += f"\n\n... {more} warning(s) supplémentaire(s) non affiché(s) dans ce tour."
        messages.append(
            HumanMessage(
                content=(
                    "[PREBUILD WARNINGS AGGREGATED]\n"
                    "Warnings non bloquants détectés (agrégés, une seule notification par itération):\n\n"
                    f"{body}"
                )
            )
        )

    iteration = 0
    for iteration in range(1, max_iterations + 1):
        current_phase = 1 if iteration <= phase1_limit else 2
        current_tools = tools_phase1 if current_phase == 1 else tools_phase2
        logger.info(
            f"[DEV AGENT v3.2] Itération {iteration}/{max_iterations} | "
            f"Phase {current_phase} | State {_state} | Build attempts: {build_attempts}"
        )

        if len(messages) > 28:
            logger.info("Historique long détecté — conservation intégrale, sélection contextuelle via _main_context.")

        _ctx_budget = _PHASE1_MAX_CHARS if _state == _SM_GEN else _PHASE2_MAX_CHARS
        main_messages = runner._main_context(messages, max_chars=_ctx_budget)
        run_state = run_state_computer.compute(files, build_attempts, last_build_error)
        run_state["iterations_left"] = max(0, max_iterations - iteration + 1)
        _progress.update(run_state)
        main_messages.append(HumanMessage(content=build_iteration_brief(run_state, _progress, stack_cfg)))
        _iter_tools = current_tools
        if run_state.get("active_blocker") != "ready_for_build":
            _iter_tools = [t for t in current_tools if getattr(t, "name", "") != "run_build"]
        response = llm.bind_tools(_iter_tools).invoke(main_messages)
        messages.append(response)

        tool_messages = []
        raw_tool_outputs = []
        iter_gate_warnings: list[str] = []
        successful_write_paths: set[str] = set()
        wrote_file_this_iter = False
        _wrote_pending_file_this_iter = False
        called_build_this_iter = False
        build_failed_this_iter = False
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_to_call = tool_map.get(tool_name)
                if tool_to_call:
                    try:
                        call_args = tool_call["args"]
                        _path = str(call_args.get("path", ""))
                        if tool_name == "write_file":
                            _allowed = allowed_paths_for_blocker(run_state, scaffold_extends_paths)
                            if not path_is_allowed_for_objective(
                                _path, _allowed, run_state.get("active_blocker", ""), scaffold_extends_paths
                            ):
                                logger.info(
                                    "[write_focus_block] blocker=%s path=%s allowed=%s",
                                    run_state.get("active_blocker", ""),
                                    _path,
                                    _allowed,
                                )
                                _allowed_msg = ", ".join(_allowed) if _allowed else "aucune restriction"
                                tool_messages.append(
                                    ToolMessage(
                                        content=(
                                            "WRITE_FILE BLOQUÉ (focus actif)\n"
                                            f"Objectif courant: {run_state.get('active_blocker', 'N/A')}\n"
                                            f"Chemin proposé: {_path}\n"
                                            f"Chemins autorisés: {_allowed_msg}\n"
                                            "Corrige d'abord la priorité active."
                                        ),
                                        tool_call_id=tool_call["id"],
                                    )
                                )
                                continue
                        _tp_norm = _path.lstrip("./").replace("\\", "/")
                        if _tp_norm in templated_names and _tp_norm not in scaffold_extends_paths:
                            logger.info(f"[template_guard] write ignoré pour template: {_path}")
                            tool_messages.append(
                                ToolMessage(
                                    content=f"[OK] '{_path}' déjà sur le disque (template factory). Passe au fichier suivant.",
                                    tool_call_id=tool_call["id"],
                                )
                            )
                            continue
                        if tool_name == "run_build":
                            computed_dir = find_project_dir(files, effective_stack_id)
                            if computed_dir != "." and call_args.get("project_dir", ".") == ".":
                                call_args = {**call_args, "project_dir": computed_dir}
                                logger.info(f"[run_build] project_dir corrigé: '.' → '{computed_dir}'")
                            _prev_state = _state
                            _state = _SM_STRUCT_GATES
                            logger.info(f"[STATE] {_prev_state} → {_state}")
                            _gate_blocked, _gate_msg, _, _gate_warns = pre_build_validator.check(files)
                            iter_gate_warnings.extend(_gate_warns)
                            if not _gate_blocked:
                                try:
                                    with ThreadPoolExecutor(max_workers=1) as _ex:
                                        _det_blocked, _det_msg = _ex.submit(
                                            asyncio.run,
                                            run_pre_build_deterministic_checks(workdir),
                                        ).result()
                                except Exception as _det_exc:
                                    logger.debug(f"[pre_build_det] non-bloquant: {_det_exc}")
                                    _det_blocked, _det_msg = False, ""
                                if _det_blocked:
                                    _gate_blocked = True
                                    _gate_msg = _det_msg
                            if not _gate_blocked:
                                _prev_state = _state
                                _state = _SM_REQ_GATES
                                logger.info(f"[STATE] {_prev_state} → {_state}")
                                _gate_blocked, _gate_msg = _engine_gate_check(requirements or [], files)
                            if _gate_blocked:
                                tool_messages.append(ToolMessage(content=_gate_msg, tool_call_id=tool_call["id"]))
                                logger.warning("[PreBuildGate] BUILD BLOQUÉ (tool_call path)")
                                called_build_this_iter = False
                                continue
                        logger.info(f"Exécution tool: {tool_name}")
                        if tool_name == "run_build":
                            _prev_state = _state
                            _state = _SM_BUILD
                            logger.info(f"[STATE] {_prev_state} → {_state}")
                        output = tool_to_call.invoke(call_args)
                        raw_output = str(output)
                        raw_tool_outputs.append(raw_output)
                        if tool_name == "write_file":
                            _wp = str(call_args.get("path", "")).replace("\\", "/").strip()
                            if _wp and raw_output.startswith("OK:"):
                                successful_write_paths.add(_wp)

                        if tool_name == "run_build":
                            build_attempted = True
                            called_build_this_iter = True
                            if "Build successful" in raw_output:
                                last_build_succeeded = True
                                build_success = True
                                build_attempts = 0
                                last_build_error = ""
                                last_build_error_full = ""
                                last_failed_command = ""
                            else:
                                build_failed_this_iter = True
                                extracted_stderr = _extract_stderr(raw_output)
                                last_build_error_full = extracted_stderr if extracted_stderr else raw_output
                                last_build_error = last_build_error_full[:2000]
                                failed_cmd = _extract_failed_command(raw_output)
                                if failed_cmd:
                                    last_failed_command = failed_cmd

                        if tool_name == "run_tests":
                            if "Tests passed" in raw_output:
                                last_test_error = ""
                                last_test_error_full = ""
                            else:
                                extracted_stderr = _extract_stderr(raw_output)
                                last_test_error_full = extracted_stderr if extracted_stderr else raw_output
                                last_test_error = last_test_error_full[:2000]

                        shrunk_output = runner._shrink_tool_output(tool_name, raw_output)
                        tool_messages.append(ToolMessage(content=shrunk_output, tool_call_id=tool_call["id"]))
                    except Exception as e:
                        error_text = f"ERREUR {tool_name}: {e}"
                        raw_tool_outputs.append(error_text)
                        if tool_name == "run_build":
                            build_attempted = True
                            called_build_this_iter = True
                            build_failed_this_iter = True
                            last_build_error = error_text[:2000]
                            last_build_error_full = error_text
                            last_failed_command = "run_build"
                        if tool_name == "run_tests":
                            last_test_error = error_text[:2000]
                            last_test_error_full = error_text
                        tool_messages.append(ToolMessage(content=error_text, tool_call_id=tool_call["id"]))
                else:
                    if tool_name == "run_build" and current_phase == 1:
                        tool_messages.append(
                            ToolMessage(
                                content="Génération non terminée, continue d'écrire les fichiers",
                                tool_call_id=tool_call["id"],
                            )
                        )
                    else:
                        tool_messages.append(ToolMessage(content=f"Tool {tool_name} inconnu", tool_call_id=tool_call["id"]))

            messages.extend(tool_messages)

            _files_to_supervise: list[tuple[str, str]] = []
            for tc in response.tool_calls:
                if tc["name"] == "write_file":
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None:
                        _path_norm = str(path).replace("\\", "/").strip()
                        if _path_norm not in successful_write_paths:
                            logger.info(f"Write ignoré (non confirmé sur disque): {_path_norm}")
                            continue
                        _prev_content = files.get(path, "")
                        try:
                            disk_path = os.path.normpath(os.path.join(workdir, path))
                            with open(disk_path, "r", encoding="utf-8") as _df:
                                files[path] = _df.read()
                        except Exception:
                            files[path] = content
                        file_content_on_disk = files.get(path, "")
                        _is_noop_write = (
                            bool(_prev_content)
                            and _prev_content.rstrip() == file_content_on_disk.rstrip()
                        )
                        if _is_noop_write:
                            logger.info(f"[noop_write] {_path_norm} : contenu inchangé — supervision ignorée")
                        else:
                            wrote_file_this_iter = True
                            logger.info(f"Fichier généré : {path}")
                            supervision_loop.reset_file(_path_norm)
                            if file_content_on_disk:
                                if _path_norm in supervision_loop.pending_paths():
                                    logger.info(f"[supervision_loop] {_path_norm} réécrit après correction superviseur")
                                    _wrote_pending_file_this_iter = True
                                _files_to_supervise.append((_path_norm, file_content_on_disk))

            if _files_to_supervise:
                for _batch_start in range(0, len(_files_to_supervise), supervision_batch_size):
                    _batch = _files_to_supervise[_batch_start:_batch_start + supervision_batch_size]
                    _batch_t0 = time.perf_counter()
                    for _path_norm, file_content_on_disk in _batch:
                        supervisors_to_call = _match_supervision_routing_inline(_path_norm, supervision_routing)
                        if not supervisors_to_call:
                            continue

                        _is_reverification = supervision_loop.needs_reverification(_path_norm)
                        if _is_reverification:
                            logger.info(f"[supervision_loop] Re-vérification de {_path_norm} après correction")

                        _sup_files_reviewed += 1
                        _sup_context = {
                            "requirements": requirements or [],
                            "plan": plan or {},
                            "files_so_far": files,
                            "prisma_schema": files.get("prisma/schema.prisma", ""),
                            "project_name": project_name or "",
                            "run_id": run_id or "",
                            "stack_id": stack_id or "nextjs-clerk-prisma",
                        }
                        try:
                            with ThreadPoolExecutor(max_workers=1) as _ex:
                                _sup_result = _ex.submit(
                                    asyncio.run,
                                    _supervise_file_inline(
                                        _path_norm,
                                        file_content_on_disk,
                                        _sup_context,
                                        supervisors_to_call,
                                        _conformity_scores,
                                        _security_scores,
                                        _architecture_scores,
                                        timeout_ms=supervisor_timeout_ms,
                                        project_dir=workdir,
                                    ),
                                ).result()
                            _sup_msg, _sup_raw_results = _sup_result

                            if _sup_msg:
                                should_inject = supervision_loop.on_supervisor_needs_fix(_path_norm)
                                if should_inject:
                                    _sup_corrections_count += 1
                                    runner.inject(_sup_msg)
                                    logger.info(
                                        f"[supervision_loop] Correction injectée pour {_path_norm} "
                                        f"(tentatives restantes: {supervision_loop._pending.get(_path_norm, 0)})"
                                    )
                                else:
                                    logger.info(f"[supervision_loop] {_path_norm}: max tentatives atteintes, correction ignorée")
                            else:
                                supervision_loop.on_supervisor_ok(_path_norm)
                                if _is_reverification:
                                    logger.info(f"[supervision_loop] {_path_norm}: re-vérification OK — validé")

                            try:
                                _write_learner_event(
                                    event_type="supervisor_file_reviewed",
                                    payload={
                                        "file_path": _path_norm,
                                        "supervisors": supervisors_to_call,
                                        "is_reverification": _is_reverification,
                                        "results": {
                                            k: {
                                                "status": v.get("status"),
                                                "confidence": float(v.get("confidence", 0.0) or 0.0),
                                                "fix_applied": bool(
                                                    str(v.get("status", "")).lower() == "needs_fix"
                                                    and float(v.get("confidence", 0.0) or 0.0) > 0.7
                                                ),
                                            }
                                            for k, v in (_sup_raw_results or {}).items()
                                        },
                                        "project_name": project_name or "",
                                        "stack_id": stack_id or "nextjs-clerk-prisma",
                                    },
                                    run_id=run_id or "",
                                )
                            except Exception as _sl_err:
                                logger.warning(f"[inline_supervisor] shadow log non bloquant: {_sl_err}")
                        except Exception as _sup_err:
                            logger.warning(f"[inline_supervisor] non bloquant: {_sup_err}")
                    _batch_duration_ms = int((time.perf_counter() - _batch_t0) * 1000)
                    logger.info(
                        f"[inline_supervisor] batch_size={len(_batch)} duration_ms={_batch_duration_ms} "
                        f"timeout_ms={supervisor_timeout_ms}"
                    )

        if build_failed_this_iter:
            build_attempts += 1
            if last_build_error_full:
                try:
                    with ThreadPoolExecutor(max_workers=1) as _ex:
                        _bs_result = _ex.submit(
                            asyncio.run,
                            _run_build_supervisor_inline(
                                last_build_error_full,
                                files,
                                run_id,
                                stack_id,
                            ),
                        ).result()
                    if _bs_result:
                        _build_corrections_count += 1
                        runner.inject(_bs_result)
                        logger.info("[build_supervisor] correction injectée dans la boucle")
                except Exception as _bs_err:
                    logger.warning(f"[build_supervisor] non bloquant: {_bs_err}")

        if called_build_this_iter:
            stagnant_iterations = 0
        elif wrote_file_this_iter:
            if not supervision_loop.has_pending_corrections() or _wrote_pending_file_this_iter:
                stagnant_iterations = 0
            else:
                stagnant_iterations += 1
                logger.info(
                    f"[stagnant] LLM a écrit des fichiers mais pas les {len(supervision_loop.pending_paths())} "
                    f"fichier(s) en attente superviseur — stagnant_iterations={stagnant_iterations}"
                )
        else:
            stagnant_iterations += 1

        if wrote_file_this_iter:
            _post_write_state = run_state_computer.compute(files, build_attempts, last_build_error)
            _post_write_state["iterations_left"] = max(0, max_iterations - iteration + 1)
            _pre_blocker = run_state.get("active_blocker", "")
            _post_blocker = _post_write_state.get("active_blocker", "")
            if _pre_blocker and _pre_blocker == _post_blocker and _pre_blocker != "ready_for_build":
                _allowed = allowed_paths_for_blocker(_post_write_state, scaffold_extends_paths)
                _allowed_msg = ", ".join(_allowed) if _allowed else "aucune restriction"
                runner.inject((
                    "[IMMEDIATE_VERIFY] Le blocker actif n'a pas été résolu dans ce tour.\n"
                    f"Blocker courant: {_post_blocker}\n"
                    f"Chemins autorisés maintenant: {_allowed_msg}\n"
                    "Corrige ce blocker en priorité avant toute autre écriture."
                ))

        _primary = get_root_file(stack_id) if stack_id else "package.json"
        if current_phase == 1 and wrote_file_this_iter and _primary not in files:
            non_pkg_files = [
                tc["args"].get("path", "")
                for tc in response.tool_calls
                if tc["name"] == "write_file" and tc["args"].get("path", "") != _primary
            ]
            if non_pkg_files:
                logger.warning(
                    f"[PHASE1_SEQUENCE_VIOLATION] Fichier(s) écrit(s) avant {_primary} : {non_pkg_files}"
                )
                runner.inject((
                    f"⚠️ ERREUR DE SÉQUENCE CRITIQUE : Tu as écrit {non_pkg_files} avant {_primary}.\n"
                    f"RÈGLE ABSOLUE : {_primary} DOIT être le PREMIER fichier généré, AVANT TOUT AUTRE.\n"
                    f"ACTION OBLIGATOIRE IMMÉDIATE : génère {_primary} maintenant avec les versions exactes :\n"
                    + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in packages.items())
                    + f"\n\nNe génère AUCUN autre fichier avant que {_primary} soit écrit."
                ))

        _pdir = find_project_dir(files, effective_stack_id)
        _files_norm = {p.replace("\\", "/").lower() for p in files}
        if all(
            any(
                fp == k.replace("\\", "/").lower() or fp.endswith("/" + k.replace("\\", "/").lower())
                for fp in _files_norm
            )
            for k in key_files
        ) and not build_success:
            _early_gates_blocked, _early_gates_msg, _, _early_gate_warns = pre_build_validator.check(files)
            iter_gate_warnings.extend(_early_gate_warns)
            if _early_gates_blocked:
                runner.inject(f"[PRE_BUILD_CHECK]\n{_early_gates_msg}")
            else:
                _rg_early_blocked, _rg_early_msg = _engine_gate_check(requirements or [], files)
                if _rg_early_blocked:
                    runner.inject(f"[REQUIREMENTS CHECK]\n{_rg_early_msg}")
                else:
                    runner.inject(f"Fichiers clés présents. Appelle run_build(project_dir='{_pdir}') maintenant pour valider le projet.")

        if not build_success and not called_build_this_iter and (stagnant_iterations >= 2 or iteration >= max_iterations - 1):
            _bypass_sup = stagnant_iterations >= 2 and supervision_loop.has_pending_corrections()
            if _bypass_sup:
                for _bp_path in list(supervision_loop.pending_paths()):
                    supervision_loop.on_supervisor_ok(_bp_path)
                logger.warning(
                    "[supervision_loop] BYPASS — corrections pendantes force-validées en best-effort "
                    f"après {stagnant_iterations} itérations stagnantes"
                )
            _forced_blocked, _forced_msg, _, _forced_gate_warns = pre_build_validator.check(files, bypass_supervision=_bypass_sup)
            iter_gate_warnings.extend(_forced_gate_warns)
            if not _forced_blocked:
                _forced_blocked, _forced_msg = _engine_gate_check(requirements or [], files)
            if _forced_blocked:
                runner.inject(f"[PRE_BUILD_CHECK]\n{_forced_msg}")
                logger.warning("[PreBuildGate] FORCED BUILD BLOQUÉ — fichiers manquants ou violations")
                stagnant_iterations = 0
            else:
                forced_build_output = str(run_build.invoke({"project_dir": _pdir}))
                build_attempted = True
                called_build_this_iter = True
                raw_tool_outputs.append(forced_build_output)
                runner.inject(f"[FORCED_RUN_BUILD]\n{runner._shrink_tool_output('run_build', forced_build_output)}")
                if "Build successful" in forced_build_output:
                    last_build_succeeded = True
                    build_success = True
                    build_attempts = 0
                    last_build_error = ""
                    last_build_error_full = ""
                    last_failed_command = ""
                else:
                    build_attempts += 1
                    extracted_stderr = _extract_stderr(forced_build_output)
                    last_build_error_full = extracted_stderr if extracted_stderr else forced_build_output
                    last_build_error = last_build_error_full[:2000]
                    failed_cmd = _extract_failed_command(forced_build_output)
                    if failed_cmd:
                        last_failed_command = failed_cmd
                    try:
                        with ThreadPoolExecutor(max_workers=1) as _ex:
                            _bs_result = _ex.submit(
                                asyncio.run,
                                _run_build_supervisor_inline(
                                    last_build_error_full,
                                    files,
                                    run_id,
                                    stack_id,
                                ),
                            ).result()
                        if _bs_result:
                            _build_corrections_count += 1
                            runner.inject(_bs_result)
                            logger.info("[build_supervisor] correction injectée après FORCED_RUN_BUILD")
                    except Exception as _bs_err:
                        logger.warning(f"[build_supervisor] non bloquant (forced): {_bs_err}")

        _append_aggregated_gate_warnings(iter_gate_warnings)

        _reflection_state = run_state_computer.compute(files, build_attempts, last_build_error)
        _reflection_state["iterations_left"] = max(0, max_iterations - iteration + 1)
        _reflection_unmet = _reflection_state.get("requirements_unmet", [])
        _reflection_missing = _reflection_state.get("missing_required_files", [])
        reflection_messages = [
            SystemMessage(content=(
                "État actuel :\n"
                f"Requirements couverts : {_reflection_state.get('requirements_met', 0)}/{_reflection_state.get('requirements_total', 0)}\n"
                f"Blocker actif : {_reflection_state.get('active_blocker', 'N/A')}\n"
                f"Requirement prioritaire non couvert : {_reflection_unmet[0] if _reflection_unmet else 'N/A'}\n"
                f"Fichier requis manquant prioritaire : {_reflection_missing[0] if _reflection_missing else 'N/A'}\n"
                f"Build attempts : {build_attempts}/{max_build_attempts}\n"
                f"Dernière erreur build : {last_build_error[:500] if last_build_error else 'N/A'}\n"
                f"Dernière commande en échec : {last_failed_command or 'N/A'}\n"
                "- Si 'Build successful' dans les logs → réponds 'TERMINÉ : CODE PRÊT'\n"
                "- Si trop d'échecs → 'ÉCHEC : ERREUR RÉCURRENTE BUILD'\n"
                "- Sinon → continue l'étape suivante sans réécrire les fichiers existants."
            )),
            HumanMessage(content=(
                f"Résumé runtime: blocker={_reflection_state.get('active_blocker', 'N/A')}, "
                f"requirements={_reflection_state.get('requirements_met', 0)}/{_reflection_state.get('requirements_total', 0)}"
            ))
        ]

        reflection_response = llm.invoke(reflection_messages)
        reflection = reflection_response.content.strip()

        if hasattr(reflection_response, "tool_calls") and reflection_response.tool_calls:
            logger.warning("Reflection a généré des tool_calls inattendus → ignorés pour sécurité")

        runner.inject(reflection)

        if last_build_succeeded:
            _state = _SM_FINAL
            logger.info(f"[STATE] BUILD → {_state} | BUILD_SUCCESS")
            build_success = True
            final_message = "BUILD_SUCCESS"
            break

        if build_attempts >= max_build_attempts:
            _state = _SM_FINAL
            logger.info(f"[STATE] {_state} → FINAL | BUILD_FAILED (max attempts)")
            final_message = "BUILD_FAILED"
            break

    if not build_success and _state != _SM_FINAL:
        _state = _SM_FINAL
        logger.info(f"[STATE] → {_state} | MAX_ITER_REACHED")
        final_message = "MAX_ITER_REACHED"

    _terminal_guard_handled = False
    if not build_attempted and files:
        _terminal_guard_handled = True
        _tg_dir = find_project_dir(files, effective_stack_id)
        _tg_blocked, _tg_msg, _tg_gid, _ = pre_build_validator.check(files)
        _tg_is_structural = _tg_blocked
        if not _tg_blocked:
            _tg_blocked, _tg_msg = _engine_gate_check(requirements or [], files)
            _tg_gid = "requirements" if _tg_blocked else ""
        if _tg_blocked:
            final_message = "NOT_BUILT_BY_GATE"
            _final_gate_source = "structural" if _tg_is_structural else "requirements"
            _final_blocking_guard_id = _tg_gid
            _final_gate_message = (_tg_msg or "")[:2000]
            if _tg_gid == "blueprint":
                _present = set(files.keys()) | templated_names
                _present_norm = {p.replace("\\", "/").lower() for p in _present}
                _final_missing_required_files = [
                    f
                    for f in required_files
                    if not any(
                        pp == str(f).replace("\\", "/").lower()
                        or pp.endswith("/" + str(f).replace("\\", "/").lower())
                        for pp in _present_norm
                    )
                ]
            logger.warning(f"[terminal_guard] build non tente: gate bloque. guard={_tg_gid} detail={_tg_msg[:400]}")
        else:
            forced_build_output = str(run_build.invoke({"project_dir": _tg_dir}))
            build_attempted = True
            logger.info("[terminal_guard] run_build force hors boucle LLM")
            if "Build successful" in forced_build_output:
                last_build_succeeded = True
                build_success = True
                final_message = "BUILD_SUCCESS"
                last_build_error = ""
                last_build_error_full = ""
                last_failed_command = ""
            else:
                _tg_stderr = _extract_stderr(forced_build_output)
                last_build_error_full = _tg_stderr if _tg_stderr else forced_build_output
                last_build_error = last_build_error_full[:2000]
                _tg_cmd = _extract_failed_command(forced_build_output)
                if _tg_cmd:
                    last_failed_command = _tg_cmd
                final_message = "BUILD_FAILED"

    if not _terminal_guard_handled and not build_attempted and not build_success:
        _state = _SM_FINAL
        final_message = "NOT_BUILT_BY_GATE"
        _final_gate_source = "no_files"
        _final_gate_message = "Aucun fichier généré; build non tentée."
        logger.info(f"[STATE] → {_state} | NOT_BUILT_BY_GATE (aucun fichier généré)")

    return DevLoopState(
        iteration=iteration,
        stagnant_iterations=stagnant_iterations,
        build_attempts=build_attempts,
        build_attempted=build_attempted,
        build_success=build_success,
        last_build_succeeded=last_build_succeeded,
        last_build_error=last_build_error,
        last_build_error_full=last_build_error_full,
        last_test_error=last_test_error,
        last_test_error_full=last_test_error_full,
        last_failed_command=last_failed_command,
        final_message=final_message,
        files=files,
        final_gate_source=_final_gate_source,
        final_blocking_guard_id=_final_blocking_guard_id,
        final_gate_message=_final_gate_message,
        final_missing_required_files=list(_final_missing_required_files),
        sup_files_reviewed=_sup_files_reviewed,
        sup_corrections_count=_sup_corrections_count,
        build_corrections_count=_build_corrections_count,
        conformity_scores=list(_conformity_scores),
        security_scores=list(_security_scores),
        architecture_scores=list(_architecture_scores),
    )
