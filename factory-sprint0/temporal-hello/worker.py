import asyncio
import threading
from queue import Queue
from flask import Flask, request, jsonify
from temporalio.client import Client
from temporalio.worker import Worker
from workflow import HelloWorkflow

# Queue thread-safe pour passer les jobs Flask → Worker asyncio
job_queue = Queue()

app = Flask(__name__)

@app.route('/start-saas', methods=['POST'])
def start_saas():
    phrase = request.json.get('phrase', 'No phrase')

    # On push la tâche dans la queue
    job_queue.put(phrase)

    return jsonify({
        "message": "SaaS en cours de création",
        "suivi": "http://localhost:8080"
    })


# -------------------------------
# THREAD Flask
# -------------------------------
def run_flask():
    app.run(host="0.0.0.0", port=5000)


# -------------------------------
# ASYNC WORKER + CONSO QUEUE
# -------------------------------
async def workflow_dispatcher(client):
    """Lit la queue Flask et démarre les workflows"""
    while True:
        phrase = await asyncio.to_thread(job_queue.get)
        print(f"[DISPATCH] Démarrage workflow pour : {phrase}")

        await client.start_workflow(
            HelloWorkflow.run,
            phrase,
            id=f"saas-{int(asyncio.get_event_loop().time())}",
            task_queue="hello-queue",
        )


async def main():
    # Connexion Temporal
    client = await Client.connect("localhost:7233")

    # Démarrage Flask dans un thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Worker
    worker = Worker(
        client,
        task_queue="hello-queue",
        workflows=[HelloWorkflow],
    )

    print("Worker + API Flask démarrés – prêts 🚀")

    # Lancer workflow dispatcher en parallèle
    await asyncio.gather(
        worker.run(),
        workflow_dispatcher(client),
    )


if __name__ == "__main__":
    asyncio.run(main())
