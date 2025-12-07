import asyncio
from temporalio.client import Client
from workflow import HelloWorkflow


async def main():
    client = await Client.connect("localhost:7233")
    
    print("Lancement du workflow indestructible...")
    handle = await client.start_workflow(
        HelloWorkflow.run,
        "Arthur le Boss",
        id="hello-workflow-001",
        task_queue="hello-queue",
    )
    
    print(f"Workflow lancé ! ID = {handle.id}")
    print("Va sur http://localhost:8080 → tu le verras en cours")
    print("Quand tu veux, tue le worker avec Ctrl+C → puis relance-le")
    print("Tu vas voir la magie...")
    
    result = await handle.result()
    print(f"RÉSULTAT FINAL : {result}")

if __name__ == "__main__":
    asyncio.run(main())