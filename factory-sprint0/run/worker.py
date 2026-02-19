"""
run/worker.py
Worker Temporal pour la Software Agent Factory
"""

import asyncio
import logging
import os
import sys

# Force le chemin racine du projet
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Imports
from workflows.factory_workflow import SaaSFactoryWorkflow
from workflows.todo_pilot_workflow import TodoPilotWorkflow

from workflows.activities.architect_activity import architect_activity
from workflows.activities.dev_test_activity import dev_test_activity
from workflows.activities.qa_activity import qa_activity
from workflows.activities.github_activity import github_activity
from workflows.activities.learner_activity import learner_activity

from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-22s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

TASK_QUEUE = "factory-task-queue"


async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)
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
            learner_activity,
        ],
    )

    logger.info("╔════════════════════════════════════════════╗")
    logger.info("║     Software Agent Factory Worker          ║")
    logger.info("║     Queue : factory-task-queue             ║")
    logger.info("╚════════════════════════════════════════════╝")

    # Logging statique (pas d'accès aux attributs internes)
    logger.info(f"Workflows   : {', '.join(w.__name__ for w in [SaaSFactoryWorkflow, TodoPilotWorkflow])}")
    logger.info(f"Activities  : {', '.join(a.__name__ for a in [architect_activity, dev_test_activity, qa_activity, github_activity, learner_activity])}")

    logger.info("Worker en écoute... (Ctrl+C pour arrêter)")
    
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker arrêté proprement (Ctrl+C)")
    except Exception as e:
        logger.exception("Erreur critique dans le worker")
        sys.exit(1)
