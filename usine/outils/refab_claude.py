"""Refabrique (0 $, sans la session isolée) une app à partir d'une lecture Claude déjà faite, avec les juges actuels.
Usage : python usine/outils/refab_claude.py <brief> <dossier …-claude-comprendre>
Exemple : python usine/outils/refab_claude.py c2-portes-interventions 20261013-143203-c2-portes-interventions-claude-comprendre"""
import json, sys
from datetime import datetime
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from usine.repetition import RUNS, fabriquer_depuis

brief, comp = sys.argv[1], sys.argv[2]
dossier = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-repetition-claude-refab"
dossier.mkdir(parents=True)
ligne = fabriquer_depuis(RUNS / comp, brief, "dans", dossier, client_simule=True)
(dossier / "repetition.json").write_text(json.dumps([ligne], ensure_ascii=False, indent=2), encoding="utf-8")
x = ligne.get("essai") or ligne.get("variante") or {}
print("RÉSULTAT :", brief, "|", x.get("etape"), x.get("regles", ""), x.get("ecrans", ""))
