"""Experimental conversational prototype composed beside the maintained ``/answer`` contract.

Nothing in this package changes retrieval, the status gate, citation validation, or the
deterministic ``/answer`` route. It adds a separate ``/chat`` surface that explains admitted
passages with an optional model provider (OpenAI Responses API, opt-in) and checks the result
mechanically. See ``docs/chat-prototype.md`` and ADR-019.
"""

from __future__ import annotations

from biotech_rag_assistant.chat.settings import ChatSettings

__all__ = ["ChatSettings"]
