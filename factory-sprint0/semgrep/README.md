# Semgrep Rules

Ce dossier contient les règles Semgrep versionnées utilisées pour les guards P3.

Fichier principal:
- `rules/critical.yml`

Usage (dans le conteneur `factory-worker`):
```bash
semgrep --config /app/semgrep/rules/critical.yml app/
```

Variables d'environnement (docker-compose):
- `SEMGREP_RULES_PATH=/app/semgrep/rules/critical.yml`
- `SEMGREP_TIMEOUT=30`

