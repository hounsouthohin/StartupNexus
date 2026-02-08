# run/worker.py – tout en haut du fichier
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import threading
from queue import Queue
from flask import Flask, request, jsonify
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions
# Imports supplémentaires (en haut)
from workflows.todo_pilot_workflow import TodoPilotWorkflow
from workflows.activities.dev_test_activity import dev_test_activity

# Autorise logging et traceback à accéder à os.stat
sandbox_restrictions = SandboxRestrictions.default.with_passthrough_modules(
    ("logging", "traceback", "linecache", "warnings", "sys", "builtins")
)

from workflows.factory_workflow import SaaSFactoryWorkflow
from workflows.activities.architect_activity import architect_activity
from workflows.activities.dev_activity import dev_activity
from workflows.activities.github_activity import github_activity
from workflows.activities.test_coverage_activity import test_coverage_activity
from workflows.activities.qa_activity import qa_activity

# Queue thread-safe Flask → Temporal
job_queue = Queue()

app = Flask(__name__)

@app.route('/start-saas', methods=['POST'])
def start_saas():
    phrase = request.json.get('phrase', 'No phrase provided')
    job_queue.put({"phrase": phrase})
    return jsonify({
        "message": "Factory lancée – SaaS en cours de création",
        "suivi": "http://temporal-ui:8080"
    })

def run_flask():
    app.run(host="0.0.0.0", port=5000, use_reloader=False)

async def workflow_dispatcher(client):
    while True:
        input_data = await asyncio.to_thread(job_queue.get)
        phrase = input_data.get("phrase", "inconnu")
        print(f"[DISPATCH] Démarrage workflow pour : {phrase}")

        await client.start_workflow(
            SaaSFactoryWorkflow.run,
            input_data,
            id=f"saas-factory-{int(asyncio.get_running_loop().time())}",
            task_queue="factory-queue",
        )
        job_queue.task_done()

async def main():
    client = await Client.connect("temporal:7233")

    threading.Thread(target=run_flask, daemon=True).start()

    worker = Worker(
        client,
        task_queue="factory-queue",
        workflows=[SaaSFactoryWorkflow,TodoPilotWorkflow,],
        activities=[
            architect_activity,
            dev_test_activity,
            github_activity,
            test_coverage_activity,
            qa_activity,
        ],
        workflow_runner=SandboxedWorkflowRunner(restrictions=sandbox_restrictions),
    )
    print("Worker + API Flask démarrés – prêts 🚀")
    print("Test : POST http://localhost:5000/start-saas avec {'phrase': 'crée un SaaS de gestion de tâches'}")

    await asyncio.gather(
        worker.run(),
        workflow_dispatcher(client),
    )

if __name__ == "__main__":
    asyncio.run(main())