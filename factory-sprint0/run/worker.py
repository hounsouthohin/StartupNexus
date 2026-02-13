"""
run/worker.py
Worker Temporal — Software Agent Factory
Enregistre tous les workflows et activities.
"""

import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

# Workflows
from workflows.factory_workflow import SaaSFactoryWorkflow
from workflows.todo_pilot_workflow import TodoPilotWorkflow

# Activities (Import pass-through recommandé pour Temporal)
with Worker.with_import_pass_through():
    from workflows.activities.architect_activity import architect_activity
    from workflows.activities.dev_test_activity import dev_test_activity
    from workflows.activities.qa_activity import qa_activity
    from workflows.activities.github_activity import github_activity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TASK_QUEUE = "factory-task-queue"

async def main():
    # Connexion au serveur Temporal local (Docker par défaut)
    client = await Client.connect("localhost:7233")
    
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            SaaSFactoryWorkflow,
            TodoPilotWorkflow,
        ],
        activities=[
            architect_activity,
            dev_test_activity,
            qa_activity,
            github_activity,
        ],
    )
    
    logger.info(f"🚀 Worker démarré sur queue '{TASK_QUEUE}'")
    logger.info("✅ Workflows enregistrés: SaaSFactoryWorkflow, TodoPilotWorkflow")
    logger.info("✅ Activities enregistrées: architect, dev_test, qa, github")
    
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker arrêté par l'utilisateur.")