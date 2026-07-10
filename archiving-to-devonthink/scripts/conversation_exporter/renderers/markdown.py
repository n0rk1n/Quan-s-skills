from __future__ import annotations

import json
import re
from typing import Any

from conversation_exporter.model import Conversation, Message, ToolCall
from conversation_exporter.utils import sanitize_heading_depth, truncate_text


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
    parts = [heading, "", sanitize_heading_depth(message.content).strip()]
    rendered_message = "\n".join(parts).rstrip()
    if message.role == "user" and message.tool_calls:
        return "\n\n".join([rendered_message, "## AI", "\n\n".join(render_tool_call(call) for call in message.tool_calls)])
    for tool_call in message.tool_calls:
        parts.extend(["", render_tool_call(tool_call)])
    return "\n".join(parts).rstrip()


def render_tool_call(tool_call: ToolCall) -> str:
    parts = [f"### 工具调用：{_tool_name_label(tool_call.name)}", ""]
    if tool_call.call_id:
        parts.extend([f"- call_id: `{_tool_name_label(tool_call.call_id)}`"])
    if tool_call.status:
        parts.extend([f"- status: `{_tool_name_label(tool_call.status)}`"])
    if tool_call.arguments not in (None, "", {}):
        parts.extend(["", "```json", _json_dump_limited(tool_call.arguments), "```"])
    if tool_call.output_summary:
        parts.extend(["", "### 工具输出摘要", "", _text_code_fence(truncate_text(tool_call.output_summary))])
    return "\n".join(parts)


def _json_dump_limited(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return json.dumps(truncate_text(value, limit=1200), ensure_ascii=False)
        return _json_dump_limited(parsed)
    try:
        rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    except TypeError:
        return json.dumps(truncate_text(value, limit=1200), ensure_ascii=False)
    if len(rendered) > 1200:
        return json.dumps(truncate_text(value, limit=1200), ensure_ascii=False)
    return rendered


def _text_code_fence(value: str) -> str:
    text = value.rstrip("\n")
    longest_backtick_run = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest_backtick_run + 1)
    return f"{fence}text\n{text}\n{fence}"


def _tool_name_label(name: str) -> str:
    return re.sub(r"\s+", " ", str(name)).strip() or "unknown"


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if any(char in text for char in [":", "#", "\n", "'", '"']):
        return json.dumps(text, ensure_ascii=False)
    return text
