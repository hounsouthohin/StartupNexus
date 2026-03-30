"""
build_state_manager.py — centralise l'état de build et les métriques de fin de run.

DEPRECATED (Phase A - Prebuild Truth Engine, 2026-03-30).
Legacy module kept for rollback/tests only.
Active runtime uses agents.dev_graph via dev_test_activity.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .dev_path_utils import sort_paths_by_priority, sort_requirements_by_priority
from .requirements_engine import compute_coverage_detailed as _engine_compute_coverage_detailed

if TYPE_CHECKING:
    from .pre_build_validator import PreBuildValidator


logger = logging.getLogger(__name__)
logger.warning(
    "[DEPRECATED] agents.build_state_manager is legacy and not used by active runtime path "
    "(dev_test_activity -> dev_graph)."
)


class RunStateComputer:
    def __init__(
        self,
        requirements,
        llm_required_files,
        validator,
        path_priority_ranker,
        scaffold_extends_paths,
    ) -> None:
        self.requirements = requirements
        self.llm_required_files = llm_required_files
        self.validator: "PreBuildValidator" = validator
        self.path_priority_ranker = path_priority_ranker
        self.scaffold_extends_paths = scaffold_extends_paths

    def compute(self, files_dict: dict, build_attempts: int, last_build_error: str) -> dict:
        cov = _engine_compute_coverage_detailed(self.requirements or [], files_dict)
        unmet = sort_requirements_by_priority(cov.get("unmet", []), self.path_priority_ranker)
        prisma_unmet = [
            r for r in unmet
            if ("modèle prisma" in str(r).lower() or "model prisma" in str(r).lower() or "prisma:" in str(r).lower())
        ]
        schema_text = str(files_dict.get("prisma/schema.prisma", "") or "")
        schema_has_model = bool(re.search(r"(?m)^\s*model\s+\w+\s*\{", schema_text))
        # DEBUG prisma loop trap — log uniquement quand des requirements Prisma restent unmet
        if prisma_unmet:
            _schema_keys = [k for k in files_dict.keys() if "schema.prisma" in k.replace("\\", "/").lower()]
            logger.info(
                "[prisma_debug] prisma_unmet=%d schema_keys=%s schema_has_model=%s schema_chars=%d",
                len(prisma_unmet), _schema_keys, schema_has_model, len(schema_text),
            )
            for _st in cov.get("statuses", []):
                _req_str = str(_st.get("requirement", ""))
                if "modèle prisma" in _req_str.lower() or "model prisma" in _req_str.lower():
                    logger.info(
                        "[prisma_debug] req=%r  satisfied=%s  reason=%r",
                        _req_str[:100], _st.get("satisfied"), _st.get("reason", ""),
                    )
        _present_p = {k.replace("\\", "/").lower() for k in files_dict.keys()}
        missing_files = sort_paths_by_priority(
            [p for p in self.llm_required_files
             if not any(pp == str(p).replace("\\", "/").lower() or pp.endswith("/" + str(p).replace("\\", "/").lower())
                        for pp in _present_p)],
            self.path_priority_ranker,
        )
        structural_gid, structural_paths = self.validator.find_blocking_targets(files_dict)
        # Priorité convergence: créer d'abord les fichiers blueprint manquants.
        # Sinon l'agent peut boucler sur des détails requirements sans jamais
        # produire le fichier racine attendu par le gate structural.
        if missing_files:
            missing_norm = [str(p).replace("\\", "/").lower() for p in missing_files]
            if "prisma/schema.prisma" in missing_norm:
                blocker = "file_missing::prisma/schema.prisma"
            elif prisma_unmet:
                # Priorité Prisma si des modèles manquent dans le schema,
                # même si d'autres modèles existent déjà (schema_has_model=True).
                # scaffold_extends accumule les blocs model — chaque write ajoute
                # les modèles manquants sans écraser les existants.
                # Note: la garde "not schema_has_model" a été retirée car elle
                # empêchait d'ajouter le premier modèle quand le second était déjà présent.
                blocker = f"requirements::{prisma_unmet[0]}"
            else:
                blocker = f"file_missing::{missing_files[0]}"
        elif structural_gid:
            blocker = f"structural::{structural_gid}"
        elif prisma_unmet:
            # Même logique hors missing_files.
            blocker = f"requirements::{prisma_unmet[0]}"
        elif unmet:
            blocker = f"requirements::{unmet[0]}"
        elif last_build_error:
            blocker = "build_error"
        else:
            blocker = "ready_for_build"
        return {
            "requirements_met": cov.get("requirements_met", 0),
            "requirements_unmet": cov.get("requirements_unmet", len(unmet)),
            "requirements_unknown": cov.get("requirements_unknown", 0),
            "requirements_total": cov.get("requirements_total", 0),
            "requirements_unmet_list": unmet,
            "requirements_unknown_list": cov.get("unknown", []),
            "requirements_statuses": cov.get("statuses", []),
            "missing_required_files": missing_files,
            "structural_blocking_guard_id": structural_gid,
            "structural_targets": structural_paths,
            "active_blocker": blocker,
            "last_build_error_excerpt": (last_build_error or "")[:400],
            "build_attempts": build_attempts,
        }


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
    tsc_errors_caught: int = 0
    eslint_errors_caught: int = 0
    prisma_errors_caught: int = 0
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
            "tsc_errors_caught": int(self.tsc_errors_caught),
            "eslint_errors_caught": int(self.eslint_errors_caught),
            "prisma_errors_caught": int(self.prisma_errors_caught),
            "supervision_loop_corrections": supervision_loop_corrections,
            "supervision_loop_pending_at_end": supervision_loop_pending_at_end,
        }
