from temporalio import activity

@activity.defn
async def qa_activity(input_data: dict) -> dict:
    """
    Temporal Activity to run the QA Agent for End-to-End testing.
    
    This activity is intended to be called after the dev and test_coverage
    activities have successfully completed and the application is built/deployed.
    """
    # Imports moved inside the function to respect Temporal's sandbox
    from agents.qa import create_qa_agent
    from langchain_core.messages import HumanMessage

    activity.logger.info("Starting QA Agent activity...")

    # For now, we use a generic prompt. In a real scenario, input_data
    # would contain more context, like a deployment URL or project specs.
    prompt = input_data.get(
        "prompt", 
        "The application is a SaaS for task management with Clerk authentication. Please generate E2E tests for it."
    )

    try:
        agent = create_qa_agent()
        initial_message = HumanMessage(content=prompt)
        
        # Invoke the agent graph
        final_state = await agent.ainvoke({"messages": [initial_message]})
        
        # The agent's output is the generated test code
        generated_test_code = final_state['messages'][-1].content
        
        activity.logger.info("QA Agent activity completed successfully.")
        
        # Here, you might want to write the test code to a file
        # and then use the 'playwright_test' tool to run it.
        # For now, we return the generated code.
        return {"e2e_tests": {"tests/e2e/generated_test.spec.ts": generated_test_code}}

    except Exception as e:
        activity.logger.error(f"QA Agent activity failed: {str(e)}")
        raise
