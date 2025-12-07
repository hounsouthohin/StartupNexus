import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflow import HelloWorkflow, sleepy_activity

async def main():
    client = await Client.connect("localhost:7233")

    print("Worker démarré – prêt à exécuter workflows + activities")
    
    worker = Worker(
        client,
        task_queue="hello-queue",
        workflows=[HelloWorkflow],
        activities=[sleepy_activity],
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
