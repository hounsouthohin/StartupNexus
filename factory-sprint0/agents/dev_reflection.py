"""
dev_reflection.py — Gestion du résumé de progression et du brief d'itération.

Extraite de dev.py (progress_summary dict + _update_progress_summary
+ _build_progress_summary_text + _build_iteration_brief) pour alléger dev_agent().

ProgressSummary est un objet mutable mis à jour à chaque itération de la boucle LLM.
build_iteration_brief() génère le texte injecté comme contexte à chaque tour.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProgressSummary:
    """
    Résumé de progression de la boucle LLM, mis à jour après chaque itération.
    Injecté dans le brief d'itération pour aider le LLM à se situer.
    """
    what_done: list[str] = field(default_factory=list)
    what_missing: list[str] = field(default_factory=list)
    next_action: str = "Démarrer par l'objectif actif"

    def update(self, state: dict) -> None:
        unmet = state.get("requirements_unmet", [])
        missing_files = state.get("missing_required_files", [])
        met = state.get("requirements_met", 0)
        total = state.get("requirements_total", 0)

        done = [f"requirements_couverts={met}/{total}"]
        if not unmet:
            done.append("requirements_mappables_couverts")
        self.what_done = done

        missing = []
        if unmet:
            missing.append(f"requirement: {unmet[0]}")
        if missing_files:
            missing.append(f"fichier: {missing_files[0]}")
        if state.get("last_build_error_excerpt"):
            missing.append("corriger dernière erreur build")
        self.what_missing = missing or ["aucun blocage détecté"]

        self.next_action = (
            "appeler run_build"
            if state.get("active_blocker") == "ready_for_build"
            else f"corriger {state.get('active_blocker')}"
        )

    def as_text(self) -> str:
        return (
            "SUMMARY LOOP:\n"
            f"- DONE: {' | '.join(self.what_done)}\n"
            f"- MISSING: {' | '.join(self.what_missing)}\n"
            f"- NEXT: {self.next_action}"
        )


def build_iteration_brief(
    state: dict,
    progress: ProgressSummary,
    stack_cfg: dict,
) -> str:
    """
    Génère le texte FOCUS LOOP injecté à chaque itération.
    Contient l'objectif prioritaire, les requirements non couverts,
    les fichiers manquants, les erreurs build, et les instructions de correction.
    """
    unmet = state.get("requirements_unmet", [])
    missing_files = state.get("missing_required_files", [])
    objective = state.get("active_blocker", "ready_for_build")
    statuses = state.get("requirements_statuses", [])

    first_unmet_reason = ""
    for s in statuses:
        if s.get("is_mappable") and not s.get("satisfied"):
            first_unmet_reason = s.get("reason", "")
            break

    lines = [
        "FOCUS LOOP (itération courante) — travaille sur UNE priorité à la fois.",
        f"OBJECTIF UNIQUE: {objective}",
        f"REQUIREMENTS: {state.get('requirements_met', 0)}/{state.get('requirements_total', 0)} couverts",
    ]

    if unmet:
        lines.append("REQUIREMENT PRIORITAIRE NON COUVERT:")
        lines.append(f"- {unmet[0]}")
        if first_unmet_reason:
            lines.append(f"- DÉTAIL: {first_unmet_reason}")

    if missing_files:
        lines.append("FICHIER REQUIS PRIORITAIRE MANQUANT:")
        lines.append(f"- {missing_files[0]}")

    if objective.startswith("structural::"):
        guard_id = state.get("structural_blocking_guard_id", "")
        targets = state.get("structural_targets", []) or []
        lines.append(f"GUARD STRUCTUREL BLOQUANT: {guard_id}")
        if targets:
            lines.append("FICHIERS À CORRIGER (OBLIGATOIRE avant tout autre écriture):")
            for p in targets[:3]:
                lines.append(f"- {p}")
        guard_cfg = next(
            (g for g in stack_cfg.get("content_guards", []) if g.get("id") == guard_id),
            None,
        )
        if guard_cfg:
            msg_lines = guard_cfg.get("message_lines", [])
            if msg_lines:
                lines.append("INSTRUCTIONS DE CORRECTION:")
                for ml in msg_lines:
                    if ml == "{details}":
                        for p in targets[:3]:
                            lines.append(f"  - {p}")
                    else:
                        lines.append(ml)

    err = state.get("last_build_error_excerpt", "")
    if err:
        lines.append("DERNIÈRE ERREUR BUILD (extrait):")
        lines.append(err)

    lines.append(
        "ACTION: corrige les fichiers listés ci-dessus en priorité absolue, puis valide par run_build."
    )
    lines.append(progress.as_text())
    return "\n".join(lines)
