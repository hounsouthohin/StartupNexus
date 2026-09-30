#!/bin/bash
# scripts/start.sh — Démarrage factory-worker
# BrowserUse tourne en headless — plus besoin de Xvfb/noVNC.
# Le live viewer QA est sur http://localhost:5001 (WebSocket screenshots).
set -e

echo "[START] Attente du service Temporal..."
python scripts/wait-for-it.py temporal:7233 120

echo "[START] Démarrage du factory worker..."
echo "[START] QA Live viewer disponible pendant les runs → http://localhost:5001"
exec python run/worker.py
