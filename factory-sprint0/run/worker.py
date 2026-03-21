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

# Imports — pipeline principal
from workflows.factory_workflow import SaaSFactoryWorkflow
from workflows.todo_pilot_workflow import TodoPilotWorkflow

from workflows.activities.architect_activity import architect_activity
from workflows.activities.dev_test_activity import dev_test_activity
from workflows.activities.qa_activity import qa_activity
from workflows.activities.github_activity import github_activity
from workflows.activities.learner_activity import learner_activity
# Sprint 4.6 — superviseurs inline
from workflows.activities.conformity_activity import conformity_activity
from workflows.activities.security_activity import security_activity
from workflows.activities.architecture_activity import architecture_activity
from workflows.activities.build_supervisor_activity import build_supervisor_activity
# M2 — workflow parallèle + stubs activités
from workflows.generation_session_workflow import GenerationSessionWorkflow
from workflows.activities.generation_session_activities import (
    generate_batch_activity,
    aggregate_corrections_activity,
    apply_corrections_activity,
    build_activity,
)

from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-22s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

# Queues
MAIN_QUEUE       = "factory-task-queue"       # backward compat — toutes activités existantes
DEV_QUEUE        = "factory-dev-queue"         # M2 — génération + application corrections
SUPERVISORS_QUEUE = "factory-supervisors-queue" # M2 — conformity / security / architecture
BUILD_QUEUE      = "factory-build-queue"        # M2 — build + build_supervisor


async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)

    # ── Worker principal (backward compat M0/M1) ─────────────────────────────
    main_worker = Worker(
        client,
        task_queue=MAIN_QUEUE,
        workflows=[
            SaaSFactoryWorkflow,
            TodoPilotWorkflow,
            GenerationSessionWorkflow,   # M2 — enregistré ici pour le routing TodoPilot
        ],
        activities=[
            architect_activity,
            dev_test_activity,
            qa_activity,
            github_activity,
            learner_activity,
            conformity_activity,
            security_activity,
            architecture_activity,
            build_supervisor_activity,
        ],
    )

    # ── Worker dev queue (M2) ─────────────────────────────────────────────────
    dev_worker = Worker(
        client,
        task_queue=DEV_QUEUE,
        activities=[
            generate_batch_activity,
            apply_corrections_activity,
        ],
    )

    # ── Worker supervisors queue (M2) ─────────────────────────────────────────
    supervisors_worker = Worker(
        client,
        task_queue=SUPERVISORS_QUEUE,
        activities=[
            conformity_activity,
            security_activity,
            architecture_activity,
            aggregate_corrections_activity,
        ],
    )

    # ── Worker build queue (M2) ───────────────────────────────────────────────
    build_worker = Worker(
        client,
        task_queue=BUILD_QUEUE,
        activities=[
            build_activity,
            build_supervisor_activity,
        ],
    )

    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║     Software Agent Factory Worker                      ║")
    logger.info("║     Queues : main | dev | supervisors | build          ║")
    logger.info("╚════════════════════════════════════════════════════════╝")
    logger.info(f"MAIN       ({MAIN_QUEUE})       : pipeline principal + backward compat")
    logger.info(f"DEV        ({DEV_QUEUE})          : generate_batch + apply_corrections")
    logger.info(f"SUPERVISORS({SUPERVISORS_QUEUE}) : conformity + security + architecture")
    logger.info(f"BUILD      ({BUILD_QUEUE})        : build + build_supervisor")
    logger.info("Workers en écoute... (Ctrl+C pour arrêter)")

    await asyncio.gather(
        main_worker.run(),
        dev_worker.run(),
        supervisors_worker.run(),
        build_worker.run(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Workers arrêtés proprement (Ctrl+C)")
    except Exception as e:
        logger.exception("Erreur critique dans le worker")
        sys.exit(1)
