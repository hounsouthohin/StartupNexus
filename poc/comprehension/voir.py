"""Affiche, sous une forme compacte et toujours la même, ce que les agents ont compris d'un brief
(pour le juger contre references.yaml). Usage : python voir.py <modèle> <projet> [v2-passe1]"""
import json
import sys
from pathlib import Path

model, name = sys.argv[1], sys.argv[2]
sub = sys.argv[3] if len(sys.argv) > 3 else ""
r = json.loads((Path(__file__).parent / "sorties" / model / sub / f"{name}.json").read_text(encoding="utf-8"))
p = r.get("perimetre") or {}
print(f"■ {name} [{model}] — périmètre : {p.get('perimetre')} — {p.get('raison', '')[:160]}")
for h in p.get("hors_stock", []):
    print(f"   hors stock · {h['categorie']:<19} {h['besoin']}")
if r.get("echec"):
    print("   ÉCHEC :", r["echec"])
for a in (r.get("acteurs") or {}).get("acteurs", []):
    print(f"   acteur  {a['id']:<16} {a['devient']:<9} {a.get('invite_par') or ''}  « {a['citation'][:70]} »")
print("   non-utilisateurs :", [n["libelle"] for n in (r.get("acteurs") or {}).get("non_utilisateurs", [])])
for f in (r.get("fiches") or {}).get("fiches", []):
    who = f["proprietaire"] or (",".join(f["gestionnaires"]) if f["gestionnaires"] else "")
    extra = " ".join(x for x in [f"parent={f['parent']}" if f["parent"] else "", "PUBLIC" if f["publique"] else "",
                                   f"saisie_par={f['saisie_par']}" if f["saisie_par"] else "",
                                   f"refs={f['references']}" if f["references"] else ""] if x)
    print(f"   fiche   {f['nom']:<22} {f['nature']:<10} {who:<22} {extra}")
for c in (r.get("circuits") or {}).get("circuits", []):
    print(f"   circuit {c['fiche']:<22} {c['transitions']}  lance={c['initiateur']} décide={c['decideur']} étapes={c['etapes_par']}")
for d in (r.get("droits") or {}).get("droits", []):
    print(f"   droit   {d['acteur']}/{d['fiche']}/{d['action']} {'permis' if d['autorise'] else 'INTERDIT'} {d['portee']}  « {d['citation'][:60]} »")
if r.get("circuits_hors_vocabulaire_D1"):
    print("   circuits hors vocabulaire D1 :", r["circuits_hors_vocabulaire_D1"])
for a in r.get("matrice_alertes", []):
    print("   alerte :", a)
for e in r.get("matrice_erreurs", []):
    print("   ERREUR MATRICE :", e)
for actor, lines in (r.get("miroir") or {}).items():
    for line in lines:
        print(f"   miroir  {actor} {line}")
refus = [(x["agent"], x["essai"]) for x in r.get("journal", []) if x["erreurs"]]
print(f"   réponses refusées puis corrigées : {refus or 'aucune'}")
if r.get("droits_revus_apres_alerte"):
    print("   droits revus après alerte :", r["droits_revus_apres_alerte"])
for c in (r.get("fiches") or {}).get("correspondances", []):
    print(f"   correspondance {c['non_utilisateur']} → {c['fiche']}  ({c['raison'][:60]})")
if r.get("jetons"):
    print("   jetons :", r["jetons"])
