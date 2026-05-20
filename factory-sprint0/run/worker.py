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

from workflows.factory_workflow import SaaSFactoryWorkflow
from workflows.todo_pilot_workflow import TodoPilotWorkflow

from workflows.activities.architect_activity import architect_activity
from workflows.activities.dev_test_activity import dev_test_activity
from workflows.activities.review_activity import review_activity
from workflows.activities.correction_pass_activity import correction_pass_activity
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

MAIN_QUEUE = "factory-task-queue"


async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)

    worker = Worker(
        client,
        task_queue=MAIN_QUEUE,
        workflows=[
            SaaSFactoryWorkflow,
            TodoPilotWorkflow,
        ],
        activities=[
            architect_activity,
            dev_test_activity,
            review_activity,
            correction_pass_activity,
            qa_activity,
            github_activity,
            learner_activity,
        ],
    )

    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║     Software Agent Factory Worker                      ║")
    logger.info("╚════════════════════════════════════════════════════════╝")
    logger.info(f"Queue : {MAIN_QUEUE}")
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
