"""
DevOrchestrator — Phase R5 : extraction run_batch.

Invariant : aucun changement de comportement métier.
Le moteur canonique reste dev_agent(); ce module expose maintenant un état
de boucle explicite (DevLoopState) et un contrat batch-oriented pour Temporal.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from agents.llm_runner import LLMConversationRunner

logger = logging.getLogger(__name__)


@dataclass
class DevLoopState:
    # État mutable de la boucle dev_agent
    files: dict = field(default_factory=dict)
    build_success: bool = False
    build_attempted: bool = False
    build_attempts: int = 0
    stagnant_iterations: int = 0
    last_build_error: str = ""
    last_build_error_full: str = ""
    last_test_error: str = ""
    last_test_error_full: str = ""
    last_failed_command: str = ""
    last_build_succeeded: bool = False
    iteration: int = 0
    _state: str = "GEN"
    _sup_files_reviewed: int = 0
    _sup_corrections_count: int = 0
    _build_corrections_count: int = 0
    _conformity_scores: list[float] = field(default_factory=list)
    _security_scores: list[float] = field(default_factory=list)
    _architecture_scores: list[float] = field(default_factory=list)
    _guard_warning_hits: dict[str, int] = field(default_factory=dict)
    final_message: str = ""
    done: bool = False
    raw: dict = field(default_factory=dict)

    def to_raw_dict(self) -> dict:
        """Miroir du payload dev_agent() pour compatibilité totale."""
        if self.raw:
            return self.raw
        return {
            "files": dict(self.files),
            "final_message": self.final_message,
            "success": bool(self.build_success),
            "metadata": {
                "iterations": int(self.iteration),
                "build_attempts": int(self.build_attempts),
                "build_attempted": bool(self.build_attempted),
                "total_files": len(self.files),
                "last_build_error": self.last_build_error,
                "last_build_error_full": self.last_build_error_full,
                "last_test_error": self.last_test_error,
                "last_test_error_full": self.last_test_error_full,
                "last_failed_command": self.last_failed_command,
                "gate_source": "",
                "blocking_guard_id": "",
                "gate_message": "",
                "missing_required_files": [],
                "guard_warning_hits": dict(self._guard_warning_hits),
                "guard_warning_count": int(sum(self._guard_warning_hits.values())),
                "supervisor_files_reviewed": int(self._sup_files_reviewed),
                "supervisor_corrections_count": int(self._sup_corrections_count),
                "conformity_score": float(
                    (sum(self._conformity_scores) / len(self._conformity_scores))
                    if self._conformity_scores else 0.0
                ),
                "security_score": float(
                    (sum(self._security_scores) / len(self._security_scores))
                    if self._security_scores else 0.0
                ),
                "architecture_score": float(
                    (sum(self._architecture_scores) / len(self._architecture_scores))
                    if self._architecture_scores else 0.0
                ),
                "build_corrections_count": int(self._build_corrections_count),
            },
        }


@dataclass(frozen=True)
class DevLoopContext:
    # Readonly context pour une itération de boucle
    execute_full_run: Callable[[LLMConversationRunner | None, DevLoopState], dict]


def _run_one_iteration(
    state: DevLoopState,
    runner: LLMConversationRunner | None,
    ctx: DevLoopContext,
) -> DevLoopState:
    """
    Exécution d'une itération logique.

    Phase R5:
    - extraction structurelle sans changement métier
    - délègue encore à dev_agent() pour conserver le comportement identique
    """
    if state.done:
        return state

    raw = ctx.execute_full_run(runner, state)
    meta = raw.get("metadata", {}) or {}

    state.raw = raw
    state.files = raw.get("files", {}) or {}
    state.build_success = bool(raw.get("success", False))
    state.final_message = str(raw.get("final_message", "") or "")
    state.build_attempted = bool(meta.get("build_attempted", False))
    state.build_attempts = int(meta.get("build_attempts", 0) or 0)
    state.stagnant_iterations = int(meta.get("stagnant_iterations", 0) or 0)
    state.last_build_error = str(meta.get("last_build_error", "") or "")
    state.last_build_error_full = str(meta.get("last_build_error_full", "") or "")
    state.last_test_error = str(meta.get("last_test_error", "") or "")
    state.last_test_error_full = str(meta.get("last_test_error_full", "") or "")
    state.last_failed_command = str(meta.get("last_failed_command", "") or "")
    state.last_build_succeeded = bool(raw.get("success", False))
    state.iteration = int(meta.get("iterations", 0) or 0)
    state._state = "FINAL"
    state._sup_files_reviewed = int(meta.get("supervisor_files_reviewed", 0) or 0)
    state._sup_corrections_count = int(meta.get("supervisor_corrections_count", 0) or 0)
    state._build_corrections_count = int(meta.get("build_corrections_count", 0) or 0)
    state._guard_warning_hits = dict(meta.get("guard_warning_hits", {}) or {})
    state._conformity_scores = [float(meta.get("conformity_score", 0.0) or 0.0)]
    state._security_scores = [float(meta.get("security_score", 0.0) or 0.0)]
    state._architecture_scores = [float(meta.get("architecture_score", 0.0) or 0.0)]
    state.done = True
    return state


class DevOrchestrationResult:
    """
    Résultat structuré d'un run DevOrchestrator.
    Miroir exact du dict retourné par dev_agent().
    """

    __slots__ = (
        "files",
        "build_success",
        "final_message",
        "conformity_score",
        "security_score",
        "architecture_score",
        "sup_files_reviewed",
        "sup_corrections_count",
        "build_corrections_count",
        "build_attempts",
        "iterations_used",
        "guard_warning_hits",
        "last_build_error",
        "missing_required_files",
        "raw",
    )

    def __init__(self, raw: dict) -> None:
        self.raw = raw
        meta: dict = raw.get("metadata", {}) or {}

        self.files: dict = raw.get("files", {})
        self.build_success: bool = bool(raw.get("success", False))
        self.final_message: str = str(raw.get("final_message", ""))
        self.conformity_score: float = float(meta.get("conformity_score", 0.0))
        self.security_score: float = float(meta.get("security_score", 0.0))
        self.architecture_score: float = float(meta.get("architecture_score", 0.0))
        self.sup_files_reviewed: int = int(meta.get("supervisor_files_reviewed", 0))
        self.sup_corrections_count: int = int(meta.get("supervisor_corrections_count", 0))
        self.build_corrections_count: int = int(meta.get("build_corrections_count", 0))
        self.build_attempts: int = int(meta.get("build_attempts", 0))
        self.iterations_used: int = int(meta.get("iterations", 0))
        self.guard_warning_hits: dict = meta.get("guard_warning_hits", {})
        self.last_build_error: str = str(meta.get("last_build_error", ""))
        self.missing_required_files: list = list(meta.get("missing_required_files", []))


class DevOrchestrator:
    def __init__(
        self,
        spec: str,
        mermaid: str,
        project_name: str = "default-project",
        run_id: str = "",
        stack_id: str = "",
        requirements: List[str] | None = None,
        spec_unmatched: List[str] | None = None,
        plan: Dict[str, Any] | None = None,
    ) -> None:
        self._spec = spec
        self._mermaid = mermaid
        self._project_name = project_name
        self._run_id = run_id
        self._stack_id = stack_id
        self._requirements = requirements
        self._spec_unmatched = spec_unmatched
        self._plan = plan
        self._result: DevOrchestrationResult | None = None

    @property
    def result(self) -> DevOrchestrationResult | None:
        return self._result

    def _build_initial_state(self) -> DevLoopState:
        return DevLoopState()

    def _build_context(self) -> DevLoopContext:
        from agents.dev import dev_agent

        def _execute_full_run(_runner: LLMConversationRunner | None, _state: DevLoopState) -> dict:
            return dev_agent(
                spec=self._spec,
                mermaid=self._mermaid,
                project_name=self._project_name,
                run_id=self._run_id,
                stack_id=self._stack_id,
                requirements=self._requirements,
                spec_unmatched=self._spec_unmatched,
                plan=self._plan,
            )

        return DevLoopContext(execute_full_run=_execute_full_run)

    def run_batch(self, runner: LLMConversationRunner | None, n_iters: int = 3) -> DevLoopState:
        """
        Exécute jusqu'à n_iters itérations logiques.
        Phase R5: _run_one_iteration encapsule la délégation canonique à dev_agent().
        """
        state = self._state
        for _ in range(max(1, int(n_iters))):
            if state.done:
                break
            state = _run_one_iteration(state, runner, self._ctx)
        self._state = state
        return state

    def run(self) -> DevOrchestrationResult:
        logger.info(
            f"[DevOrchestrator] run start — project={self._project_name!r} "
            f"run_id={self._run_id!r} stack_id={self._stack_id!r}"
        )

        self._state = self._build_initial_state()
        self._ctx = self._build_context()
        runner: LLMConversationRunner | None = None

        while not self._state.done:
            self._state = self.run_batch(runner, n_iters=3)

        self._result = DevOrchestrationResult(self._state.to_raw_dict())
        logger.info(
            f"[DevOrchestrator] run done — build_success={self._result.build_success} "
            f"final_message={self._result.final_message!r}"
        )
        return self._result

    def summary(self) -> dict:
        if self._result is None:
            return {"status": "not_run"}
        r = self._result
        return {
            "status": "ok" if r.build_success else "failed",
            "build_success": r.build_success,
            "final_message": r.final_message,
            "files_count": len(r.files),
            "conformity_score": round(r.conformity_score, 3),
            "security_score": round(r.security_score, 3),
            "architecture_score": round(r.architecture_score, 3),
            "sup_files_reviewed": r.sup_files_reviewed,
            "sup_corrections_count": r.sup_corrections_count,
            "build_corrections_count": r.build_corrections_count,
            "build_attempts": r.build_attempts,
            "iterations_used": r.iterations_used,
            "last_build_error": r.last_build_error[:400] if r.last_build_error else "",
            "missing_required_files": r.missing_required_files,
        }
