"""
build_state_manager.py — centralise l'état de build et les métriques de fin de run.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BuildStateManager:
    iteration: int = 0
    build_attempts: int = 0
    build_attempted: bool = False
    build_success: bool = False
    final_message: str = ""
    gate_source: str = ""
    blocking_guard_id: str = ""
    gate_message: str = ""
    missing_required_files: list[str] = field(default_factory=list)
    guard_warning_hits: dict[str, int] = field(default_factory=dict)
    supervisor_files_reviewed: int = 0
    supervisor_corrections_count: int = 0
    conformity_scores: list[float] = field(default_factory=list)
    security_scores: list[float] = field(default_factory=list)
    architecture_scores: list[float] = field(default_factory=list)
    build_corrections_count: int = 0
    last_build_error: str = ""
    last_build_error_full: str = ""
    last_test_error: str = ""
    last_test_error_full: str = ""
    last_failed_command: str = ""

    @staticmethod
    def _avg(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 3)

    def to_metadata(self, total_files: int, supervision_loop_corrections: int, supervision_loop_pending_at_end: int) -> dict:
        return {
            "iterations": self.iteration,
            "build_attempts": self.build_attempts,
            "build_attempted": self.build_attempted,
            "total_files": total_files,
            "last_build_error": self.last_build_error[:2000] if self.last_build_error else "",
            "last_build_error_full": self.last_build_error_full if self.last_build_error_full else "",
            "last_test_error": self.last_test_error[:2000] if self.last_test_error else "",
            "last_test_error_full": self.last_test_error_full if self.last_test_error_full else "",
            "last_failed_command": self.last_failed_command,
            "gate_source": self.gate_source,
            "blocking_guard_id": self.blocking_guard_id,
            "gate_message": self.gate_message,
            "missing_required_files": self.missing_required_files,
            "guard_warning_hits": self.guard_warning_hits,
            "guard_warning_count": sum(self.guard_warning_hits.values()),
            "supervisor_files_reviewed": self.supervisor_files_reviewed,
            "supervisor_corrections_count": self.supervisor_corrections_count,
            "conformity_score": self._avg(self.conformity_scores),
            "security_score": self._avg(self.security_scores),
            "architecture_score": self._avg(self.architecture_scores),
            "build_corrections_count": self.build_corrections_count,
            "supervision_loop_corrections": supervision_loop_corrections,
            "supervision_loop_pending_at_end": supervision_loop_pending_at_end,
        }
