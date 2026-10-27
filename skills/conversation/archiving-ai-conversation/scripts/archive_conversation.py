#!/usr/bin/env python3
"""Save and verify an AI conversation, eligible SOPs, and non-Git artifacts. Python 3.10+, macOS/Linux, stdlib only."""
from __future__ import annotations

import argparse
from datetime import date
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import quote, unquote

SECTIONS = ('背景', '处理过程', '结果', '决策', '经验教训', '疑难问题', '后续事项')
SOP_SECTIONS = ('目的与适用场景', '前置条件与输入', '标准步骤或格式', '输出与验收标准', '异常处理与适用边界')
ROLES = {'user': '用户', 'assistant': 'AI'}


class ArchiveError(OSError):
    def __init__(self, message: str, paths: dict):
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


def validate_title(value: object) -> str:
    title = value
    if not isinstance(title, str) or not title.strip():
        raise ValueError('title must be nonempty text')
    title = title.strip()
    if len(title.encode('utf-8')) > 150 or re.search(r'[\x00-\x1f\x7f/\\:]', title) or title in {'.', '..'}:
        raise ValueError('title must be at most 150 UTF-8 bytes with no slashes, controls, or colons')
    return title


def prepare(data: object) -> tuple[str, str, dict[str, str]]:
    if not isinstance(data, dict):
        raise ValueError('Input must be a JSON object')
    title = validate_title(data.get('title'))
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


def prepare_sops(data: dict) -> tuple[list, list]:
    values = data.get('sops', [])
    if not isinstance(values, list):
        raise ValueError('sops must be a list')
    prepared = []
    skipped = []
    for sop in values:
        if not isinstance(sop, dict):
            raise ValueError('Each SOP must be an object')
        title = validate_title(sop.get('title'))
        scope = sop.get('scope', 'general')
        if scope not in ('general', 'archiving-ai-conversation'):
            raise ValueError('SOP scope must be general or archiving-ai-conversation')
        if scope == 'archiving-ai-conversation':
            skipped.append(title)
            continue
        sections = sop.get('sections')
        if not isinstance(sections, dict) or set(sections) != set(SOP_SECTIONS):
            raise ValueError('SOP sections must contain exactly: ' + ', '.join(SOP_SECTIONS))
        body = '\n'.join('## ' + key + '\n\n' + normalize_body(sections[key]) for key in SOP_SECTIONS)
        prepared.append((title, body))
    return prepared, skipped


def fingerprint(path: Path) -> tuple[int, str]:
    """Hash regular files in bounded memory; never follow a final symlink."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Artifact must be a regular file: ' + str(path))
        digest = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def git_tracking(path: Path) -> dict | None:
    """Query the file's own repository/index, including linked worktrees."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['LC_ALL'] = 'C'
    def git(*args):
        return subprocess.run(['git', '-C', str(path.parent), *args],
                              capture_output=True, env=env, timeout=30)
    try:
        root = git('rev-parse', '--show-toplevel')
        if root.returncode:
            if b'not a git repository' in root.stderr:
                return None
            raise OSError('Cannot determine artifact Git repository: ' + os.fsdecode(root.stderr))
        tracked = git('--literal-pathspecs', 'ls-files', '--cached', '-z', '--', path.name)
        if tracked.returncode:
            raise OSError('Cannot determine artifact Git tracking: ' + os.fsdecode(tracked.stderr))
        if tracked.stdout:
            return {'repository': os.fsdecode(root.stdout).rstrip('\n'), 'reason': 'git-tracked'}
        return None
    except subprocess.TimeoutExpired as exc:
        raise OSError('Git tracking check timed out: ' + str(path)) from exc


def prepare_artifacts(data: dict) -> tuple[list, list]:
    values = data.get('artifacts', [])
    if not isinstance(values, list):
        raise ValueError('artifacts must be a list of absolute file paths')
    prepared, skipped, seen = [], [], set()
    for value in values:
        if not isinstance(value, str) or not value or not Path(value).is_absolute():
            raise ValueError('Each artifact must be an absolute file path')
        path = Path(value)
        if path.is_symlink():
            raise ValueError('Supply the actual artifact file, not a symlink: ' + value)
        path = path.resolve(strict=True)
        if not path.is_file():
            raise ValueError('Artifact must be a regular file: ' + value)
        if path in seen:
            continue
        seen.add(path)
        tracking = git_tracking(path)
        if tracking:
            skipped.append({'source': str(path), **tracking})
        else:
            size, digest = fingerprint(path)
            prepared.append({'source': str(path), 'size': size, 'sha256': digest})
    return prepared, skipped


def copy_artifact(source: Path, destination: Path) -> None:
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as src:
        if not stat.S_ISREG(os.fstat(src.fileno()).st_mode):
            raise ValueError('Artifact must remain a regular file: ' + str(source))
        with destination.open('xb') as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())


