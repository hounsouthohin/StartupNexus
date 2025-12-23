import os
from typing import TypedDict, Annotated, List, Dict
import operator
from pydantic import BaseModel, Field

# --- Pydantic Models for Structured Output ---
class TestFile(BaseModel):
    """Represents a single generated test file."""
    file_path: str = Field(description="The full relative path for the test file, e.g., 'tests/components/Button.test.tsx'.")
    content: str = Field(description="The complete source code for the test file.")

class TestSuite(BaseModel):
    """A collection of generated test files."""
    tests: List[TestFile]

# Setup basic logger (replace with actual logger if available)
class Logger:
    def info(self, message):
        print(f"[INFO] {message}")
    def error(self, message):
        print(f"[ERROR] {message}")
logger = Logger()

# Agent node function
def call_llm(state: dict) -> dict:
    """
    Invokes the LLM with the current messages and returns the response.
    The LLM generates test files based on the provided source files,
    with its output structured by the TestSuite Pydantic model.
    """
    # Imports moved inside the function to avoid Temporal sandbox issues
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    logger.info("TestCoverage Agent: Starting test generation using OpenAI with structured output.")

    # Upgraded to a model that is more reliable with structured output
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    # Read the system prompt from prompts/test_coverage.md
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_path = os.path.join(current_dir, '..', 'prompts', 'test_coverage.md')
        with open(prompts_path, "r", encoding='utf-8') as f:
            system_prompt_content = f.read()
    except FileNotFoundError:
        logger.error("prompts/test_coverage.md not found. Using fallback system prompt.")
        system_prompt_content = "You are TestCoverage Agent. Generate unit tests for the provided files, conforming to the required JSON schema."

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt_content),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    # Construct the message with files content
    files_content_message = "Provided source code files:\n\n"
    for path, content in state.get("files", {}).items():
        files_content_message += f"File: {path}\n```\n{content}\n```\n\n"
    
    # Chain with structured output
    structured_llm = llm.with_structured_output(TestSuite)
    chain = prompt | structured_llm
    
    try:
        # The chain now returns a Pydantic object, not a raw string
        response_suite = chain.invoke({"messages": state["messages"] + [HumanMessage(content=files_content_message)]})
        
        # Convert the Pydantic model into the dictionary format expected by the agent state
        generated_tests_dict = {test.file_path: test.content for test in response_suite.tests}
        
        logger.info(f"TestCoverage Agent: Successfully generated {len(generated_tests_dict)} test files.")
        # We no longer have the raw AIMessage, so we can't add it to the state.
        # This is fine as the test agent is a one-shot process.
        return {"tests": generated_tests_dict}

    except Exception as e:
        # This will catch errors from the LLM call or Pydantic validation
        logger.error(f"TestCoverage Agent: An error occurred during structured output generation: {e}")
        return {"tests": {}}

def test_coverage_agent(files: dict) -> dict:
    """
    Main function to run the TestCoverage Agent.
    Takes a dictionary of files (path: content) as input.
    """
    # Imports moved inside the function to avoid Temporal sandbox issues
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, BaseMessage
    
    # Define Agent State
    class AgentState(TypedDict):
        messages: Annotated[List[BaseMessage], operator.add]
        files: dict
        tests: dict

    # Graph definition
    graph = StateGraph(AgentState)
    graph.add_node("test_coverage", call_llm)
    graph.set_entry_point("test_coverage")
    graph.add_edge("test_coverage", END)
    app = graph.compile()
    
    logger.info("Starting TestCoverage Agent process.")
    initial_message = HumanMessage(content="Generate unit tests for the provided files.")
    
    final_state = app.invoke(
        {"messages": [initial_message], "files": files, "tests": {}},
        config={"recursion_limit": 10}
    )
    
    generated_tests = final_state.get("tests", {})
    
    logger.info("TestCoverage Agent process completed.")
    return {"tests": generated_tests}
