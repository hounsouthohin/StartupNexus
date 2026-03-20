from temporalio import activity

from agents.architecture_agent import run_architecture_supervisor


@activity.defn(name="architecture_activity")
async def architecture_activity(input_data: dict) -> dict:
    return await run_architecture_supervisor(
        file_path=input_data.get("file_path", ""),
        file_content=input_data.get("file_content", ""),
        prisma_schema=input_data.get("prisma_schema", ""),
        plan=input_data.get("plan", {}),
        files_so_far=input_data.get("files_so_far", {}),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )

