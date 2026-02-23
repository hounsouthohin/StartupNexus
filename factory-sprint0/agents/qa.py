import os
import subprocess
from typing import TypedDict, Annotated, List
import operator
from dotenv import load_dotenv

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from utils.prompt_loader import load_prompt
from agents.llm_factory import create_chat_llm

# Load environment variables from .env file
load_dotenv()

# --- Logger ---
class Logger:
    def info(self, message): print(f"[INFO] {message}")
    def error(self, message): print(f"[ERROR] {message}")
logger = Logger()

# --- Tools ---
class PlaywrightTestArgs(BaseModel):
    test_file: str = Field(description="Optional: The path to a specific test file to run. If not provided, all tests will run.", default="")

@tool(args_schema=PlaywrightTestArgs)
def playwright_test(test_file: str = "") -> str:
    """
    Runs End-to-End tests using Playwright.
    """
    logger.info("Executing 'npx playwright test'...")
    try:
        command = ['npx', 'playwright', 'test']
        if test_file:
            command.append(test_file)
            
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True, 
            timeout=120
        )
        return f"Playwright tests passed: {result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Playwright tests failed (code {e.returncode}):\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
    except Exception as e:
        return f"An error occurred during Playwright test execution: {e}"

# --- Agent State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

# --- Agent Definition ---
def qa_agent_node(state: AgentState) -> dict:
    """
    The primary node for the QA agent that generates test scenarios.
    """
    try:
        system_prompt_content = load_prompt("qa")
    except FileNotFoundError:
        logger.error("prompts/qa.md not found.")
        system_prompt_content = "You are a QA Agent..."

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt_content),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    llm = create_chat_llm(temperature=0.2)
    # The agent's primary job is to generate the test file content, not run it directly.
    # The 'playwright_test' tool would be used in a more complex graph to validate the generated tests.
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    # In a real scenario, this response would be parsed to extract the test file content
    # and then written to a file. For this basic agent, we just return the content.
    return {"messages": state["messages"] + [response]}

def create_qa_agent():
    """
    Creates the graph for the QA Agent.
    """
    graph = StateGraph(AgentState)
    graph.add_node("qa_node", qa_agent_node)
    graph.set_entry_point("qa_node")
    graph.add_edge("qa_node", END)
    
    return graph.compile()

if __name__ == '__main__':
    # Example of how to run the agent
    agent = create_qa_agent()
    initial_message = HumanMessage(content="The application is a SaaS for task management with Clerk authentication. Please generate E2E tests for it.")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
    else:
        final_state = agent.invoke({"messages": [initial_message]})
        print("\n--- QA Agent Final Output ---")
        print(final_state['messages'][-1].content)
