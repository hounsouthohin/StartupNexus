from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn
class SaaSFactoryWorkflow:
    @workflow.run
    async def run(self, input_data: dict) -> str:
        phrase = input_data.get("phrase", "phrase inconnue")
        workflow.logger.info(f"Workflow démarré – phrase reçue : {phrase}")

        # On délègue TOUT le raisonnement AI à une Activity
        # BUG FIX: Previously, `architect_activity` was directly imported.
        # This caused a `RestrictedWorkflowAccessError` because Temporal workflows
        # are sandboxed and cannot directly import modules that have
        # non-deterministic or restricted operations (like `requests` which was
        # transitively imported by `architect_agent`).
        # The fix is to refer to the activity by its string name.
        # Temporal's worker will then resolve the activity by name.
        result = await workflow.execute_activity(
            "architect_activity",
            input_data,
            start_to_close_timeout=timedelta(minutes=10),  # LLM peut être long
            heartbeat_timeout=timedelta(seconds=30),
        )

        return result