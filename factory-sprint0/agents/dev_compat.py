from __future__ import annotations

import re

try:
    from langchain_openai import ChatOpenAI
except ModuleNotFoundError:
    class ChatOpenAI:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            self._args = args
            self._kwargs = kwargs

        def get_num_tokens(self, text: str) -> int:
            return max(1, len(text) // 4)

        def bind_tools(self, *args, **kwargs):
            raise ModuleNotFoundError("langchain_openai is required to execute dev_agent()")

        def invoke(self, *args, **kwargs):
            raise ModuleNotFoundError("langchain_openai is required to execute dev_agent()")


try:
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
except ModuleNotFoundError:
    class _BaseMessage:
        def __init__(self, content="", tool_calls=None, tool_call_id=None):
            self.content = content
            self.tool_calls = tool_calls or []
            self.tool_call_id = tool_call_id

    class HumanMessage(_BaseMessage):
        pass

    class SystemMessage(_BaseMessage):
        pass

    class ToolMessage(_BaseMessage):
        pass


try:
    from .llm_runner import LLMConversationRunner
except ModuleNotFoundError:
    class LLMConversationRunner:  # type: ignore[override]
        def __init__(self, llm, messages: list) -> None:
            self.llm = llm
            self.messages = messages

        def inject(self, content: str) -> None:
            self.messages.append(HumanMessage(content=content))

        def _compact(self, text: str) -> str:
            return re.sub(r"\s+", " ", text).strip()

        def _shrink_tool_output(self, tool_name: str, output: str, max_chars: int = 1800) -> str:
            compact = self._compact(output)
            if len(compact) <= max_chars:
                return compact
            head = max_chars // 2
            tail = max_chars - head
            return (
                f"[{tool_name}] OUTPUT_TRUNCATED total_chars={len(compact)} | "
                f"head: {compact[:head]} ... tail: {compact[-tail:]}"
            )

        def _main_context(self, messages_list: list, max_chars: int = 14000) -> list:
            if len(messages_list) <= 2:
                return messages_list
            kept = [messages_list[0], messages_list[1]]
            turns = []
            i = 2
            n = len(messages_list)
            while i < n:
                msg = messages_list[i]
                has_tool_calls = hasattr(msg, "tool_calls") and bool(getattr(msg, "tool_calls", None))
                if has_tool_calls:
                    turn = [msg]
                    i += 1
                    while i < n and isinstance(messages_list[i], ToolMessage):
                        turn.append(messages_list[i])
                        i += 1
                    expected_ids = {tc.get("id") for tc in msg.tool_calls if tc.get("id")}
                    got_ids = {tm.tool_call_id for tm in turn[1:] if getattr(tm, "tool_call_id", None)}
                    if expected_ids and expected_ids.issubset(got_ids):
                        turns.append(turn)
                else:
                    if isinstance(msg, ToolMessage):
                        i += 1
                        continue
                    turns.append([msg])
                    i += 1
            if not turns:
                return kept
            last_turn = turns[-1]
            turn_chars = sum(len(str(getattr(m, "content", ""))) for m in last_turn)
            if turn_chars > max_chars:
                for msg in reversed(messages_list[2:]):
                    if not isinstance(msg, ToolMessage):
                        return kept + [msg]
                return kept
            return kept + last_turn
