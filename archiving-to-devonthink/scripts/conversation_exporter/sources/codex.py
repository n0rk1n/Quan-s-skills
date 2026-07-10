from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from conversation_exporter.model import Conversation, ExportWarning, Message, ParseResult, ToolCall
from conversation_exporter.utils import plain_text_from_parts, to_iso_datetime, truncate_text


DEVONTHINK_SUFFIXES = (".dtBase2", ".dtSparse", ".dtArchive")
TOOL_CALL_TYPES = {"function_call", "custom_tool_call", "tool_search_call", "web_search_call"}
TOOL_OUTPUT_TYPES = {"function_call_output", "custom_tool_call_output", "tool_search_output"}
TOOL_NAME_BY_TYPE = {
    "tool_search_call": "tool_search",
    "web_search_call": "web_search",
}


def default_codex_paths(home: Path | None = None) -> list[Path]:
    root = home or Path.home()
    return [root / ".codex" / "sessions", root / ".codex" / "archived_sessions"]


def discover_rollout_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file() and path.name.endswith(".jsonl"):
            if _is_safe_path(path):
                files.append(path)
            continue
        if not _is_safe_path(path):
            continue
        for root, directories, filenames in os.walk(path, topdown=True):
            directories[:] = [
                directory for directory in directories if not directory.endswith(DEVONTHINK_SUFFIXES)
            ]
            for filename in filenames:
                if filename.startswith("rollout-") and filename.endswith(".jsonl"):
                    files.append(Path(root) / filename)
    return sorted(files)


def parse_codex_paths(paths: list[Path]) -> ParseResult:
    result = ParseResult()
    for path in paths:
        if not path.exists():
            result.skipped.append(str(path))
            continue
        files = [path] if path.is_file() else discover_rollout_files([path])
        if not files:
            result.skipped.append(str(path))
            continue
        for file_path in files:
            file_result = parse_codex_file(file_path)
            result.conversations.extend(file_result.conversations)
            result.warnings.extend(file_result.warnings)
            result.skipped.extend(file_result.skipped)
    return result


def parse_codex_file(path: Path) -> ParseResult:
    result = ParseResult()
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        result.skipped.append(str(path))
        result.warnings.append(ExportWarning(str(path), f"Read failed: {exc}"))
        return result

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            result.warnings.append(ExportWarning(str(path), f"Invalid JSON on line {line_number}: {exc.msg}"))
            continue
        if not isinstance(event, dict):
            result.warnings.append(ExportWarning(str(path), f"Expected JSON object on line {line_number}"))
            continue
        events.append(event)

    if not events:
        result.skipped.append(str(path))
        return result

    conversation = _conversation_from_events(path, events)
    conversation.stats.warning_count = len(result.warnings)
    result.conversations.append(conversation)
    return result


def _conversation_from_events(path: Path, events: list[dict[str, Any]]) -> Conversation:
    metadata: dict[str, Any] = {"source_path": str(path)}
    conversation_id = _id_from_path(path)
    created_at = None
    updated_at = None
    messages: list[Message] = []
    pending_calls: dict[str, ToolCall] = {}
    pending_outputs: dict[str, str] = {}

    for event in events:
        event_type = event.get("type")
        timestamp = to_iso_datetime(event.get("timestamp"))
        if timestamp:
            created_at = created_at or timestamp
            updated_at = timestamp
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if event_type == "session_meta":
            conversation_id = str(payload.get("id") or payload.get("session_id") or conversation_id)
            for key in ("session_id", "cwd", "model_provider", "originator", "source", "thread_source"):
                if payload.get(key) is not None:
                    metadata[key] = payload[key]
        elif event_type == "turn_context":
            for key in ("model", "cwd", "current_date", "timezone"):
                if payload.get(key) is not None:
                    metadata[key] = payload[key]
        elif event_type == "response_item":
            _consume_response_item(payload, timestamp, messages, pending_calls, pending_outputs)
        elif event_type == "event_msg":
            _consume_event_msg(payload, pending_calls, pending_outputs)

    title = _derive_title(messages, conversation_id)
    conversation = Conversation(
        source="codex",
        conversation_id=conversation_id,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
        metadata=metadata,
        messages=messages,
    )
    conversation.recompute_stats()
    return conversation


