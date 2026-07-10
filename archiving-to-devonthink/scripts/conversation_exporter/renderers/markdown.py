from __future__ import annotations

import json
import re
from typing import Any

from conversation_exporter.model import Conversation, Message
from conversation_exporter.utils import sanitize_heading_depth


SKILL_BLOCK_RE = re.compile(r"<skill\b[^>]*>.*?</skill>", re.IGNORECASE | re.DOTALL)


def render_conversation(conversation: Conversation) -> str:
    conversation.recompute_stats()
    parts = [render_front_matter(conversation), ""]
    for message in conversation.messages:
        rendered = render_message(message)
        if rendered:
            parts.append(rendered)
    return "\n\n".join(parts).rstrip() + "\n"


def render_front_matter(conversation: Conversation) -> str:
    fields: list[tuple[str, Any]] = [
        ("source", conversation.source),
        ("conversation_id", conversation.conversation_id),
        ("title", conversation.title),
        ("created_at", conversation.created_at),
        ("updated_at", conversation.updated_at),
        ("message_count", conversation.stats.message_count),
        ("user_message_count", conversation.stats.user_message_count),
        ("assistant_message_count", conversation.stats.assistant_message_count),
        ("tool_call_count", conversation.stats.tool_call_count),
    ]
    lines = ["---"]
    for key, value in fields:
        if value is None:
            continue
        lines.append(f"{key}: {_yaml_scalar(value)}")
    for key in sorted(conversation.metadata):
        value = conversation.metadata[key]
        if isinstance(value, (str, int, float, bool)) and value is not None:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def render_message(message: Message) -> str:
    if message.role not in {"user", "assistant"}:
        return ""
    heading = "## 用户" if message.role == "user" else "## AI"
    parts = [heading, "", sanitize_heading_depth(_lightweight_message_content(message.content)).strip()]
    return "\n".join(parts).rstrip()


def _lightweight_message_content(content: str) -> str:
    return SKILL_BLOCK_RE.sub(_skill_placeholder, content)


def _skill_placeholder(match: re.Match[str]) -> str:
    block = match.group(0)
    name_match = re.search(r"<name>\s*(.*?)\s*</name>", block, re.IGNORECASE | re.DOTALL)
    if not name_match:
        return "[已省略 skill 原文]"
    name = re.sub(r"\s+", " ", name_match.group(1)).strip()
    return f"[已省略 skill 原文：{name}]" if name else "[已省略 skill 原文]"


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if any(char in text for char in [":", "#", "\n", "'", '"']):
        return json.dumps(text, ensure_ascii=False)
    return text
