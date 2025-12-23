import os
from typing import TypedDict, Annotated, List
import operator

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
    The LLM generates test files based on the provided source files.
    """
    # Imports moved inside the function to avoid Temporal sandbox issues
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    import json # Import json

    logger.info("TestCoverage Agent: Starting test generation using OpenAI.")

    # Use ChatOpenAI instead of Ollama
    # The OPENAI_API_KEY is already loaded from the .env file in the worker's environment
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    
    # Read the system prompt from prompts/test_coverage.md
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_path = os.path.join(current_dir, '..', 'prompts', 'test_coverage.md')
        with open(prompts_path, "r") as f:
            system_prompt_content = f.read()
    except FileNotFoundError:
        logger.error("prompts/test_coverage.md not found. Using fallback system prompt.")
        system_prompt_content = "You are TestCoverage Agent. Generate unit tests."

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
        
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"] + [HumanMessage(content=files_content_message)]})
    logger.info(f"RAW RESPONSE FROM LLM (test_coverage):\n{response.content[:1000]}...")

    # Safely parse the LLM's response using json.loads
    try:
        generated_tests = json.loads(response.content)
        if "tests" in generated_tests and isinstance(generated_tests["tests"], dict):
            logger.info("TestCoverage Agent: Successfully generated tests.")
            return {"messages": [response], "tests": generated_tests["tests"]}
        else:
            logger.error(f"TestCoverage Agent: LLM response did not contain expected 'tests' dictionary. Raw content: {response.content}")
            return {"messages": [response], "tests": {}}
    except json.JSONDecodeError as e:
        logger.error(f"TestCoverage Agent: Error parsing LLM response as JSON: {e}. Raw content: {response.content}")
        return {"messages": [response], "tests": {}}
    except Exception as e:
        logger.error(f"TestCoverage Agent: Unexpected error during response parsing: {e}. Raw content: {response.content}")
        return {"messages": [response], "tests": {}}

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
