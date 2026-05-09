from langchain_core.messages import AIMessage

from agents.stacks.nextjs_clerk_prisma.dev_graph import (
    _extract_tool_calls_from_text,
    _normalize_ai_message_tool_calls,
)


def test_extract_tool_calls_from_text_handles_multiple_json_objects():
    allowed = {"write_file", "shell_exec"}
    content = """
    {
      "name": "write_file",
      "arguments": {"path": "app/page.tsx", "content": "export default function Page() { return null }"}
    }
    {
      "name": "shell_exec",
      "arguments": {"command": "npm run build"}
    }
    """

    calls = _extract_tool_calls_from_text(content, allowed)
    assert len(calls) == 2
    assert calls[0]["name"] == "write_file"
    assert calls[0]["args"]["path"] == "app/page.tsx"
    assert calls[1]["name"] == "shell_exec"
    assert calls[1]["args"]["command"] == "npm run build"


def test_extract_tool_calls_from_text_handles_tool_calls_wrapper():
    allowed = {"shell_exec"}
    content = """
    {
      "tool_calls": [
        {
          "id": "call_123",
          "function": {
            "name": "shell_exec",
            "arguments": "{\\"command\\": \\"npx tsc --noEmit\\"}"
          }
        }
      ]
    }
    """

    calls = _extract_tool_calls_from_text(content, allowed)
    assert len(calls) == 1
    assert calls[0]["id"] == "call_123"
    assert calls[0]["name"] == "shell_exec"
    assert calls[0]["args"] == {"command": "npx tsc --noEmit"}


def test_normalize_ai_message_tool_calls_recovers_from_content():
    allowed = {"write_file"}
    ai = AIMessage(
        content='{"name":"write_file","arguments":{"path":"a.txt","content":"ok"}}',
        tool_calls=[],
    )

    normalized = _normalize_ai_message_tool_calls(ai, allowed)
    assert len(normalized.tool_calls) == 1
    assert normalized.tool_calls[0]["name"] == "write_file"
    assert normalized.tool_calls[0]["args"]["path"] == "a.txt"

