from __future__ import annotations

from pathlib import Path

from conversation_exporter.model import Conversation
from conversation_exporter.renderers.markdown import render_conversation
from conversation_exporter.utils import sanitize_filename, short_id


DEVONTHINK_SUFFIXES = (".dtBase2", ".dtSparse", ".dtArchive")


class UnsafeOutputPathError(ValueError):
    pass


def write_conversations(
    conversations: list[Conversation],
    out_dir: Path,
    protected_roots: list[Path] | None = None,
) -> list[Path]:
    _assert_safe_output_dir(out_dir, protected_roots or [])
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    used_names: set[str] = set()
    for conversation in conversations:
        path = _unique_path(conversation, out_dir, used_names)
        path.write_text(render_conversation(conversation), encoding="utf-8")
        written.append(path)
        used_names.add(path.name)
    return written


def _assert_safe_output_dir(out_dir: Path, protected_roots: list[Path]) -> None:
    resolved_out = out_dir.resolve(strict=False)
    if _is_inside_devonthink_package(resolved_out):
        raise UnsafeOutputPathError(f"Refusing to write inside DEVONthink package: {out_dir}")

    for root in protected_roots:
        resolved_root = root.resolve(strict=False)
        if _is_inside_devonthink_package(resolved_root):
            continue
        if root.exists() and root.is_dir() and _is_relative_to(resolved_out, resolved_root):
            raise UnsafeOutputPathError(f"Refusing to write inside source input directory: {out_dir}")
        if root.exists() and root.is_file() and resolved_out == resolved_root.parent:
            raise UnsafeOutputPathError(f"Refusing to write next to source input file: {out_dir}")


def _is_inside_devonthink_package(path: Path) -> bool:
    return any(part.endswith(DEVONTHINK_SUFFIXES) for part in path.parts)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _unique_path(conversation: Conversation, out_dir: Path, used_names: set[str]) -> Path:
    date = _date_part(conversation)
    title = sanitize_filename(conversation.title, fallback=conversation.conversation_id)[:80]
    identifier = short_id(conversation.conversation_id, 10)
    name = f"{date} {title} {identifier}.md"
    counter = 2
    while name in used_names or (out_dir / name).exists():
        name = f"{date} {title} {identifier}-{counter}.md"
        counter += 1
    return out_dir / name


def _date_part(conversation: Conversation) -> str:
    value = conversation.created_at or conversation.updated_at or ""
    if len(value) >= 10 and value[4:5] == "-" and value[7:8] == "-":
        return value[:10]
    return "unknown-date"
