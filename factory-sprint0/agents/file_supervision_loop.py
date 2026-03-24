"""
FileSupervisionLoop — Boucle de correction per-fichier superviseurs.

Responsabilité :
- Tracker quelles fichiers ont des corrections superviseurs en attente
- Décider si un fichier doit être re-supervisé (il vient d'être réécrit après correction)
- Bloquer le build si des corrections sont encore pendantes
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAX_CORRECTION_ATTEMPTS_DEFAULT = 2


@dataclass
class FileSupervisionLoop:
    max_attempts: int = MAX_CORRECTION_ATTEMPTS_DEFAULT

    # path → nombre de tentatives restantes (>0 = correction en attente de re-vérification)
    _pending: dict = field(default_factory=dict)
    # paths validés par les superviseurs (ok ou max tentatives atteintes)
    _validated: set = field(default_factory=set)
    # paths réécrit sur disque et en attente de re-supervision (armés par reset_file)
    _needs_reverify: set = field(default_factory=set)
    # compteur de corrections appliquées (injections LLM)
    corrections_count: int = 0
    # compteur de re-vérifications déclenchées (fichier réécrit puis re-supervisé)
    reverifications_count: int = 0

    def needs_reverification(self, path: str) -> bool:
        """
        Retourne True si ce fichier vient d'être réécrit sur disque après une correction
        et doit être re-supervisé avant de continuer.
        Incrémente reverifications_count au premier appel pour ce path (comptage unique par réécriture).
        """
        if path in self._needs_reverify:
            self._needs_reverify.discard(path)
            self.reverifications_count += 1
            return True
        return False

    def on_supervisor_ok(self, path: str) -> None:
        """Fichier validé — retirer des pending."""
        self._pending.pop(path, None)
        self._validated.add(path)

    def on_supervisor_needs_fix(self, path: str) -> bool:
        """
        Fichier nécessite une correction.
        Retourne True si la correction doit être injectée (tentatives restantes).
        Retourne False si le max est atteint (on valide quand même pour ne pas bloquer).
        """
        remaining = self._pending.get(path, self.max_attempts)
        if remaining <= 0:
            # Max atteint — on valide malgré tout (best-effort)
            self._pending.pop(path, None)
            self._validated.add(path)
            logger.warning(f"[supervision_loop] {path}: max tentatives atteintes — validé best-effort")
            return False
        self._pending[path] = remaining - 1
        self.corrections_count += 1
        return True

    def has_pending_corrections(self) -> bool:
        """True si des fichiers ont encore des corrections en attente."""
        return bool(self._pending)

    def pending_paths(self) -> list:
        return list(self._pending.keys())

    def reset_file(self, path: str) -> None:
        """
        Appelé à chaque réécriture confirmée sur disque (write_file succès).
        - Si le fichier avait une correction en attente (_pending) : marquer pour re-supervision.
        - Si le fichier était validé best-effort (_validated) : re-armer pour supervision.
        - Si le fichier est nouveau (jamais supervisé) : pas d'action nécessaire.
        """
        if path in self._pending:
            # Correction injectée + fichier réécrit → re-supervision obligatoire
            self._needs_reverify.add(path)
            logger.debug(f"[supervision_loop] {path}: réécrit après correction — armé pour re-supervision")
        elif path in self._validated:
            # Fichier réécrit après validation best-effort → re-armer avec max tentatives
            self._validated.discard(path)
            self._pending[path] = self.max_attempts
            self._needs_reverify.add(path)
            logger.debug(f"[supervision_loop] {path}: réécrit après validation — re-armé ({self.max_attempts} tentatives)")
