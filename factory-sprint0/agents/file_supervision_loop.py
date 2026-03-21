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

    # path → nombre de tentatives restantes (>0 = en attente de re-vérification)
    _pending: dict = field(default_factory=dict)
    # paths validés par les superviseurs (ok ou max tentatives atteintes)
    _validated: set = field(default_factory=set)
    # compteur de corrections appliquées
    corrections_count: int = 0

    def needs_reverification(self, path: str) -> bool:
        """Retourne True si ce fichier vient d'être réécrit et doit être re-supervisé."""
        return path in self._pending and self._pending[path] > 0

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
        """Appelé quand un fichier est réécrit — prêt pour re-supervision."""
        # Ne rien faire : needs_reverification() retournera True si path est dans _pending
        pass
