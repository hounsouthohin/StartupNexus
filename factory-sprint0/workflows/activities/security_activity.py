from temporalio import activity

from agents.security_agent import run_security_supervisor


@activity.defn(name="security_activity")
async def security_activity(input_data: dict) -> dict:
    return await run_security_supervisor(
        file_path=input_data.get("file_path", ""),
        file_content=input_data.get("file_content", ""),
        prisma_schema=input_data.get("prisma_schema", ""),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )

