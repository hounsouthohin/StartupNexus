"""
api/flask_api.py
HTTP API pour déclencher les workflows Temporal depuis n8n ou curl.
"""

import asyncio
import os
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime

from flask import Flask, jsonify, request
from temporalio.client import Client

# Assure les imports absolus du projet quand on lance "python api/flask_api.py"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.factory_config import TEMPORAL_ADDRESS
from agents.stack_config import _DEFAULT_STACK_ID
from workflows.factory_workflow import SaaSFactoryWorkflow

app = Flask(__name__)

TASK_QUEUE = "factory-task-queue"

# ── Sécurité ────────────────────────────────────────────────────────────────
_API_KEY = os.getenv("FACTORY_API_KEY", "")  # vide = désactivé (dev local)
_PROJECT_NAME_RE = re.compile(r'^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$')

# Rate-limit simple en mémoire: max 10 requêtes / 60s par IP
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX = 10
_rate_buckets: dict = defaultdict(list)  # ip → [timestamps]


def _check_api_key() -> bool:
    """Retourne True si la clé est valide (ou si la vérification est désactivée)."""
    if not _API_KEY:
        return True
    return request.headers.get("X-API-Key", "") == _API_KEY


def _check_rate_limit(ip: str) -> bool:
    """Retourne True si la requête est autorisée (fenêtre glissante)."""
    now = time.monotonic()
    bucket = _rate_buckets[ip]
    _rate_buckets[ip] = [t for t in bucket if now - t < _RATE_LIMIT_WINDOW]
    if len(_rate_buckets[ip]) >= _RATE_LIMIT_MAX:
        return False
    _rate_buckets[ip].append(now)
    return True


async def _start_saas_workflow(phrase: str, project_name: str, stack_id: str) -> dict:
    """Démarre un workflow SaaSFactory sur Temporal et retourne ses identifiants."""
    client = await Client.connect(TEMPORAL_ADDRESS)
    workflow_id = f"saas-{project_name}-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        SaaSFactoryWorkflow.run,
        {"phrase": phrase, "project_name": project_name, "stack_id": stack_id},
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    return {"workflow_id": handle.id, "run_id": handle.result_run_id}


@app.get("/status")
def status() -> tuple:
    return jsonify(
        {
            "status": "ok",
            "service": "factory-api",
            "temporal_address": TEMPORAL_ADDRESS,
            "task_queue": TASK_QUEUE,
        }
    ), 200


@app.post("/start-saas")
def start_saas() -> tuple:
    if not _check_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    ip = request.remote_addr or "unknown"
    if not _check_rate_limit(ip):
        return jsonify({"error": "Rate limit exceeded — max 10 req/60s"}), 429

    payload = request.get_json(silent=True) or {}
    phrase = str(payload.get("phrase", "")).strip()
    project_name = str(payload.get("project_name", "")).strip()
    stack_id = str(payload.get("stack_id", "")).strip() or _DEFAULT_STACK_ID

    if not phrase:
        return jsonify({"error": "Champ 'phrase' requis"}), 400

    if not project_name:
        project_name = f"saas-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    if not _PROJECT_NAME_RE.match(project_name):
        return jsonify({"error": "project_name invalide — format requis: ^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$"}), 400

    try:
        started = asyncio.run(_start_saas_workflow(phrase, project_name, stack_id))
        return (
            jsonify(
                {
                    "message": "Workflow démarré",
                    "project_name": project_name,
                    "stack_id": stack_id,
                    "workflow_id": started["workflow_id"],
                    "run_id": started["run_id"],
                }
            ),
            202,
        )
    except Exception as e:
        return jsonify({"error": f"Impossible de démarrer le workflow: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
