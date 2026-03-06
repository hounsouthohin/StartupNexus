"""
agents/learner.py — LearnerActivity Sprint 3.

Analyse le learner_shadow_log.json (events dev_test_run + qa_run)
et génère des StandardSuggestion exploitables pour améliorer
la factory (prompts, standards Qdrant, config stack, guards).

Appelé en fin de run Temporal via learner_activity (best-effort).
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = Path("logs/shadow/learner_shadow_log.json")
MIN_RUNS_FOR_ANALYSIS = 3


@dataclass
class StandardSuggestion:
    """Suggestion de standard générée par le LearnerActivity."""
    suggestion_id: str
    category: str        # "prompt" | "config" | "standard" | "guard" | "anti_pattern"
    severity: str        # "low" | "medium" | "high"
    title: str
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sprint: str = "sprint3"


def run_learner_activity(run_id: str = "") -> dict:
    """
    Point d'entrée de la LearnerActivity.
    Lit le shadow log, détecte les patterns, génère des StandardSuggestion.
    Retourne : {"suggestions_generated": int, "suggestions": list, error?: str}
    """
    try:
        events = _load_dev_test_events()

        if len(events) < MIN_RUNS_FOR_ANALYSIS:
            logger.info(
                f"[learner] Seulement {len(events)} run(s) — "
                f"minimum {MIN_RUNS_FOR_ANALYSIS} requis pour l'analyse"
            )
            return {
                "suggestions_generated": 0,
                "suggestions": [],
                "skipped_reason": f"Insufficient data ({len(events)} < {MIN_RUNS_FOR_ANALYSIS})",
            }

        suggestions = _analyze_patterns(events)
        _save_suggestions(suggestions, run_id)

        logger.info(
            f"[learner] {len(suggestions)} StandardSuggestion(s) générées "
            f"à partir de {len(events)} run(s)"
        )
        return {
            "suggestions_generated": len(suggestions),
            "suggestions": [asdict(s) for s in suggestions],
        }

    except Exception as e:
        logger.error(f"[learner] Erreur analyse: {e}", exc_info=True)
        return {"suggestions_generated": 0, "suggestions": [], "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Chargement des données
# ─────────────────────────────────────────────────────────────────────────────

def _load_dev_test_events() -> list[dict]:
    """Charge tous les events dev_test_run depuis le shadow log."""
    if not SHADOW_LOG_PATH.exists():
        logger.warning(f"[learner] Shadow log introuvable: {SHADOW_LOG_PATH}")
        return []
    try:
        log = json.loads(SHADOW_LOG_PATH.read_text(encoding="utf-8"))
        return [
            e for e in log.get("suggested_standards", [])
            if e.get("event_type") == "dev_test_run"
        ]
    except Exception as e:
        logger.warning(f"[learner] Impossible de lire le shadow log: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_build_error(error: str) -> str:
    """
    Normalise une erreur de build pour regrouper les signatures similaires.
    Supprime les parties variables (chemins, numéros de ligne, identifiants).
    """
    e = error.lower()
    e = re.sub(r'[./\w-]+\.(ts|tsx|js|jsx|json|prisma)', '<FILE>', e)
    e = re.sub(r':\d+:\d+', '', e)
    e = re.sub(r"'[^']{1,60}'", "'<ID>'", e)
    return e[:120].strip()


# ─────────────────────────────────────────────────────────────────────────────
# Analyse des patterns
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_patterns(events: list[dict]) -> list[StandardSuggestion]:
    """
    Analyse les events dev_test_run et retourne une liste de StandardSuggestion.
    Patterns détectés :
      P001 — Taux de succès global
      P002 — Violations sémantiques fréquentes
      P003 — Fichiers insuffisants sur les échecs
      P004 — MAX_ITERATIONS atteint trop souvent
      P005 — Amélioration du taux de succès (signal positif)
    """
    suggestions: list[StandardSuggestion] = []
    payloads = [e.get("payload", {}) for e in events]
    total = len(payloads)

    def _is_full_success(p: dict) -> bool:
        """
        Retourne True uniquement pour un succès complet (spec_coverage >= seuil).
        Priorité à delivery_status (nouveau champ) ; fallback sur success bool
        pour les events antérieurs à F-B2 qui ne l'ont pas.
        Un run PARTIAL (build ok mais spec_coverage < seuil) retourne False.
        """
        ds = p.get("delivery_status")
        if ds is not None:
            return ds == "success"
        return bool(p.get("success", False))

    # ── P001 : Taux de succès global ─────────────────────────────────────────
    successes = sum(1 for p in payloads if _is_full_success(p))
    success_rate = successes / total
    if success_rate < 0.5:
        suggestions.append(StandardSuggestion(
            suggestion_id=f"P001-{uuid.uuid4().hex[:6]}",
            category="prompt",
            severity="high",
            title="Taux de succès global insuffisant",
            description=(
                f"Seulement {success_rate:.0%} de succès sur {total} runs. "
                "Améliorer les prompts dev ou renforcer les guards de séquence."
            ),
            evidence={
                "success_rate": round(success_rate, 3),
                "total_runs": total,
                "successes": successes,
            },
        ))

    # ── P002 : Violations sémantiques fréquentes ─────────────────────────────
    violation_counter: Counter = Counter()
    for p in payloads:
        for v in p.get("semantic_violations", []):
            if isinstance(v, str):
                violation_counter[v] += 1

    for violation, count in violation_counter.most_common():
        if count >= 2:
            suggestions.append(StandardSuggestion(
                suggestion_id=f"P002-{uuid.uuid4().hex[:6]}",
                category="guard",
                severity="medium",
                title=f"Violation sémantique récurrente: {violation[:60]}",
                description=(
                    f"'{violation}' observée {count}× sur {total} runs. "
                    "Envisager un guard explicite dans spec_validation ou une "
                    "reformulation dans les standards Qdrant."
                ),
                evidence={"violation": violation, "count": count, "total_runs": total},
            ))

    # ── P003 : Fichiers insuffisants sur les échecs ───────────────────────────
    failed_runs = [p for p in payloads if not p.get("success", False)]
    if failed_runs:
        avg_files_failed = sum(p.get("files_count", 0) for p in failed_runs) / len(failed_runs)
        if avg_files_failed < 8:
            suggestions.append(StandardSuggestion(
                suggestion_id=f"P003-{uuid.uuid4().hex[:6]}",
                category="config",
                severity="medium",
                title="Nombre de fichiers insuffisant sur les runs échoués",
                description=(
                    f"Les runs échoués génèrent en moyenne {avg_files_failed:.1f} fichiers "
                    "(seuil: 8). Renforcer l'instruction 'minimum 14 fichiers' dans le "
                    "prompt architecte ou ajouter un guard files_count < 8 dans dev_test_activity."
                ),
                evidence={
                    "avg_files_failed": round(avg_files_failed, 1),
                    "failed_runs": len(failed_runs),
                    "threshold": 8,
                },
            ))

    # ── P004 : MAX_ITERATIONS atteint trop souvent ───────────────────────────
    max_iter_runs = [p for p in payloads if p.get("iterations", 0) >= 10]
    if total > 0 and len(max_iter_runs) / total >= 0.3:
        suggestions.append(StandardSuggestion(
            suggestion_id=f"P004-{uuid.uuid4().hex[:6]}",
            category="config",
            severity="medium",
            title="MAX_ITERATIONS atteint dans plus de 30% des runs",
            description=(
                f"{len(max_iter_runs)}/{total} runs atteignent MAX_ITERATIONS (≥10). "
                "Envisager un early-stop basé sur les fichiers générés ou "
                "des prompts plus directifs pour réduire le nombre d'itérations."
            ),
            evidence={
                "max_iter_runs": len(max_iter_runs),
                "total": total,
                "ratio": round(len(max_iter_runs) / total, 3),
                "threshold": 0.3,
            },
        ))

    # ── P005 : Amélioration du taux de succès (signal positif) ───────────────
    if total >= 10:
        early_success = sum(1 for p in payloads[:5] if _is_full_success(p)) / 5
        recent_success = sum(1 for p in payloads[-5:] if _is_full_success(p)) / 5
        if recent_success >= early_success + 0.2:
            suggestions.append(StandardSuggestion(
                suggestion_id=f"P005-{uuid.uuid4().hex[:6]}",
                category="standard",
                severity="low",
                title="Amélioration du taux de succès confirmée sur les 5 derniers runs",
                description=(
                    f"Taux de succès: {early_success:.0%} (5 premiers) → "
                    f"{recent_success:.0%} (5 derniers). "
                    "Les changements récents sont positifs — les documenter dans "
                    "MEMORY.md et promouvoir les guards correspondants en standard Qdrant."
                ),
                evidence={
                    "early_success_rate": round(early_success, 3),
                    "recent_success_rate": round(recent_success, 3),
                    "improvement": round(recent_success - early_success, 3),
                },
            ))

    # ── P006 : Anti-patterns récurrents depuis les erreurs de build ───────────
    error_counter: Counter = Counter()
    failed_payloads = [p for p in payloads if not p.get("success", False)]
    for p in failed_payloads:
        raw_error = p.get("last_build_error", "") or ""
        if raw_error:
            sig = _normalize_build_error(raw_error)
            if sig:
                error_counter[sig] += 1

    for sig, count in error_counter.most_common(5):
        if count >= 2:
            suggestions.append(StandardSuggestion(
                suggestion_id=f"P006-{uuid.uuid4().hex[:6]}",
                category="anti_pattern",
                severity="high",
                title=f"Erreur de build récurrente ({count}×): {sig[:60]}",
                description=(
                    f"La signature d'erreur '{sig[:80]}' est apparue {count}× "
                    f"sur {len(failed_payloads)} builds échoués. "
                    "Ce pattern est candidat à un standard Qdrant ZONE_14 "
                    "(anti-pattern) pour prévenir cette erreur en amont."
                ),
                evidence={
                    "error_signature": sig,
                    "count": count,
                    "failed_runs": len(failed_payloads),
                },
                sprint="sprint4",
            ))

    # ── P007 : spec_coverage bas récurrent ───────────────────────────────────
    coverage_values = [
        p.get("spec_coverage", None)
        for p in payloads
        if p.get("spec_coverage") is not None
    ]
    if len(coverage_values) >= 3:
        avg_coverage = sum(coverage_values) / len(coverage_values)
        low_coverage_runs = [c for c in coverage_values if c < 0.5]
        if len(low_coverage_runs) / len(coverage_values) >= 0.5:
            suggestions.append(StandardSuggestion(
                suggestion_id=f"P007-{uuid.uuid4().hex[:6]}",
                category="prompt",
                severity="high",
                title=f"spec_coverage systématiquement bas (moy. {avg_coverage:.0%})",
                description=(
                    f"spec_coverage < 50% sur {len(low_coverage_runs)}/{len(coverage_values)} runs "
                    f"(moyenne: {avg_coverage:.0%}). "
                    "Le spec_writer génère des specs génériques qui ignorent les requirements métier. "
                    "Action : renforcer l'EXTRACTION RULE dans le prompt spec_writer ou ajouter "
                    "un guard dans spec_writer_node qui rejette les specs sans modèles métier."
                ),
                evidence={
                    "avg_coverage": round(avg_coverage, 3),
                    "low_coverage_runs": len(low_coverage_runs),
                    "total_with_coverage": len(coverage_values),
                    "threshold": 0.5,
                },
                sprint="sprint4",
            ))

    return suggestions


# ─────────────────────────────────────────────────────────────────────────────
# Sauvegarde
# ─────────────────────────────────────────────────────────────────────────────

def _save_suggestions(suggestions: list[StandardSuggestion], run_id: str) -> None:
    """Sauvegarde chaque suggestion comme event 'learner_suggestion' dans le shadow log."""
    if not suggestions:
        return
    try:
        from agents.observability import _write_learner_event
        for s in suggestions:
            _write_learner_event(
                event_type="learner_suggestion",
                payload=asdict(s),
                run_id=run_id,
            )
        logger.info(f"[learner] {len(suggestions)} suggestion(s) sauvegardées dans {SHADOW_LOG_PATH}")
    except Exception as e:
        logger.warning(f"[learner] Impossible de sauvegarder les suggestions: {e}")
