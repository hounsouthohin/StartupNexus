"""Essai de la boîte aux lettres sans session Claude : un répondeur automatique répond d'abord FAUX (pour vérifier que
le refus repart dans une nouvelle question avec l'erreur), puis JUSTE."""
import json, os, sys, tempfile, threading, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
boite = Path(tempfile.mkdtemp()) / "boite"
os.environ["USINE_BOITE"] = str(boite)
sys.path.insert(0, r"C:\Users\BAMBARA Arthur\Desktop\StartupNexus")
from pydantic import BaseModel
from usine.comprendre import ia

class Forme(BaseModel):
    couleur: str

def controle(o, ctx):
    return [] if o.couleur == "bleu" else [f"couleur « {o.couleur} » : il faut bleu"]

def repondeur():
    vus = set()
    while len(vus) < 2:
        for p in sorted((boite / "demandes").glob("*.json")) if (boite / "demandes").exists() else []:
            if p.name in vus:
                continue
            msgs = json.loads(p.read_text(encoding="utf-8"))["messages"]
            print(f"   [répondeur] {p.name} reçue : {len(msgs)} message(s), dernier : {msgs[-1]['content'][:60]!r}")
            (boite / "reponses" / p.name).write_text('{"couleur": "rouge"}' if not vus else '{"couleur": "bleu"}', encoding="utf-8")
            vus.add(p.name)
        time.sleep(0.5)

threading.Thread(target=repondeur, daemon=True).start()
journal = []
r = ia.demander(ia.client_pour("boite"), ia.Budget("boite", 2.0), "Réponds en JSON {couleur}.", {"q": "couleur ?"},
                Forme, controle, {}, journal)
print("réponse acceptée :", r, "| essais :", [(j["essai"], j["erreurs"]) for j in journal])
ia.fin_de_lot()
print("FIN déposé :", (boite / "FIN").exists())
