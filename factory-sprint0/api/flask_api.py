"""
api/flask_api.py
HTTP API pour déclencher les workflows Temporal depuis n8n ou curl.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime

from flask import Flask, jsonify, request
from temporalio.client import Client

# Assure les imports absolus du projet quand on lance "python api/flask_api.py"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.factory_config import TEMPORAL_ADDRESS
from workflows.factory_workflow import SaaSFactoryWorkflow

app = Flask(__name__)

TASK_QUEUE = "factory-task-queue"


async def _start_saas_workflow(phrase: str, project_name: str) -> dict:
    """Démarre un workflow SaaSFactory sur Temporal et retourne ses identifiants."""
    client = await Client.connect(TEMPORAL_ADDRESS)
    workflow_id = f"saas-{project_name}-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        SaaSFactoryWorkflow.run,
        {"phrase": phrase, "project_name": project_name},
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
    payload = request.get_json(silent=True) or {}
    phrase = str(payload.get("phrase", "")).strip()
    project_name = str(payload.get("project_name", "")).strip()

    if not phrase:
        return jsonify({"error": "Champ 'phrase' requis"}), 400

    if not project_name:
        project_name = f"saas-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    try:
        started = asyncio.run(_start_saas_workflow(phrase, project_name))
        return (
            jsonify(
                {
                    "message": "Workflow démarré",
                    "project_name": project_name,
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
