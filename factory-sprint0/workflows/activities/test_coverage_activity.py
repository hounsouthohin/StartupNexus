from temporalio import activity

@activity.defn
async def test_coverage_activity(dev_result_files: dict) -> dict:
    """
    Temporal Activity to run the TestCoverage Agent.
    Takes the dictionary of generated files from the Dev Agent as input.
    """
    # Import moved inside the activity function
    from agents.test_coverage import test_coverage_agent

    activity.logger.info(f"Running TestCoverage Activity with {len(dev_result_files)} files.")
    
    # Call the TestCoverage Agent
    test_agent_output = test_coverage_agent(dev_result_files)
    
    # The agent returns {'tests': {path: content}}, so we pass that through.
    activity.logger.info(f"TestCoverage Agent generated {len(test_agent_output.get('tests', {}))} test files.")
    return test_agent_output