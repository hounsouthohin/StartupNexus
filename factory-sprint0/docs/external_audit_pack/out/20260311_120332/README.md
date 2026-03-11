# External Audit Pack

Ce dossier contient le cadre pour faire valider la source de vérité de la stack par un expert externe (humain ou IA), sans connaissance du projet interne.

## Objectif

Valider que la stack `nextjs-clerk-prisma` est conforme aux bonnes pratiques officielles et cohérente entre:

- stack config
- templates
- prompts
- contracts
- standards

## Contenu

- `AUDIT_CHECKLIST.md`: grille d'audit externe
- `REQUEST_TEMPLATE.md`: prompt/cadre a envoyer a l'externe
- `pack_manifest.txt`: liste des fichiers a inclure
- `build_pack.ps1`: script pour generer un pack partageable

## Standards: oui, ils sont inclus

Le pack inclut les standards via:

- `scripts/pending_prescriptive_standards.json`
- `scripts/create_full_standards_v1.py`
- `scripts/enrich_qdrant.py`
- `scripts/tag_qdrant_standards.py`

Si tu veux un export direct de Qdrant en JSON, ajoute un script dedie (optionnel) puis ajoute ce fichier au manifeste.

## Utilisation

Depuis `factory-sprint0`:

```powershell
powershell -ExecutionPolicy Bypass -File docs/external_audit_pack/build_pack.ps1
```

Le pack sera cree dans `docs/external_audit_pack/out/<timestamp>`.
