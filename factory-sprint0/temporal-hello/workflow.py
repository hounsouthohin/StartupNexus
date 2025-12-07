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
    async def run(self, name: str) -> str:
        print(f"Workflow démarré pour {name}")

        result = await workflow.execute_activity(
            sleepy_activity,
            name,
            start_to_close_timeout=timedelta(seconds=300),
            retry_policy=RetryPolicy(maximum_attempts=100),
            heartbeat_timeout=timedelta(seconds=60),
        )

        return f"Workflow terminé : {result}"


# --------------------------
# ACTIVITY (correcte)
# --------------------------



@activity.defn
async def sleepy_activity(name: str) -> str:
    # Récupération robuste du dernier heartbeat
    info = activity.info()
    raw = info.heartbeat_details  # peut être None, int, list, etc.

    # Normaliser raw en entier
    last = 0
    if raw is None:
        last = 0
    elif isinstance(raw, list):
        # si c'est une liste, prendre le dernier élément (ou le premier)
        if len(raw) == 0:
            last = 0
        else:
            candidate = raw[-1]
            try:
                last = int(candidate)
            except Exception:
                # fallback si ce n'est pas convertible
                last = 0
    else:
        # cas scalaire (str/int/float)
        try:
            last = int(raw)
        except Exception:
            last = 0

    print(f"Activité pour {name} — reprise à {last}/120")

    for i in range(last, 120):
        await asyncio.sleep(1)         # ✅ non-bloquant
        activity.heartbeat(i + 1)      # ✅ envoie heartbeat
        print(f"  → {i+1}/120 secondes…")

    return f"Bonjour {name}, j’ai terminé mon sommeil !"

