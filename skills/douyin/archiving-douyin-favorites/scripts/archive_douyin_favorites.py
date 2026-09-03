#!/usr/bin/env python3
"""Write and verify local page/detail pairs for one Douyin favorites batch."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import sys
import tempfile
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DOWNLOADS_ROOT = Path("/Users/oriki/Downloads")
DESTINATION_SUFFIX = "Archived DouYin Favorites"
DETAIL_SUFFIX = " 详情.md"
CANONICAL_URL = re.compile(
    r"https://www\.douyin\.com/(?P<type>video|note)/(?P<id>[0-9]+)"
)
UNSAFE_FILENAME = re.compile(r"[\\/:*?\"<>|\x00-\x1f\x7f]+")


def _require_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if value is None:
        return ""
    if not isinstance(value, (str, int)):
        raise ValueError(f"{key} must be text")
    return str(value).strip()


def _text_list(item: dict[str, Any], key: str) -> list[str]:
    value = item.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
        raise ValueError(f"{key} must be a list of strings")
    return [entry.strip() for entry in value if entry.strip()]


def _validate_item(raw_item: Any) -> dict[str, Any]:
    if not isinstance(raw_item, dict):
        raise ValueError("each item must be a JSON object")

    content_id = _require_text(raw_item, "id")
    content_type = _require_text(raw_item, "type")
    url = _require_text(raw_item, "url")
    match = CANONICAL_URL.fullmatch(url)
    if match is None:
        raise ValueError(f"{content_id or '<missing>'}: canonical Douyin URL required")
    if not content_id or match.group("id") != content_id:
        raise ValueError(f"{content_id or '<missing>'}: URL content ID does not match")
    if content_type not in {"video", "note"} or match.group("type") != content_type:
        raise ValueError(f"{content_id}: URL content type does not match")

    title = _require_text(raw_item, "title") or "DouYin 收藏"
    tags = ["DouYin", "DouYin Favorites", *_text_list(raw_item, "tags")]
    tags = list(dict.fromkeys(tags))

    return {
        "id": content_id,
        "type": content_type,
        "url": url,
        "title": title,
        "author": _require_text(raw_item, "author") or "insufficient metadata",
        "caption": _require_text(raw_item, "caption") or "insufficient metadata",
        "facts": _text_list(raw_item, "facts"),
        "summary": _require_text(raw_item, "summary") or "insufficient metadata",
        "inferences": _text_list(raw_item, "inferences"),
        "tags": tags,
        "cautions": _text_list(raw_item, "cautions"),
        "archive_status": (
            _require_text(raw_item, "archive_status") or "archived; pending unfavorite"
        ),
    }


def _validate_batch(raw_items: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("items must be a non-empty JSON array")

    items = [_validate_item(item) for item in raw_items]
    ids = [item["id"] for item in items]
    urls = [item["url"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate content ID in input batch")
    if len(urls) != len(set(urls)):
        raise ValueError("duplicate canonical URL in input batch")
    return items


def _validate_date(archive_date: str | None) -> str:
    value = archive_date or date.today().isoformat()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("archive date must use YYYY-MM-DD") from exc
    return value


def _safe_title(title: str, max_length: int = 80) -> str:
    normalized = unicodedata.normalize("NFKC", title)
    normalized = UNSAFE_FILENAME.sub(" ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip(" .-")
    return (normalized[:max_length].rstrip(" .-") or "DouYin 收藏")


def _list_markdown(values: Iterable[str], empty: str = "insufficient metadata") -> str:
    entries = list(values)
    return "\n".join(f"- {entry}" for entry in entries) if entries else f"- {empty}"


def _render_detail(item: dict[str, Any], link_name: str) -> str:
    return (
        f"# {item['title']}\n\n"
        f"- 内容 ID：`{item['id']}`\n"
        f"- 内容类型：`{item['type']}`\n"
        f"- 原始链接：{item['url']}\n"
        f"- 页面文件：`{link_name}`\n"
        f"- 作者：{item['author']}\n"
        f"- 标签：{', '.join(item['tags'])}\n"
        f"- 归档状态：{item['archive_status']}\n\n"
        "## 页面文案\n\n"
        f"{item['caption']}\n\n"
        "## 可见事实\n\n"
        f"{_list_markdown(item['facts'])}\n\n"
        "## 事实摘要\n\n"
        f"{item['summary']}\n\n"
        "## 推断\n\n"
        f"{_list_markdown(item['inferences'], '无')}\n\n"
        "## 风险提示\n\n"
        f"{_list_markdown(item['cautions'], '无')}\n"
    )


def _atomic_write(path: Path, content: bytes) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _existing_base(destination: Path, item: dict[str, Any]) -> str | None:
    content_id = item["id"]
    links = list(destination.glob(f"*--{content_id}.webloc"))
    details = list(destination.glob(f"*--{content_id}{DETAIL_SUFFIX}"))
    if not links and not details:
        return None
    if len(links) != 1 or len(details) != 1:
        raise ValueError("incomplete existing pair or ambiguous files")

    link_base = links[0].name[: -len(".webloc")]
    detail_base = details[0].name[: -len(DETAIL_SUFFIX)]
    if link_base != detail_base:
        raise ValueError("incomplete existing pair or mismatched filenames")
    try:
        existing_url = plistlib.loads(links[0].read_bytes()).get("URL")
    except (OSError, plistlib.InvalidFileException, AttributeError) as exc:
        raise ValueError("existing page link is unreadable") from exc
    if existing_url != item["url"]:
        raise ValueError("existing pair URL conflicts with content ID")
    return link_base


def _verify_pair(link_path: Path, detail_path: Path, item: dict[str, Any]) -> None:
    try:
        link_url = plistlib.loads(link_path.read_bytes()).get("URL")
        detail = detail_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, plistlib.InvalidFileException, AttributeError) as exc:
        raise ValueError("written pair cannot be read back") from exc
    if link_url != item["url"]:
        raise ValueError("written page link URL mismatch")
    required_detail_values = (item["id"], item["url"], link_path.name)
    if any(value not in detail for value in required_detail_values):
        raise ValueError("written detail file is missing ID, URL, or page filename")


def archive_items(
    raw_items: Any,
    *,
    downloads_root: Path = DEFAULT_DOWNLOADS_ROOT,
    archive_date: str | None = None,
) -> dict[str, Any]:
    """Write and verify one local file pair for every valid batch item."""

    items = _validate_batch(raw_items)
    day = _validate_date(archive_date)
    destination = Path(downloads_root) / f"{day} {DESTINATION_SUFFIX}"
    destination.mkdir(parents=True, exist_ok=True)

    verified_ids: list[str] = []
    failed_items: list[dict[str, str]] = []
    for item in items:
        try:
            base = _existing_base(destination, item)
            if base is None:
                base = f"{_safe_title(item['title'])}--{item['id']}"
            link_path = destination / f"{base}.webloc"
            detail_path = destination / f"{base}{DETAIL_SUFFIX}"

            link_content = plistlib.dumps(
                {"URL": item["url"]}, fmt=plistlib.FMT_XML, sort_keys=True
            )
            detail_content = _render_detail(item, link_path.name).encode("utf-8")
            _atomic_write(link_path, link_content)
            _atomic_write(detail_path, detail_content)
            _verify_pair(link_path, detail_path, item)
            verified_ids.append(item["id"])
        except (OSError, ValueError) as exc:
            failed_items.append({"id": item["id"], "error": str(exc)})

    return {
        "destination": str(destination),
        "verified_ids": verified_ids,
        "failed_items": failed_items,
        "pairs_written": len(verified_ids),
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and verify Douyin .webloc/detail pairs from JSON on stdin."
    )
    parser.add_argument("--date", help="Archive date in YYYY-MM-DD; defaults to today.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        raw_items = payload.get("items") if isinstance(payload, dict) else payload
        result = archive_items(
            raw_items,
            downloads_root=DEFAULT_DOWNLOADS_ROOT,
            archive_date=args.date,
        )
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["failed_items"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
