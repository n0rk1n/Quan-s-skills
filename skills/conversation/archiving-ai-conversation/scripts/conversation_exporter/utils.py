from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json
import re


UNSAFE_FILENAME_RE = re.compile(r"[\\/:*?\"<>|]+")
BLOCK_PREFIX_RE = r"(?:(?: {0,3}>[ \t]?)|(?:[ \t]*(?:[-+*]|\d+[.)])[ \t]+))*"
ATX_HEADING_RE = re.compile(
    rf"^(?P<prefix>{BLOCK_PREFIX_RE})(?P<indent> {{0,3}})"
    r"#{1,6}(?=[ \t]+|$)(?P<suffix>.*)$",
    re.MULTILINE,
)
SETEXT_HEADING_RE = re.compile(
    r"^(?P<prefix>(?: {0,3}>[ \t]?)*)(?P<indent> {0,3})"
    r"(?P<title>\S(?:.*?\S)?)[ \t]*\n"
    r"(?P=prefix) {0,3}(?:=+|-+)[ \t]*$",
    re.MULTILINE,
)
LIST_SETEXT_TITLE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>[-+*]|\d+[.)])(?P<space>[ \t]+)"
    r"(?P<title>\S(?:.*?\S)?)[ \t]*$"
)
FENCE_OPEN_RE = re.compile(
    rf"^(?:{BLOCK_PREFIX_RE}) {{0,3}}(?P<fence>`{{3,}}|~{{3,}}).*$"
)


def to_iso_datetime(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def plain_text_from_parts(parts: object) -> str:
    if parts is None:
        return ""
    if isinstance(parts, str):
        return parts
    if isinstance(parts, list):
        values = [plain_text_from_parts(part) for part in parts]
        return "\n".join(value for value in values if value)
    if isinstance(parts, dict):
        if "text" in parts:
            return plain_text_from_parts(parts["text"])
        if "parts" in parts:
            return plain_text_from_parts(parts["parts"])
        if "content" in parts:
            return plain_text_from_parts(parts["content"])
    return str(parts)


def sanitize_heading_depth(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    sanitized: list[str] = []
    fence: str | None = None
    index = 0

    while index < len(lines):
        line, ending = _split_line_ending(lines[index])
        if fence is not None:
            sanitized.append(lines[index])
            if _is_fence_close(line, fence):
                fence = None
            index += 1
            continue

        opening_fence = FENCE_OPEN_RE.fullmatch(line)
        if opening_fence:
            fence = opening_fence.group("fence")
            sanitized.append(lines[index])
            index += 1
            continue

        if index + 1 < len(lines):
            underline, underline_ending = _split_line_ending(lines[index + 1])
            replacement = _normalize_setext_pair(line, underline)
            if replacement is not None:
                sanitized.append(replacement + underline_ending)
                index += 2
                continue

        sanitized.append(_normalize_atx_heading(line) + ending)
        index += 1

    return "".join(sanitized)


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith(("\n", "\r")):
        return line[:-1], line[-1]
    return line, ""


def _is_fence_close(line: str, fence: str) -> bool:
    return re.fullmatch(
        rf"(?:{BLOCK_PREFIX_RE})? {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*",
        line,
    ) is not None


def _normalize_setext_pair(title_line: str, underline_line: str) -> str | None:
    matched = LIST_SETEXT_TITLE_RE.fullmatch(title_line)
    if matched and re.fullmatch(rf"{re.escape(matched.group('indent'))}[ \t]+(?:=+|-+)[ \t]*", underline_line):
        return (
            matched.group("indent")
            + matched.group("marker")
            + matched.group("space")
            + "### "
            + matched.group("title")
        )

    matched = SETEXT_HEADING_RE.fullmatch(f"{title_line}\n{underline_line}")
    if matched:
        return matched.group("prefix") + matched.group("indent") + "### " + matched.group("title")
    return None


def _normalize_atx_heading(line: str) -> str:
    return ATX_HEADING_RE.sub(
        lambda match: match.group("prefix") + match.group("indent") + "###" + match.group("suffix"),
        line,
    )


def sanitize_filename(value: str, fallback: str = "conversation") -> str:
    cleaned = UNSAFE_FILENAME_RE.sub("-", value).strip(" .-_")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or fallback


def short_id(value: str, length: int = 8) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", value)
    return (cleaned or "conversation")[:length]


def truncate_text(value: Any, limit: int = 800) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            text = str(value)
    if len(text) <= limit:
        return text
    return text[:limit] + "..."
