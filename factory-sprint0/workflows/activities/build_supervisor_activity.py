from temporalio import activity

from agents.build_supervisor_agent import run_build_supervisor


@activity.defn(name="build_supervisor_activity")
async def build_supervisor_activity(input_data: dict) -> dict:
    return await run_build_supervisor(
        build_stderr=input_data.get("build_stderr", ""),
        combined_files=input_data.get("combined_files", {}),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )

