from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
import asyncio


# --------------------------
# WORKFLOW
# --------------------------
@workflow.defn
class HelloWorkflow:
    @workflow.run
    async def run(self, input_data: dict) -> str:   # ← ON PASSE UN DICT POUR PLUS DE CLARTÉ
        name = input_data.get("name", "Inconnu")   # ← robuste
        #NB :Temporal
        #print(f"Workflow démarré pour : {name}")
        workflow.logger.info(f"Workflow démarré pour la phrase : {name}")

        result = await workflow.execute_activity(
            sleepy_activity,
            name,
            start_to_close_timeout=timedelta(seconds=300),
            retry_policy=RetryPolicy(maximum_attempts=100),
            heartbeat_timeout=timedelta(seconds=60),
        )

        return f"Workflow terminé : {result}"


# --------------------------
# ACTIVITY (indestructible avec heartbeat)
# --------------------------


@activity.defn
async def sleepy_activity(name: str) -> str:    
    info = activity.info()
    details = info.heartbeat_details or []

    last = 0
    if details:
        try:
            last = int(details[-1])
        except (ValueError, TypeError):
            last = 0

    activity.logger.info(f"Activité pour {name} — reprise à {last}/120 secondes")

    for i in range(last, 120):
        await asyncio.sleep(1)
        activity.heartbeat(i + 1)
        activity.logger.info(f"  → {i + 1}/120 secondes…")

    return f"Bonjour {name}, j’ai terminé mon sommeil de 120 secondes !"