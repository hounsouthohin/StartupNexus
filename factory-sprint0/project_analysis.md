# Project Analysis: factory-sprint0

## 1. Project Goal

The project `factory-sprint0` aims to create a "SaaS Factory" that automatically generates the source code for a SaaS application based on a user's request, provided as a simple "phrase".

## 2. Architecture Overview

The project is built around a Temporal workflow that orchestrates three main AI-driven steps:

1.  **Architect Agent**: Designs the software architecture.
    *   **Input**: A phrase from the user (e.g., "a SaaS for task management").
    *   **Process**: Uses a LangGraph agent with a `gpt-4o` LLM and a RAG system (Qdrant) to generate a technical specification and a Mermaid diagram. It's designed to follow strict technical standards retrieved from a vector database.
    *   **Output**: A technical specification in Markdown and a Mermaid diagram.

2.  **Dev Agent**: Writes the source code.
    *   **Input**: The technical specification and Mermaid diagram from the Architect agent.
    *   **Process**: Uses a LangGraph agent with a `gpt-4o-mini` LLM and a ReAct loop. It has tools to write files, validate their syntax, and run database migrations, allowing it to correct its own errors.
    *   **Output**: A dictionary of code files (`{path: content}`).

3.  **GitHub Activity**: Manages the Git repository.
    *   **Input**: The code files from the Dev agent and a project name.
    *   **Process**: Creates a private GitHub repository, creates a `dev` branch, pushes the generated code to it, and opens a pull request to the `main` branch.
    *   **Output**: The URL of the newly created pull request.

## 3. State of the Project & Progress

The project has a solid and ambitious architectural foundation. The workflow is well-defined, the agents are structured, and the activities are in place. The overall pipeline for code generation is logical and complete in its conception.

However, the project is in an early "sprint 0" state and is **currently non-functional** due to several critical bugs.

### High-Priority Issues (Bugs Blocking Execution)

1.  **`worker.py` Crash (Fixed)**: The Temporal worker entrypoint (`run/worker.py`) was crashing on startup due to an invalid `workflow_defaults` argument passed to the `Worker` class. This argument has been removed, which should allow the worker to start.
2.  **Architect's Mermaid Tool is a Stub**: The `generate_mermaid_diagram` tool within the Architect agent is a major bug. It does not dynamically generate a diagram based on the architecture. Instead, it returns a **hardcoded, static diagram string**. This makes the diagram output completely useless and disconnected from the user's request.
3.  **Dev Agent's Prompt Path is Incorrect**: The Dev agent has a hardcoded, incorrect path (`factory-sprint0/prompts/dev.md`) to its system prompt file. The agent's working directory will be the project root, so the path should be `prompts/dev.md`. This will cause a `FileNotFoundError` and crash the agent.

### Medium-Priority Issues (Design & Robustness)

1.  **Brittle Architect Output**: The Architect agent returns a single string containing both the specification and the Mermaid diagram. The workflow has to manually parse this string. A more robust approach would be to return a structured JSON object (e.g., `{"specification": "...", "mermaid_diagram": "..."}`).
2.  **Basic Error Handling**: The error handling in the GitHub activity is too generic (`except Exception`). It should catch more specific exceptions from the `PyGithub` library to provide better feedback.
3.  **Simplistic ReAct Logic**: The `should_continue` logic in the Dev agent's ReAct loop is basic. It relies on finding the string "error" in tool messages. A more sophisticated implementation would use structured error objects.

### Low-Priority Issues (Future Improvements)

1.  **Incomplete Local LLM Fallback**: The idea of using a local LLM (Ollama) as a fallback is good but not yet implemented.
2.  **Configuration Management**: Many values (e.g., `task_queue`, LLM model names) are hardcoded. These should be moved to a central configuration file.

## 4. Next Steps & Recommendations

The immediate focus should be on fixing the critical bugs to make the pipeline functional.

1.  **Fix the `generate_mermaid_diagram` Tool**: This is the most critical issue after the worker crash. The tool must be implemented to dynamically generate a Mermaid diagram that accurately reflects the architecture described in the specification.
2.  **Fix the Dev Agent's Prompt Path**: Correct the hardcoded path in `agents/dev.py` to `prompts/dev.md`.
3.  **Refactor Architect Agent's Output**: Modify the agent to return a structured JSON object. This will make the workflow more robust and easier to maintain.

Once these issues are addressed, the project will be in a state where it can be tested end-to-end and has the potential to successfully generate a simple SaaS application.