def _consume_response_item(
    payload: dict[str, Any],
    timestamp: str | None,
    messages: list[Message],
    pending_calls: dict[str, ToolCall],
    pending_outputs: dict[str, str],
) -> None:
    payload_type = payload.get("type")
    role = payload.get("role")
    if payload_type == "message" and role in {"user", "assistant"}:
        content = _content_to_text(payload.get("content"))
        if content or role == "assistant":
            messages.append(Message(role=role, created_at=timestamp, content=content))
    elif payload_type in TOOL_CALL_TYPES:
        tool_call = _tool_call_from_payload(payload_type, payload)
        _attach_tool_call(messages, tool_call)
        if tool_call.call_id:
            pending_calls[tool_call.call_id] = tool_call
            if tool_call.call_id in pending_outputs:
                tool_call.output_summary = pending_outputs.pop(tool_call.call_id)
    elif payload_type in TOOL_OUTPUT_TYPES:
        _consume_tool_output(payload, pending_calls, pending_outputs)


def _consume_event_msg(
    payload: dict[str, Any],
    pending_calls: dict[str, ToolCall],
    pending_outputs: dict[str, str],
) -> None:
    if payload.get("type") == "web_search_end":
        _consume_tool_output(payload, pending_calls, pending_outputs)


def _tool_call_from_payload(payload_type: str, payload: dict[str, Any]) -> ToolCall:
    call_id = payload.get("call_id") or payload.get("id")
    return ToolCall(
        name=str(payload.get("name") or TOOL_NAME_BY_TYPE.get(payload_type) or payload_type),
        call_id=str(call_id) if call_id is not None else None,
        arguments=_tool_arguments(payload),
        status=payload.get("status"),
    )


def _tool_arguments(payload: dict[str, Any]) -> Any:
    for key in ("arguments", "input", "action"):
        if key in payload:
            return payload[key]
    if "query" in payload:
        return {"query": payload["query"]}
    return None


def _consume_tool_output(
    payload: dict[str, Any],
    pending_calls: dict[str, ToolCall],
    pending_outputs: dict[str, str],
) -> None:
    call_id = payload.get("call_id") or payload.get("id")
    if call_id is None:
        return
    summary = _tool_output_summary(payload)
    if summary is None:
        return
    call_id_text = str(call_id)
    tool_call = pending_calls.get(call_id_text)
    if tool_call is not None:
        tool_call.output_summary = summary
    else:
        pending_outputs[call_id_text] = summary


def _tool_output_summary(payload: dict[str, Any]) -> str | None:
    if "output" in payload:
        return truncate_text(payload.get("output"), limit=800)
    if "tools" in payload:
        return truncate_text({"tools": payload.get("tools")}, limit=800)
    public_payload = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "type",
            "id",
            "call_id",
            "status",
            "execution",
            "internal_chat_message_metadata_passthrough",
        }
    }
    return truncate_text(public_payload, limit=800) if public_payload else None


def _attach_tool_call(messages: list[Message], tool_call: ToolCall) -> None:
    if not messages or messages[-1].role != "assistant":
        messages.append(Message(role="assistant", content=""))
    messages[-1].tool_calls.append(tool_call)


def _content_to_text(content: Any) -> str:
    if isinstance(content, list):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") in {"input_text", "output_text", "text"}:
                    pieces.append(plain_text_from_parts(item.get("text")))
                elif "text" in item:
                    pieces.append(plain_text_from_parts(item.get("text")))
                elif "content" in item:
                    pieces.append(plain_text_from_parts(item.get("content")))
            else:
                pieces.append(plain_text_from_parts(item))
        return "\n".join(piece for piece in pieces if piece)
    return plain_text_from_parts(content)


def _derive_title(messages: list[Message], fallback: str) -> str:
    for message in messages:
        if message.role == "user" and message.content.strip():
            return message.content.strip().splitlines()[0][:60]
    return fallback


def _id_from_path(path: Path) -> str:
    stem = path.stem
    return stem.split("-")[-1] if "-" in stem else stem


def _is_safe_path(path: Path) -> bool:
    return not any(part.endswith(DEVONTHINK_SUFFIXES) for part in path.parts)
