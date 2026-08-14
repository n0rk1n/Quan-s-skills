from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    call_id: str | None = None
    arguments: Any = None
    output_summary: str | None = None
    status: str | None = None


@dataclass
class Message:
    role: str
    content: str = ""
    created_at: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationStats:
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    tool_call_count: int = 0
    warning_count: int = 0


@dataclass
class Conversation:
    source: str
    conversation_id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)
    stats: ConversationStats = field(default_factory=ConversationStats)

    def recompute_stats(self) -> None:
        self.stats.message_count = len(self.messages)
        self.stats.user_message_count = sum(1 for message in self.messages if message.role == "user")
        self.stats.assistant_message_count = sum(1 for message in self.messages if message.role == "assistant")
        self.stats.tool_call_count = sum(len(message.tool_calls) for message in self.messages)


@dataclass
class ExportWarning:
    path: str
    message: str


@dataclass
class ParseResult:
    conversations: list[Conversation] = field(default_factory=list)
    warnings: list[ExportWarning] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
