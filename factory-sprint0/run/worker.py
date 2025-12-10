import asyncio
import threading
from queue import Queue
from flask import Flask, request, jsonify
from temporalio.client import Client
from temporalio.worker import Worker

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # ← FIX CHEMIN

from workflows.factory_workflow import SaaSFactoryWorkflow # ← maintenant OK
from workflows.activities.architect_activity import architect_activity

# Queue thread-safe Flask → Temporal
job_queue = Queue()

app = Flask(__name__)

@app.route('/start-saas', methods=['POST'])
def start_saas():
    phrase = request.json.get('phrase', 'No phrase provided')
    job_queue.put({"phrase": phrase})

    return jsonify({
        "message": "Factory lancée – SaaS en cours de création",
        "suivi": "http://localhost:8080"
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
    client = await Client.connect("localhost:7233")

    threading.Thread(target=run_flask, daemon=True).start()

    worker = Worker(
    client,
    task_queue="factory-queue",
    workflows=[SaaSFactoryWorkflow],
    activities=[architect_activity],  
)
    print("Worker + API Flask démarrés – prêts 🚀")
    print("Test : POST http://localhost:5000/start-saas avec {'phrase': 'crée un SaaS de gestion de tâches'}")

    await asyncio.gather(
        worker.run(),
        workflow_dispatcher(client),
    )

if __name__ == "__main__":
    asyncio.run(main())