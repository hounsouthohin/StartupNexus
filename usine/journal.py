"""Le journal de fabrication : chaque étape écrit un événement (résultat, durée) — affiché dans le
terminal et conservé dans runs/<n°>/journal.jsonl (la future page de suivi le lira)."""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path


class Journal:
    def __init__(self, dossier: Path, total: int):
        self.fichier = dossier / "journal.jsonl"
        self.total = total
        self.n = 0
        self.debut = time.time()

    def _ecrire(self, evenement: dict) -> None:
        with self.fichier.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evenement, ensure_ascii=False) + "\n")

    @contextmanager
    def etape(self, nom: str):
        """with journal.etape("Traduire") as e: ... ; e["resume"] = "21 règles" """
        self.n += 1
        info = {"etape": nom, "numero": self.n, "resume": ""}
        print(f"▶ [{self.n}/{self.total}] {nom} …", flush=True)
        t0 = time.time()
        self._ecrire({**info, "statut": "debut", "t": round(t0 - self.debut, 2)})
        try:
            yield info
        except Exception as exc:
            duree = round(time.time() - t0, 1)
            self._ecrire({**info, "statut": "echec", "duree": duree, "erreur": str(exc)[:2000]})
            print(f"  ✗ échec après {duree} s : {str(exc)[:500]}", flush=True)
            raise
        duree = round(time.time() - t0, 1)
        self._ecrire({**info, "statut": "fait", "duree": duree})
        print(f"  ✓ {duree} s — {info['resume']}", flush=True)
