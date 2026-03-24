"""
dev_loop.py — helpers de boucle dev et état d'itération.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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

    def mark_write(self, wrote_file_this_iter: bool, supervision_pending: bool, wrote_pending_file_this_iter: bool) -> None:
        if wrote_file_this_iter:
            if not supervision_pending or wrote_pending_file_this_iter:
                self.stagnant_iterations = 0
            else:
                self.stagnant_iterations += 1
        else:
            self.stagnant_iterations += 1

    def should_force_build(self, iteration: int, max_iterations: int, called_build_this_iter: bool) -> bool:
        return (
            not self.build_success
            and not called_build_this_iter
            and (self.stagnant_iterations >= 2 or iteration >= max_iterations - 1)
        )
