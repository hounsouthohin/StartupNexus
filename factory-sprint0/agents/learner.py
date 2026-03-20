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
import os
import re
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOG_ROOT = Path(os.getenv("FACTORY_LOG_DIR", "/app/logs"))
SHADOW_LOG_PATH = _LOG_ROOT / "shadow" / "learner_shadow_log.json"
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
    supervisor_type: str = ""
    file_type: str = ""
    pattern: str = ""
    zone_target: str = ""
    confidence: float = 0.0
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
        all_events = _load_all_events()
        events = _load_dev_test_events(all_events)

        # ── SPRINT5 GATE : mise à jour rolling au plus tôt (avant check MIN_RUNS) ──
        # Le gate doit être alimenté dès le run #1, même si le learner skippe l'analyse.
        try:
            from scripts.sprint5_gate import update_gate as _update_gate
            if events:
                latest = events[-1]
                _gate_result = _update_gate(
                    build_success=bool(latest.get("build_success", False)),
                    spec_validation_status=str(latest.get("spec_validation_status", "UNKNOWN")),
                )
                if _gate_result.get("enforce"):
                    logger.warning(
                        "[learner] Architect Gate en mode ENFORCE — "
                        "spec DEGRADED persistante détectée sur la fenêtre glissante."
                    )
        except Exception as _gate_err:
            logger.warning(f"[learner] sprint5_gate non bloquant : {_gate_err}")

        supervisor_events_count = sum(
            1 for e in all_events if e.get("event_type") == "supervisor_file_reviewed"
        )
        if len(events) < MIN_RUNS_FOR_ANALYSIS and supervisor_events_count < MIN_RUNS_FOR_ANALYSIS:
            logger.info(
                f"[learner] Seulement {len(events)} run(s) dev_test et "
                f"{supervisor_events_count} event(s) supervisor_file_reviewed — "
                f"minimum {MIN_RUNS_FOR_ANALYSIS} requis pour l'analyse"
            )
            return {
                "suggestions_generated": 0,
                "suggestions": [],
                "skipped_reason": (
                    f"Insufficient data (dev_test={len(events)}, "
                    f"supervisor={supervisor_events_count}, min={MIN_RUNS_FOR_ANALYSIS})"
                ),
            }

        suggestions = _analyze_patterns(events)
        suggestions.extend(_analyze_supervisor_patterns(all_events))
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

def _load_all_events() -> list[dict]:
    """Charge tous les events depuis le shadow log."""
    if not SHADOW_LOG_PATH.exists():
        logger.warning(f"[learner] Shadow log introuvable: {SHADOW_LOG_PATH}")
        return []
    try:
        log = json.loads(SHADOW_LOG_PATH.read_text(encoding="utf-8"))
        return list(log.get("suggested_standards", []))
    except Exception as e:
        logger.warning(f"[learner] Impossible de lire le shadow log: {e}")
        return []


def _load_dev_test_events(all_events: list[dict]) -> list[dict]:
    """Filtre les events dev_test_run depuis la liste globale."""
    return [e for e in all_events if e.get("event_type") == "dev_test_run"]


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


def _file_type_from_path(file_path: str) -> str:
    norm = (file_path or "").replace("\\", "/")
    if norm.startswith("app/api/") and norm.endswith(".ts"):
        return "app/api/*.ts"
    if norm.startswith("app/") and norm.endswith(".tsx"):
        return "app/**/*.tsx"
    if norm.startswith("app/") and norm.endswith(".ts"):
        return "app/**/*.ts"
    if norm.endswith("schema.prisma"):
        return "prisma/schema.prisma"
    if "." in norm:
        return f"*.{norm.rsplit('.', 1)[-1]}"
    return "unknown"


def _zone_for_supervisor(supervisor_type: str) -> str:
    mapping = {
        "conformity": "ZONE_15",
        "security": "ZONE_16",
        "architecture": "ZONE_17",
    }
    return mapping.get(supervisor_type, "ZONE_15")


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


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


