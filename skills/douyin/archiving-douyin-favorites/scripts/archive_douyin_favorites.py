#!/usr/bin/env python3
"""Write and verify local page/cover pairs for one Douyin favorites batch."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


DEFAULT_DOWNLOADS_ROOT = Path("/Users/oriki/Downloads")
DESTINATION_SUFFIX = "Archived DouYin Favorites"
DETAIL_SUFFIX = " 详情.md"  # Reserve legacy filenames; never rewrite old details.
COVER_SUFFIX = " 封面"
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
MAX_COVER_BYTES = 20 * 1024 * 1024
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

    cover_url = _require_text(raw_item, "cover_url")
    parsed = urlsplit(cover_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{content_id}: HTTPS cover URL required")
    title = _require_text(raw_item, "title") or "DouYin 收藏"
    return {
        "id": content_id,
        "type": content_type,
        "url": url,
        "title": title,
        "cover_url": cover_url,
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
    matches = []
    for link in destination.glob("*.webloc"):
        try:
            url = plistlib.loads(link.read_bytes()).get("URL")
        except (OSError, plistlib.InvalidFileException, AttributeError):
            if link.stem.endswith(f"--{item['id']}"):
                raise ValueError("existing ID link is unreadable")
            continue
        if link.stem.endswith(f"--{item['id']}") and url != item["url"]:
            raise ValueError("existing ID link conflicts with URL")
        if url == item["url"]:
            if link.is_symlink():
                raise ValueError("existing link is a symlink")
            matches.append(link.stem)
    if len(matches) > 1:
        raise ValueError("ambiguous existing links for content ID")
    return matches[0] if matches else None


def _cover_files(destination: Path, base: str) -> list[Path]:
    # Literal prefix comparison: titles may contain glob metacharacters.
    return [p for p in destination.iterdir() if p.name.startswith(base + COVER_SUFFIX + ".")]


def _available_base(destination: Path, title: str) -> str:
    base = _safe_title(title)
    candidate = base
    suffix = 2
    while (
        (destination / f"{candidate}.webloc").exists()
        or (destination / f"{candidate}{DETAIL_SUFFIX}").exists()
        or _cover_files(destination, candidate)
    ):
        candidate = f"{base} ({suffix})"
        suffix += 1
    return candidate


def _image_extension(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_COVER_BYTES:
        raise ValueError("cover is missing, empty, oversized, or a symlink")
    mime = subprocess.run(
        ["file", "--brief", "--mime-type", str(path)],
        capture_output=True, text=True, check=True, timeout=15,
    ).stdout.strip()
    if mime not in IMAGE_TYPES:
        raise ValueError(f"unsupported cover image MIME: {mime}")
    # ImageIO must also be able to read dimensions; MIME alone can accept broken files.
    dimensions = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True, text=True, check=True, timeout=15,
    ).stdout
    for key in ("pixelWidth", "pixelHeight"):
        if not re.search(rf"{key}: [1-9][0-9]*", dimensions):
            raise ValueError("cover image cannot be read")
    return IMAGE_TYPES[mime]


def _download_cover(item: dict[str, Any], destination: Path) -> tuple[bytes, str]:
    request = urllib.request.Request(item["cover_url"], headers={
        "User-Agent": "Mozilla/5.0", "Referer": "https://www.douyin.com/",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read(MAX_COVER_BYTES + 1)
    if not content or len(content) > MAX_COVER_BYTES:
        raise ValueError("cover download is empty or oversized")
    with tempfile.NamedTemporaryFile(dir=destination, prefix=".cover-", suffix=".part") as handle:
        handle.write(content)
        handle.flush()
        extension = _image_extension(Path(handle.name))
    return content, extension


def _verify_pair(link_path: Path, cover_path: Path, item: dict[str, Any]) -> None:
    try:
        link_url = plistlib.loads(link_path.read_bytes()).get("URL")
    except (OSError, plistlib.InvalidFileException, AttributeError) as exc:
        raise ValueError("written link cannot be read back") from exc
    if link_url != item["url"]:
        raise ValueError("written page link URL mismatch")
    extension = _image_extension(cover_path)
    if cover_path.suffix != "." + extension:
        raise ValueError("cover extension does not match image format")


def archive_items(
    raw_items: Any,
    *,
    downloads_root: Path = DEFAULT_DOWNLOADS_ROOT,
    archive_date: str | None = None,
) -> dict[str, Any]:
    """Write and verify one local link/cover pair for every valid batch item."""

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
                base = _available_base(destination, item["title"])
            link_path = destination / f"{base}.webloc"
            covers = _cover_files(destination, base)
            if len(covers) > 1:
                raise ValueError("ambiguous existing cover files")
            if covers:
                cover_path = covers[0]
                _verify_pair(link_path, cover_path, item)
            else:
                content, extension = _download_cover(item, destination)
                cover_path = destination / f"{base}{COVER_SUFFIX}.{extension}"
                if not link_path.exists():
                    _atomic_write(link_path, plistlib.dumps({"URL": item["url"]}, fmt=plistlib.FMT_XML))
                _atomic_write(cover_path, content)
                _verify_pair(link_path, cover_path, item)
            verified_ids.append(item["id"])
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            failed_items.append({"id": item["id"], "error": str(exc)})

    return {
        "destination": str(destination),
        "verified_ids": verified_ids,
        "failed_items": failed_items,
        "pairs_written": len(verified_ids),
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and verify Douyin .webloc/cover pairs from JSON."
    )
    parser.add_argument("--date", help="Archive date in YYYY-MM-DD; defaults to today.")
    parser.add_argument(
        "--input",
        type=Path,
        help="Read batch JSON from this file instead of standard input.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.input is None:
            payload = json.load(sys.stdin)
        else:
            with args.input.open(encoding="utf-8") as input_handle:
                payload = json.load(input_handle)
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
