# Harnais

Filet de sécurité du cœur déterministe (voir `USINE.md`, phase 1).

- `declarations/<projet>.json` : déclarations étalons (brief + ProjectSpec complet produit par
  l'architect). Capturées avec `scripts/capture_declarations.py`, jamais remplacées sans `--force`.
- `references/<projet>/` : les fichiers que les générateurs produisent pour cette déclaration,
  acceptés comme référence (`scripts/harness.py --update`). Un `git diff` de ce dossier montre
  exactement ce qu'une modification de générateur change dans les apps.

Commandes (dans le conteneur) :

```
docker exec factory-worker python scripts/capture_declarations.py --briefs scripts/<fichier>.json
docker exec factory-worker python scripts/harness.py            # génération + comparaison + tsc
docker exec factory-worker python scripts/harness.py --no-tsc   # sans tsc (rapide)
docker exec factory-worker python scripts/harness.py --update   # accepter la génération actuelle
```

Chaque passage est enregistré dans `logs/harness/`.
