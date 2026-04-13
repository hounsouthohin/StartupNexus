from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy


MAIN_TASK_QUEUE = "factory-task-queue"
DEV_TASK_QUEUE  = "factory-dev-queue"
BUILD_TASK_QUEUE = "factory-build-queue"

CONTINUE_AS_NEW_THRESHOLD = 10


@dataclass
class GenerationSessionRequest:
    run_id: str
    stack_id: str
    project_name: str
    requirements_ref: str
    plan_ref: str


@dataclass
class GenerationSessionState:
    run_id: str
    stack_id: str
    project_name: str
    batch_cursor: int
    completed_files: list[str] = field(default_factory=list)
    corrections_applied: int = 0
    iteration: int = 0
    requirements_ref: str = ""
    plan_ref: str = ""


@workflow.defn
class GenerationSessionWorkflow:
    def __init__(self) -> None:
        self._pending_batch: dict | None = None
        self._pending_corrections: dict | None = None
        self._abort_requested: bool = False
        self._status: str = "waiting_batch"
        self._state: GenerationSessionState | None = None

    @workflow.signal
    async def batch_ready(self, payload: dict) -> None:
        self._pending_batch = dict(payload or {})
        self._status = "supervising"

    @workflow.signal
    async def abort_generation(self, reason: str = "") -> None:
        _ = reason  # conservé pour traçabilité future
        self._abort_requested = True
        self._status = "aborted"

    @workflow.query
    def state_snapshot(self) -> dict:
        if self._state is None:
            return {
                "run_id": "",
                "batch_cursor": 0,
                "iteration": 0,
                "completed_files": [],
                "corrections_applied": 0,
                "pending_corrections": self._pending_corrections,
                "status": self._status,
            }
        return {
            "run_id": self._state.run_id,
            "batch_cursor": self._state.batch_cursor,
            "iteration": self._state.iteration,
            "completed_files": list(self._state.completed_files),
            "corrections_applied": self._state.corrections_applied,
            "pending_corrections": self._pending_corrections,
            "status": self._status,
        }

    @workflow.run
    async def run(
        self,
        request: GenerationSessionRequest | GenerationSessionState | Dict[str, Any],
    ) -> Dict[str, Any]:
        if isinstance(request, dict):
            if "batch_cursor" in request:
                state = GenerationSessionState(
                    run_id=str(request.get("run_id", "")),
                    stack_id=str(request.get("stack_id", "")),
                    project_name=str(request.get("project_name", "")),
                    batch_cursor=int(request.get("batch_cursor", 0)),
                    completed_files=list(request.get("completed_files", []) or []),
                    corrections_applied=int(request.get("corrections_applied", 0)),
                    iteration=int(request.get("iteration", 0)),
                    requirements_ref=str(request.get("requirements_ref", "")),
                    plan_ref=str(request.get("plan_ref", "")),
                )
            else:
                req = GenerationSessionRequest(
                    run_id=str(request.get("run_id", "")),
                    stack_id=str(request.get("stack_id", "nextjs-clerk-prisma")),
                    project_name=str(request.get("project_name", "")),
                    requirements_ref=str(request.get("requirements_ref", "")),
                    plan_ref=str(request.get("plan_ref", "")),
                )
                state = GenerationSessionState(
                    run_id=req.run_id,
                    stack_id=req.stack_id,
                    project_name=req.project_name,
                    batch_cursor=0,
                    completed_files=[],
                    corrections_applied=0,
                    iteration=0,
                    requirements_ref=req.requirements_ref,
                    plan_ref=req.plan_ref,
                )
        elif isinstance(request, GenerationSessionState):
            state = request
        else:
            state = GenerationSessionState(
                run_id=request.run_id,
                stack_id=request.stack_id,
                project_name=request.project_name,
                batch_cursor=0,
                completed_files=[],
                corrections_applied=0,
                iteration=0,
                requirements_ref=request.requirements_ref,
                plan_ref=request.plan_ref,
            )

        common_retry = RetryPolicy(
            initial_interval=timedelta(seconds=3),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )
        self._state = state
        self._status = "waiting_batch"
        self._abort_requested = False
        self._pending_batch = None
        self._pending_corrections = None

        while True:
            self._status = "waiting_batch"
            try:
                await workflow.wait_condition(
                    lambda: self._pending_batch is not None or self._abort_requested,
                    timeout=timedelta(minutes=30),
                )
            except asyncio.TimeoutError:
                self._status = "aborted"
                self._abort_requested = True
                break

            if self._abort_requested:
                break

            batch_ready = dict(self._pending_batch or {})
            self._pending_batch = None
            self._status = "supervising"

            files_count = int(batch_ready.get("files_count", 0) or 0)
            no_more_files = bool(batch_ready.get("no_more_files", False))
            if no_more_files or files_count <= 0:
                break

            batch_id = str(batch_ready.get("batch_id", f"batch_{state.batch_cursor:03d}"))
            artifact_ref = batch_ready.get("artifact_ref", {})
            # M2 : les activités superviseurs attendent maintenant `files: dict`
            # On lit le fichier batch depuis le disque pour obtenir les fichiers réels.
            batch_files: dict = batch_ready.get("files", {}) or {}

            supervisor_input = {
                "files": batch_files,
                "run_id": state.run_id,
                "stack_id": state.stack_id,
                "requirements": batch_ready.get("requirements", []),
                "plan": batch_ready.get("plan", {}),
                "project_name": state.project_name,
            }

            # Superviseurs LLM supprimés (Phase C) — supervision déterministe inline uniquement.
            sup_results: list = []

            corrections_bundle = await workflow.execute_activity(
                "aggregate_corrections_activity",
                {
                    "run_id": state.run_id,
                    "batch_id": batch_id,
                    "supervisor_results": sup_results,
                    "artifact_ref": artifact_ref,
                    "stack_id": state.stack_id,
                },
                task_queue=MAIN_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=common_retry,
            )
            corrections_bundle = corrections_bundle or {}
            self._pending_corrections = corrections_bundle

            apply_result = await workflow.execute_activity(
                "apply_corrections_activity",
                {
                    "run_id": state.run_id,
                    "batch_id": batch_id,
                    "artifact_ref": artifact_ref,
                    "corrections_bundle": corrections_bundle,
                    "stack_id": state.stack_id,
                },
                task_queue=DEV_TASK_QUEUE,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=common_retry,
            )
            apply_result = apply_result or {}

            applied_count = int(corrections_bundle.get("total_fixes", 0) or 0)
            state.corrections_applied += applied_count

            completed_from_apply = apply_result.get("completed_files", [])
            if isinstance(completed_from_apply, list) and completed_from_apply:
                dedup = set(state.completed_files)
                for p in completed_from_apply:
                    ps = str(p)
                    if ps and ps not in dedup:
                        state.completed_files.append(ps)
                        dedup.add(ps)

            state.batch_cursor += 1
            state.iteration += 1

            # continue_as_new strictement entre deux batchs
            if (
                CONTINUE_AS_NEW_THRESHOLD > 0
                and state.iteration > 0
                and state.iteration % CONTINUE_AS_NEW_THRESHOLD == 0
            ):
                workflow.continue_as_new(asdict(state))

        self._status = "aborted" if self._abort_requested else "done"
        build_result = await workflow.execute_activity(
            "build_activity",
            {
                "run_id": state.run_id,
                "stack_id": state.stack_id,
                "project_name": state.project_name,
                "requirements_ref": state.requirements_ref,
                "plan_ref": state.plan_ref,
                "completed_files": state.completed_files,
            },
            task_queue=BUILD_TASK_QUEUE,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=common_retry,
        )

        return {
            "run_id": state.run_id,
            "stack_id": state.stack_id,
            "project_name": state.project_name,
            "batch_cursor": state.batch_cursor,
            "completed_files": state.completed_files,
            "corrections_applied": state.corrections_applied,
            "iteration": state.iteration,
            "requirements_ref": state.requirements_ref,
            "plan_ref": state.plan_ref,
            "build_result": build_result,
        }
