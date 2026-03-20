from temporalio import activity

from agents.conformity_agent import run_conformity_supervisor


@activity.defn(name="conformity_activity")
async def conformity_activity(input_data: dict) -> dict:
    return await run_conformity_supervisor(
        file_path=input_data.get("file_path", ""),
        file_content=input_data.get("file_content", ""),
        requirements=input_data.get("requirements", []),
        plan=input_data.get("plan", {}),
        files_so_far=input_data.get("files_so_far", {}),
        project_name=input_data.get("project_name", ""),
        run_id=input_data.get("run_id", ""),
        stack_id=input_data.get("stack_id", "nextjs-clerk-prisma"),
    )

