# Project Analysis

This document breaks down the structure and workflow of the agent-based code generation system.

## Project Overview

The system uses a series of specialized AI agents orchestrated by a Temporal workflow to automate the process of generating a full-stack Next.js application based on a user's request. The workflow proceeds as follows:

1.  **Architect Agent**: Designs the application architecture, creating technical specifications and a Mermaid diagram.
2.  **Dev Agent**: Generates the application code based on the architect's output.
3.  **Test Coverage Agent**: Writes unit tests for the generated code.
4.  **GitHub Activity**: Pushes the generated code and tests to a new GitHub repository and opens a pull request.

## Workflow (`factory-sprint0/workflows/factory_workflow.py`)

The main workflow coordinates the execution of the different agents and activities in a specific sequence.

```python
# factory-sprint0/workflows/factory_workflow.py
import json
from datetime import timedelta
from temporalio import workflow
from .activities.architect_activity import architect_activity
from .activities.dev_activity import dev_activity
from .activities.test_coverage_activity import test_coverage_activity
from .activities.github_activity import github_activity

@workflow.defn
class FactoryWorkflow:
    @workflow.run
    async def run(self, phrase: str, project_name: str) -> dict:
        # 1. Architect Agent
        architect_result = await workflow.execute_activity(
            architect_activity,
            {"phrase": phrase},
            start_to_close_timeout=timedelta(minutes=5),
        )

        # 2. Dev Agent
        dev_input = {
            "spec": architect_result["specification"],
            "mermaid": architect_result["mermaid_diagram"],
            "project_name": project_name
        }
        dev_result = await workflow.execute_activity(
            dev_activity,
            dev_input,
            start_to_close_timeout=timedelta(minutes=15),
        )

        # 3. Test Coverage Agent
        # Ensure dev_result['files'] is not empty
        if dev_result.get("files"):
            test_coverage_result = await workflow.execute_activity(
                test_coverage_activity,
                dev_result["files"],
                start_to_close_timeout=timedelta(minutes=10),
            )
        else:
            test_coverage_result = {"tests": {}}

        # Combine code and tests
        all_files = {**dev_result.get("files", {}), **test_coverage_result.get("tests", {})}

        # 4. GitHub Activity
        github_input = {"files": all_files, "project_name": project_name}
        github_pr_url = await workflow.execute_activity(
            github_activity,
            github_input,
            start_to_close_timeout=timedelta(minutes=5),
        )

        return {
            "architect_result": architect_result,
            "dev_result": dev_result,
            "test_coverage_result": test_coverage_result,
            "github_pr_url": github_pr_url,
        }
```

## 1. Architect Agent

The Architect Agent is responsible for creating the high-level design of the application.

-   **Agent (`agents/architect.py`)**: This LangGraph-based agent orchestrates three sub-agents (Planner, Spec Writer, Diagrammer) to produce a plan, a detailed specification, and a Mermaid diagram.

    ```python
    # factory-sprint0/agents/architect.py
    import os
    from typing import TypedDict, Annotated, List
    import operator
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, END
    from .shared_tools import rag_search_tool  # Using the shared tool
    from pydantic import BaseModel, Field
    import json

    # --- Pydantic Output Schema ---
    class ArchitectOutput(BaseModel):
        specification: str = Field(..., description="The detailed technical specification in Markdown format.")
        mermaid_diagram: str = Field(..., description="The architecture diagram in Mermaid syntax.")

    # --- Agent State ---
    class ArchitectState(TypedDict):
        messages: Annotated[List[BaseMessage], operator.add]
        rag_context: str
        plan: dict
        specification: str
        mermaid_diagram: str
        architect_output: ArchitectOutput = None

    # --- Node Functions ---
    def call_rag(state: ArchitectState) -> ArchitectState:
        # ... (Implementation to call RAG and store context)
        return state

    def call_planner(state: ArchitectState) -> ArchitectState:
        # ... (Implementation to generate a plan)
        return state

    def call_spec_writer(state: ArchitectState) -> ArchitectState:
        # ... (Implementation to generate specifications)
        return state

    def call_diagrammer(state: ArchitectState) -> ArchitectState:
        # ... (Implementation to generate a diagram)
        return state

    def compile_output(state: ArchitectState) -> ArchitectState:
        output = ArchitectOutput(
            specification=state["specification"],
            mermaid_diagram=state["mermaid_diagram"]
        )
        return {"architect_output": output}

    # --- Graph Definition ---
    def create_architect_agent():
        graph = StateGraph(ArchitectState)
        graph.add_node("rag", call_rag)
        graph.add_node("planner", call_planner)
        graph.add_node("spec_writer", call_spec_writer)
        graph.add_node("diagrammer", call_diagrammer)
        graph.add_node("compile_output", compile_output)

        graph.set_entry_point("rag")
        graph.add_edge("rag", "planner")
        graph.add_edge("planner", "spec_writer")
        graph.add_edge("spec_writer", "diagrammer")
        graph.add_edge("diagrammer", "compile_output")
        graph.add_edge("compile_output", END)
        
        return graph.compile()
    ```

