#!/bin/bash
# scripts/start.sh — Démarrage factory-worker
# BrowserUse tourne en headless — plus besoin de Xvfb/noVNC.
# Le live viewer QA est sur http://localhost:5001 (WebSocket screenshots).
set -e

echo "[START] Attente des services Temporal et Qdrant..."
python scripts/wait-for-it.py qdrant:6333 120
python init_qdrant.py
python scripts/wait-for-it.py temporal:7233 120

echo "[START] Démarrage Flask API en arrière-plan..."
python api/flask_api.py &

echo "[START] Démarrage du factory worker..."
echo "[START] QA Live viewer disponible pendant les runs → http://localhost:5001"
exec python run/worker.py