def free_artifact_path(directory: Path, name: str, reserved: set) -> Path:
    # Leave room for collision suffixes even for a maximum-length source basename.
    suffix = Path(name).suffix
    if len(suffix.encode('utf-8')) > 40:
        suffix = ''
    stem = name[:-len(suffix)] if suffix else name
    stem = stem.encode('utf-8')[:180].decode('utf-8', errors='ignore')
    number = 1
    while True:
        tag = '' if number == 1 else f' {number}'
        candidate = directory / (stem + tag + suffix)
        if candidate not in reserved and not os.path.lexists(candidate):
            reserved.add(candidate)
            return candidate
        number += 1


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
    sops, skipped_sops = prepare_sops(data)
    artifacts, skipped_artifacts = prepare_artifacts(data)
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
            manifest = directory / (stem + '（文件清单）.json') if artifacts or skipped_artifacts else None
            if not any(os.path.lexists(p) for p in (original, summary, manifest) if p is not None):
                break
            counter += 1
        sop_outputs = []
        reserved = {original, summary, manifest}
        for sop_title, body in sops:
            number = 1
            while True:
                phrase = sop_title if number == 1 else f'{sop_title} {number}'
                path = directory / f'{day} {phrase}（SOP）.md'
                if path not in reserved and not os.path.lexists(path):
                    break
                number += 1
            reserved.add(path)
            content = '# ' + sop_title + '\n\n' + body
            content += '\n## 原文记录\n\n[原文](' + quote(original.name, safe='') + ')\n'
            sop_outputs.append((path, content))
        for entry in artifacts:
            entry['path'] = str(free_artifact_path(directory, Path(entry['source']).name, reserved))
        paths = {'sops': [str(path) for path, _ in sop_outputs], 'directory': str(directory),
                 'transcript': str(original), 'retrospective': str(summary),
                 'artifacts': artifacts, 'skipped_artifacts': skipped_artifacts,
                 'artifact_manifest': str(manifest) if manifest else None, 'skipped_sops': skipped_sops}
        target = quote(original.name, safe='')
        retrospective = '\n'.join('## ' + key + '\n\n' + sections[key] for key in SECTIONS[:-1])
        retrospective += '\n## 原文记录\n\n[原文](' + target + ')\n'
        retrospective += '\n## 后续事项\n\n' + sections['后续事项']
        retrospective += '\n## SOP 文档\n\n'
        if sop_outputs:
            retrospective += ''.join('- [SOP ' + str(index) + '](' + quote(path.name, safe='') + ')\n'
                                     for index, (path, _) in enumerate(sop_outputs, 1))
        elif not skipped_sops:
            retrospective += '未发现可提炼的标准流程或标准格式。\n'
        if skipped_sops:
            retrospective += '已排除归档技能自身的流程或格式，共 ' + str(len(skipped_sops)) + ' 项。\n'
        if manifest:
            retrospective += '\n## 对话产物\n\n[文件清单](' + quote(manifest.name, safe='') + ')\n'
            for index, entry in enumerate(artifacts, 1):
                retrospective += '- [产物 ' + str(index) + '](' + quote(Path(entry['path']).name, safe='') + ')\n'
            retrospective += '已受 Git 跟踪的文件不重复复制，共 ' + str(len(skipped_artifacts)) + ' 项；详见清单。\n'
        outputs = [(original, transcript), (summary, retrospective), *sop_outputs]
        try:
            for path, content in outputs:
                write_exclusive(path, content)
            for entry in artifacts:
                source, destination = Path(entry['source']), Path(entry['path'])
                copy_artifact(source, destination)
                expected_fingerprint = (entry['size'], entry['sha256'])
                if fingerprint(destination) != expected_fingerprint or fingerprint(source) != expected_fingerprint:
                    raise OSError('Artifact hash mismatch or source changed: ' + str(source))
                if destination.is_symlink() or destination.resolve().parent != directory:
                    raise OSError('Artifact path escaped the daily directory')
            if manifest:
                content = json.dumps({'artifacts': artifacts, 'skipped_artifacts': skipped_artifacts},
                                     ensure_ascii=False, indent=2) + '\n'
                write_exclusive(manifest, content)
                outputs.append((manifest, content))
            for path, expected in outputs:
                if path.is_symlink() or path.resolve().parent != directory:
                    raise OSError('Archive path escaped the daily directory')
                if path.read_bytes() != expected.encode('utf-8'):
                    raise OSError('Read-back mismatch: ' + str(path))
            for path, _ in sop_outputs:
                if (directory / unquote(quote(path.name, safe=''))).resolve() != path.resolve():
                    raise OSError('SOP link does not resolve to the saved file')
            if (directory / unquote(target)).resolve() != original.resolve():
                raise OSError('Transcript link does not resolve to the saved file')
        except (OSError, ValueError, UnicodeError) as exc:
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