-   **Activity (`workflows/activities/architect_activity.py`)**: This Temporal activity wraps the Architect Agent, making it invokable from the workflow. It handles passing the user's request to the agent and returning the structured output.

    ```python
    # factory-sprint0/workflows/activities/architect_activity.py
    from temporalio import activity
    from agents.architect import create_architect_agent
    # ... other imports

    @activity.defn
    async def architect_activity(input_data: dict) -> dict:
        # ... (Initialization and error handling)
        architect_agent = create_architect_agent()
        initial_state = { "messages": [HumanMessage(content=input_data["phrase"])] }
        final_state = await architect_agent.ainvoke(initial_state)
        architect_output = final_state["architect_output"]
        return {
            'specification': architect_output.specification,
            'mermaid_diagram': architect_output.mermaid_diagram
        }
    ```

-   **Prompts (`prompts/architect.md`)**: Contains the system prompts for the sub-agents (Planner, Spec Writer, Diagrammer), defining their roles and expected output formats.

## 2. Dev Agent

The Dev Agent generates the actual source code for the application.

-   **Agent (`agents/dev.py`)**: A LangGraph agent that uses tools like `write_file`, `validate_syntax`, and `prisma_migrate` to generate and validate code. It iteratively builds the application until the core files are created.

    ```python
    # factory-sprint0/agents/dev.py
    # ... imports
    from .shared_tools import write_file, validate_syntax, prisma_migrate, rag_search

    def call_llm(state: dict) -> dict:
        # ... (LLM invocation logic with tools)
        pass

    def dev_agent(spec: str, mermaid: str, project_name: str) -> dict:
        # ... (Graph definition and setup)
        graph = StateGraph(AgentState)
        graph.add_node("dev", call_llm)
        graph.add_node("tools", ToolNode([write_file, validate_syntax, prisma_migrate, rag_search]))
        # ... (Edges and compilation)
        app = graph.compile()

        initial_message = HumanMessage(content=f"Project Name: {project_name}\n\nArchitectural Specification:\n{spec}\n\nMermaid Diagram:\n{mermaid}")
        final_state = app.invoke({"messages": [initial_message], "files": {}, "iterations": 0})
        return {"files": final_state.get("files", {})}
    ```

-   **Activity (`workflows/activities/dev_activity.py`)**: The Temporal activity that executes the `dev_agent` with the specification and diagram from the Architect Agent.

    ```python
    # factory-sprint0/workflows/activities/dev_activity.py
    from temporalio import activity
    from agents.dev import dev_agent

    @activity.defn
    async def dev_activity(input_data: dict) -> dict:
        # ... (Input handling)
        result = dev_agent(input_data["spec"], input_data["mermaid"], input_data["project_name"])
        return result
    ```

-   **Prompt (`prompts/dev.md`)**: Instructs the Dev Agent to generate Next.js code, use RAG for standards, create one file at a time, and validate its work.

## 3. Test Coverage Agent

This agent is responsible for generating unit tests for the code created by the Dev Agent.

-   **Agent (`agents/test_coverage.py`)**: A simple LangGraph agent that takes the generated source files, invokes an LLM (Ollama) to generate test files, and returns them as a dictionary.

    ```python
    # factory-sprint0/agents/test_coverage.py
    # ... imports

    def call_llm(state: dict) -> dict:
        # ... (LLM invocation logic)
        # Parses LLM response to extract test files
        pass

    def test_coverage_agent(files: dict) -> dict:
        # ... (Graph definition)
        graph = StateGraph(AgentState)
        graph.add_node("test_coverage", call_llm)
        graph.set_entry_point("test_coverage")
        graph.add_edge("test_coverage", END)
        app = graph.compile()

        final_state = app.invoke({"messages": [HumanMessage(content="...")], "files": files, "tests": {}})
        return {"tests": final_state.get("tests", {})}
    ```

-   **Activity (`workflows/activities/test_coverage_activity.py`)**: A Temporal activity that passes the files from the `dev_activity` to the `test_coverage_agent`.

    ```python
    # factory-sprint0/workflows/activities/test_coverage_activity.py
    from temporalio import activity
    from agents.test_coverage import test_coverage_agent

    @activity.defn
    async def test_coverage_activity(dev_result_files: dict) -> dict:
        test_agent_output = test_coverage_agent(dev_result_files)
        return test_agent_output
    ```

-   **Prompt (`prompts/test_coverage.md`)**: Directs the agent to generate Jest and React Testing Library tests, aiming for high coverage and mocking authentication where necessary.

## 4. GitHub Activity

-   **Activity (`workflows/activities/github_activity.py`)**: This is a standard Python function decorated as a Temporal activity. It uses the `PyGithub` library to interact with the GitHub API. Its responsibilities include:
    1.  Creating a new private repository.
    2.  Creating a `dev` branch.
    3.  Pushing all the generated files (code and tests) to the `dev` branch.
    4.  Opening a pull request from `dev` to the main branch.

    ```python
    # factory-sprint0/workflows/activities/github_activity.py
    from temporalio import activity
    from github import Github

    @activity.defn
    async def github_activity(input_data: dict) -> str:
        # ... (GitHub token and user retrieval)
        repo = user.create_repo(...)
        # ... (Branch creation and file pushing logic)
        pr = repo.create_pull(...)
        return pr.html_url
    ```
