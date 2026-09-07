#!/usr/bin/env python3
"""Save and verify an AI conversation pair. Python 3.10+, macOS/Linux, stdlib only."""
from __future__ import annotations

import argparse
from datetime import date
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import quote, unquote

SECTIONS = ('背景', '处理过程', '结果', '决策', '经验教训', '疑难问题', '后续事项')
ROLES = {'user': '用户', 'assistant': 'AI'}


class ArchiveError(OSError):
    def __init__(self, message: str, paths: dict[str, str]):
        super().__init__(message)
        self.paths = paths


def normalize_body(value: object) -> str:
    """Demote embedded headings, preserving fenced code and ordinary wording."""
    if not isinstance(value, str) or not value.strip() or '\x00' in value:
        raise ValueError('Every message and retrospective section must be nonempty text')
    lines = value.replace('\r\n', '\n').replace('\r', '\n').strip().splitlines()
    output = []
    fence = None
    for line in lines:
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            output.append(line)
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            output.append(line)
            continue
        # Setext headings would otherwise become top-level headings on rendering.
        if re.fullmatch(r' {0,3}(?:=+|-+)\s*', line) and output and output[-1].strip():
            output[-1] = '### ' + output[-1].lstrip('# ').strip()
            output.append('')
            continue
        heading = re.match(r'^ {0,3}#{1,6}\s+(.*)$', line)
        if heading:
            output.extend(['### ' + heading[1], ''])
        else:
            output.append(line)
    if fence:
        raise ValueError('Unclosed fenced code block; fix the input before saving')
    return '\n'.join(output).strip() + '\n'


def prepare(data: object) -> tuple[str, str, dict[str, str]]:
    if not isinstance(data, dict):
        raise ValueError('Input must be a JSON object')
    title = data.get('title')
    if not isinstance(title, str) or not title.strip():
        raise ValueError('title must be nonempty text')
    title = title.strip()
    if len(title.encode('utf-8')) > 150 or re.search(r'[\x00-\x1f\x7f/\\:]', title) or title in {'.', '..'}:
        raise ValueError('title must be at most 150 UTF-8 bytes with no slashes, controls, or colons')
    messages = data.get('messages')
    if not isinstance(messages, list) or not messages:
        raise ValueError('messages must be a nonempty list of user/assistant messages')
    transcript = []
    for message in messages:
        if (not isinstance(message, dict) or not isinstance(message.get('role'), str)
                or message['role'] not in ROLES):
            raise ValueError('Each message role must be user or assistant')
        transcript.append('## ' + ROLES[message['role']] + '\n\n' + normalize_body(message.get('content')))
    retrospective = data.get('retrospective')
    if not isinstance(retrospective, dict) or set(retrospective) != set(SECTIONS):
        raise ValueError('retrospective must contain exactly: ' + ', '.join(SECTIONS))
    sections = {key: normalize_body(retrospective[key]) for key in SECTIONS}
    return title, '\n'.join(transcript), sections


def preflight(downloads: Path) -> Path:
    downloads = downloads.expanduser().resolve(strict=True)
    if not downloads.is_dir():
        raise OSError('Downloads path is not a directory')
    with tempfile.TemporaryFile(dir=downloads) as probe:
        probe.write(b'archive-access-check')
        probe.flush()
        probe.seek(0)
        if probe.read() != b'archive-access-check':
            raise OSError('Downloads read-back probe failed')
    return downloads


def write_exclusive(path: Path, text: str) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def archive(data: object, downloads: Path, day: str | None = None) -> dict:
    title, transcript, sections = prepare(data)
    day = day or date.today().isoformat()
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError('date must use YYYY-MM-DD')
    downloads = preflight(downloads)
    directory = downloads / (day + ' Archived AI Conversations')
    directory.mkdir(exist_ok=True)
    if directory.is_symlink() or directory.resolve().parent != downloads:
        raise OSError('Daily archive directory must reside directly inside Downloads')
    # Keep the lock inode: unlinking it can let concurrent writers use different locks.
    lock_fd = os.open(directory / '.archive.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        counter = 1
        while True:
            phrase = title if counter == 1 else f'{title} {counter}'
            stem = f'{day} {phrase}'
            original = directory / (stem + '（AI 对话原文）.md')
            summary = directory / (stem + '（AI 对话归档）.md')
            if not any(os.path.lexists(p) for p in (original, summary)):
                break
            counter += 1
        paths = {'directory': str(directory), 'transcript': str(original), 'retrospective': str(summary)}
        target = quote(original.name, safe='')
        retrospective = '\n'.join('## ' + key + '\n\n' + sections[key] for key in SECTIONS[:-1])
        retrospective += '\n## 原文记录\n\n[原文](' + target + ')\n'
        retrospective += '\n## 后续事项\n\n' + sections['后续事项']
        try:
            write_exclusive(original, transcript)
            write_exclusive(summary, retrospective)
            for path, expected in ((original, transcript), (summary, retrospective)):
                if path.is_symlink() or path.resolve().parent != directory:
                    raise OSError('Archive path escaped the daily directory')
                if path.read_bytes() != expected.encode('utf-8'):
                    raise OSError('Read-back mismatch: ' + str(path))
            if (directory / unquote(target)).resolve() != original.resolve():
                raise OSError('Transcript link does not resolve to the saved file')
        except (OSError, UnicodeError) as exc:
            raise ArchiveError(str(exc), paths) from exc
    return {'verified': True, **paths}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('preflight', 'save'))
    parser.add_argument('--downloads-dir', type=Path, default=Path.home() / 'Downloads',
                        help='Actual user Downloads directory; default: ~/Downloads')
    parser.add_argument('--input', type=Path, help='UTF-8 JSON input file; default: stdin')
    args = parser.parse_args()
    try:
        if args.command == 'preflight':
            result = {'writable': True, 'downloads': str(preflight(args.downloads_dir))}
        else:
            data = json.loads(args.input.read_text(encoding='utf-8')) if args.input else json.load(sys.stdin)
            result = archive(data, args.downloads_dir)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({'verified': False, 'error': str(exc),
                          **getattr(exc, 'paths', {})}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
