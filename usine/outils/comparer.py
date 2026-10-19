"""Compare deux photos (avant / après). Dans la matrice, les champs AJOUTÉS par la restructuration (create_while,
owner_links, own_choice_links) sont listés à part ; le texte des explications (why/sources) est comparé comme ensemble."""
import json, sys, difflib
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
A, B = Path(sys.argv[1]), Path(sys.argv[2])
NOUVEAUX = {"create_while", "owner_links", "own_choice_links"}
diffs, ajouts = 0, []
for app in sorted(p.name for p in A.iterdir()):
    for f in sorted(p.name for p in (A / app).iterdir()):
        a, b = (A / app / f).read_text(encoding="utf-8"), (B / app / f).read_text(encoding="utf-8") if (B / app / f).exists() else None
        if b is None:
            print(f"MANQUE {app}/{f}"); diffs += 1; continue
        if f == "matrice.json":
            ma, mb = json.loads(a), json.loads(b)
            for k in NOUVEAUX:
                if mb.get(k):
                    ajouts.append(f"{app} : {k} = {mb[k]}")
                mb.pop(k, None)
            for c in mb["cells"]:
                if c.get("create_while"):
                    ajouts.append(f"{app} : {c['actor']}/{c['entity']} create_while = {c['create_while']}")
                c.pop("create_while", None)
            for m in (ma, mb):
                for c in m["cells"]:
                    c["why"], c["sources"] = sorted(set(c["why"])), sorted(set(c["sources"]))
                m["issues"] = sorted(i["message"].split("] ", 1)[-1] for i in m["issues"])   # sans le code de refus
            a, b = json.dumps(ma, ensure_ascii=False, indent=1, sort_keys=True), json.dumps(mb, ensure_ascii=False, indent=1, sort_keys=True)
        if f == "variante.txt":
            a, b = a.replace("[bloc:", "").replace("[limite:", ""), b.replace("[bloc:", "").replace("[limite:", "")
        if a != b:
            diffs += 1
            print(f"=== DIFFÉRENCE {app}/{f}")
            for l in list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0))[2:14]:
                print("   ", l[:200])
print(f"\n{diffs} fichier(s) différent(s) ; {len(ajouts)} ajout(s) attendu(s) :")
for x in ajouts[:40]:
    print("  +", x[:180])
