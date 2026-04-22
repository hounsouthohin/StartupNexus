"""
pipeline_types.py — Types partagés de la pipeline de build.

Extraits de prebuild_pipeline.py pour briser la dépendance circulaire :
  quality_validator.py → prebuild_pipeline.py → quality_validator.py

Règle : ce module n'importe rien des autres agents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Violation:
    rule_id: str
    file: str
    reason: str
    fix_hint: str
    line: int | None = None
    col: int | None = None


@dataclass
class StageResult:
    stage_id: str
    tool: str
    status: Literal["ok", "failed", "skipped", "error"]
    duration_ms: int
    violations: list[Violation] = field(default_factory=list)
    exit_code: int | None = None
    evidence: str = ""


@dataclass
class PrebuildReport:
    run_id: str
    project_name: str
    stack_id: str
    timestamp: str
    blocking: bool
    stages: list[StageResult]
    violations: list[Violation]
    llm_correction_bundle: str
    stages_passed: list[str]
    stages_failed: list[str]
