from __future__ import annotations

import re
import logging
from langchain_core.messages import HumanMessage, ToolMessage

logger = logging.getLogger(__name__)

MAX_TOOL_OUTPUT_CHARS = 1800
MAX_MAIN_HISTORY_CHARS = 14000


class LLMConversationRunner:
    """
    Gère la conversation LLM : messages, contexte, injection de corrections.
    Extrait de dev_agent() — logique IDENTIQUE, zéro changement de comportement.
    runner.messages est la MÊME liste que dev_agent.messages (pas de copie).
    """

    def __init__(self, llm, messages: list) -> None:
        self.llm = llm
        self.messages = messages  # référence partagée avec dev_agent

    def inject(self, content: str) -> None:
        """
        Injecte un message humain dans l'historique.
        Équivalent EXACT de : messages.append(HumanMessage(content=content))
        """
        self.messages.append(HumanMessage(content=content))

    # Copies exactes des fonctions imbriquées de dev.py
    # Toute modification ici doit être répercutée dans dev.py et vice-versa.

    def _compact(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _shrink_tool_output(self, tool_name: str, output: str,
                            max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
        compact = self._compact(output)
        if len(compact) <= max_chars:
            return compact
        head = max_chars // 2
        tail = max_chars - head
        return (
            f"[{tool_name}] OUTPUT_TRUNCATED total_chars={len(compact)} | "
            f"head: {compact[:head]} ... tail: {compact[-tail:]}"
        )

    def _main_context(self, messages_list: list,
                      max_chars: int = MAX_MAIN_HISTORY_CHARS) -> list:
        """
        Contexte compact state-first:
        - garde les 2 messages initiaux,
        - garde UNIQUEMENT le dernier tour complet AI(tool_calls)+ToolMessages,
        - sinon garde le dernier message non-tool.
        Cela réduit le bruit et force la boucle done/missing/next.
        """
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

                # Ne garder que les turns complets (assistant + toutes réponses tools).
                if expected_ids and expected_ids.issubset(got_ids):
                    turns.append(turn)
                else:
                    logger.warning("Turn incomplet tool_calls ignoré dans _main_context")
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
            # Fallback: garder seulement le dernier message non-tool.
            for msg in reversed(messages_list[2:]):
                if not isinstance(msg, ToolMessage):
                    return kept + [msg]
            return kept
        return kept + last_turn