def _analyze_supervisor_patterns(all_events: list[dict]) -> list[StandardSuggestion]:
    """
    Analyse les événements `supervisor_file_reviewed`.
    Pattern récurrent = même superviseur corrige le même type de fichier
    sur 3+ runs consécutifs.
    """
    supervisor_events = [
        e for e in all_events
        if e.get("event_type") == "supervisor_file_reviewed"
    ]
    if not supervisor_events:
        return []

    run_order: list[str] = []
    seen_runs: set[str] = set()
    reviewed_counts: Counter = Counter()
    corrected_by_run: dict[tuple[str, str], set[str]] = {}
    confidence_samples: dict[tuple[str, str], list[float]] = {}

    for event in supervisor_events:
        run_id = str(event.get("run_id", "") or "")
        if not run_id:
            continue
        if run_id not in seen_runs:
            run_order.append(run_id)
            seen_runs.add(run_id)

        payload = event.get("payload", {}) or {}
        file_path = str(payload.get("file_path", "") or "")
        file_type = _file_type_from_path(file_path)
        results = payload.get("results", {}) or {}
        if not isinstance(results, dict):
            continue

        for supervisor, result in results.items():
            sup = str(supervisor or "").strip().lower()
            if not sup:
                continue
            key = (sup, file_type)
            reviewed_counts[key] += 1
            result = result if isinstance(result, dict) else {}
            conf = _as_float(result.get("confidence", 0.0))
            confidence_samples.setdefault(key, []).append(conf)
            fixed = bool(result.get("fix_applied", False))
            status = str(result.get("status", "") or "").lower()
            if fixed or status == "needs_fix":
                corrected_by_run.setdefault(key, set()).add(run_id)

    suggestions: list[StandardSuggestion] = []
    for key, corrected_runs in corrected_by_run.items():
        supervisor_type, file_type = key
        if len(corrected_runs) < 3:
            continue

        longest_streak = 0
        current_streak = 0
        current_runs: list[str] = []
        best_runs: list[str] = []
        for rid in run_order:
            if rid in corrected_runs:
                current_streak += 1
                current_runs.append(rid)
                if current_streak > longest_streak:
                    longest_streak = current_streak
                    best_runs = list(current_runs)
            else:
                current_streak = 0
                current_runs = []

        if longest_streak < 3:
            continue

        reviewed_total = int(reviewed_counts.get(key, 0) or 0)
        corrected_total = len(corrected_runs)
        confidence_ratio = (corrected_total / reviewed_total) if reviewed_total > 0 else 0.0
        confidence_value = max(0.0, min(1.0, round(confidence_ratio, 3)))

        avg_conf = 0.0
        samples = confidence_samples.get(key, [])
        if samples:
            avg_conf = round(sum(samples) / len(samples), 3)

        pattern = (
            f"Le superviseur '{supervisor_type}' corrige fréquemment le type de fichier "
            f"'{file_type}' sur des runs consécutifs."
        )
        suggestions.append(
            StandardSuggestion(
                suggestion_id=f"P008-{uuid.uuid4().hex[:6]}",
                category="standard",
                severity="medium",
                title=f"Pattern récurrent {supervisor_type} sur {file_type}",
                description=(
                    f"Corrections récurrentes détectées sur {longest_streak} runs consécutifs. "
                    "Candidat pour standard prescriptif en amont."
                ),
                evidence={
                    "run_ids": best_runs,
                    "corrected_runs_total": corrected_total,
                    "reviewed_files_total": reviewed_total,
                    "avg_supervisor_confidence": avg_conf,
                },
                supervisor_type=supervisor_type,
                file_type=file_type,
                pattern=pattern,
                zone_target=_zone_for_supervisor(supervisor_type),
                confidence=confidence_value,
                sprint="sprint46_v2",
            )
        )
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
