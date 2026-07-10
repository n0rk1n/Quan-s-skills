from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from conversation_exporter.model import Conversation, ExportWarning, Message, ParseResult
from conversation_exporter.utils import plain_text_from_parts, to_iso_datetime


def load_chatgpt_export(path: Path) -> ParseResult:
    result = ParseResult()
    try:
        records = _load_records(path)
    except (OSError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile, KeyError) as exc:
        result.warnings.append(ExportWarning(str(path), f"Could not load conversations.json: {exc}"))
        return result
    return parse_chatgpt_conversations(records)


def parse_chatgpt_conversations(records: list[dict[str, Any]]) -> ParseResult:
    result = ParseResult()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            result.warnings.append(ExportWarning(f"conversation[{index}]", "Conversation record is not an object"))
            continue
        conversation = _parse_conversation(record, index)
        conversation.stats.warning_count = 0
        result.conversations.append(conversation)
    return result


def _load_records(path: Path) -> list[dict[str, Any]]:
    if path.is_dir():
        return json.loads((path / "conversations.json").read_text(encoding="utf-8"))
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            with archive.open("conversations.json") as handle:
                return json.loads(handle.read().decode("utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_conversation(record: dict[str, Any], index: int) -> Conversation:
    conversation_id = str(record.get("id") or f"chatgpt-{index}")
    mapping = record.get("mapping") if isinstance(record.get("mapping"), dict) else {}
    node_ids = _ordered_node_ids(mapping, record.get("current_node"))
    messages: list[Message] = []
    for node_id in node_ids:
        node = mapping.get(node_id) if isinstance(mapping.get(node_id), dict) else {}
        message = node.get("message") if isinstance(node.get("message"), dict) else None
        parsed = _parse_message(message)
        if parsed is not None:
            messages.append(parsed)

    title = str(record.get("title") or _derive_title(messages, conversation_id))
    conversation = Conversation(
        source="chatgpt",
        conversation_id=conversation_id,
        title=title,
        created_at=to_iso_datetime(record.get("create_time")),
        updated_at=to_iso_datetime(record.get("update_time")),
        metadata={"source_format": "chatgpt_conversations_json"},
        messages=messages,
    )
    conversation.recompute_stats()
    return conversation


def _ordered_node_ids(mapping: dict[str, Any], current_node: Any) -> list[str]:
    if current_node and current_node in mapping:
        ordered: list[str] = []
        node_id = current_node
        seen: set[str] = set()
        while node_id and node_id in mapping and node_id not in seen:
            seen.add(node_id)
            ordered.append(node_id)
            node = mapping.get(node_id)
            if not isinstance(node, dict):
                break
            node_id = node.get("parent")
        return list(reversed(ordered))
    return sorted(mapping, key=lambda item: _message_time(mapping.get(item)))


def _message_time(node: Any) -> float:
    if not isinstance(node, dict):
        return 0
    message = node.get("message")
    if not isinstance(message, dict):
        return 0
    value = message.get("create_time")
    return float(value) if isinstance(value, (int, float)) else 0


def _parse_message(message: dict[str, Any] | None) -> Message | None:
    if not message:
        return None
    author = message.get("author") if isinstance(message.get("author"), dict) else {}
    role = author.get("role")
    if role not in {"user", "assistant"}:
        return None
    content = message.get("content") if isinstance(message.get("content"), dict) else {}
    text = plain_text_from_parts(content.get("parts") if "parts" in content else content)
    if not text:
        return None
    return Message(role=role, content=text, created_at=to_iso_datetime(message.get("create_time")))


def _derive_title(messages: list[Message], fallback: str) -> str:
    for message in messages:
        if message.role == "user" and message.content.strip():
            return message.content.strip().splitlines()[0][:60]
    return fallback
