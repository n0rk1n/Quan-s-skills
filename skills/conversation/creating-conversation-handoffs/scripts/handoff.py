#!/usr/bin/env python3
"""Publish validated handoffs and prepare a read-only resume bundle (Python 3.9+)."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Resume must not create bytecode in the installed skill directory.
sys.dont_write_bytecode = True
from handoff_contract import (  # noqa: E402
    LATEST_LINK, next_snapshot_path, validate_latest, validate_snapshot,
)


class HandoffError(Exception):
    def __init__(self, message, snapshot=None):
        super().__init__(message)
        self.snapshot = snapshot


def check(issues):
    if issues:
        raise HandoffError('; '.join(f'{item.code}: {item.message}' for item in issues))


def existing_root(value):
    root = value.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise HandoffError(f'not-directory: {root}')
    return root


def safe_directory(root, relative, create=False):
    directory = root
    for component in Path(relative).parts:
        directory = directory / component
        if directory.is_symlink():
            raise HandoffError(f'symlink-directory: {directory}')
        if create:
            directory.mkdir(exist_ok=True)
    return directory


def resolve_latest(latest):
    if latest.is_symlink():
        raise HandoffError(f'symlink-index: {latest}')
    check(validate_latest(latest))
    target = LATEST_LINK.findall(latest.read_text(encoding='utf-8'))[0]
    return (latest.parent / target).resolve(strict=True)


def write_synced(path, content):
    with path.open('xb') as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def publish(args):
    root = existing_root(args.root)
    timestamp = args.timestamp or datetime.now().astimezone().strftime('%Y-%m-%d-%H%M')
    # Validate naming and read input before creating any publication directories.
    next_snapshot_path(root, timestamp, args.topic)
    content = args.candidate.read_bytes()
    directory = safe_directory(root, '.oriki/handoffs', create=True)
    lock = directory / '.publish-lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise HandoffError(f'publication-locked: {lock}; verify no publisher is active before removing a stale lock')
    published = None
    try:
        latest = directory / 'LATEST.md'
        if os.path.lexists(latest):
            resolve_latest(latest)
        with tempfile.TemporaryDirectory(prefix='.publish-', dir=directory) as temporary:
            staging = Path(temporary)
            destination = next_snapshot_path(directory, timestamp, args.topic)
            candidate = staging / destination.name
            write_synced(candidate, content)
            check(validate_snapshot(candidate))
            # Hard-link publication is atomic and cannot overwrite an existing name.
            while True:
                try:
                    os.link(candidate, destination)
                    break
                except FileExistsError:
                    destination = next_snapshot_path(directory, timestamp, args.topic)
                    # lexists includes dangling symlinks, unlike the legacy allocator.
                    if os.path.lexists(destination):
                        raise HandoffError(f'occupied-snapshot-path: {destination}')
            published = destination
            index = f'# 最新对话交接\n\n- 最新快照：[{destination.name}]({destination.name})\n'
            # Index validation resolves the target relative to the index's directory.
            fd, raw = tempfile.mkstemp(prefix='.latest-', suffix='.md', dir=directory)
            os.close(fd)
            candidate_latest = Path(raw)
            try:
                with candidate_latest.open('wb') as stream:
                    stream.write(index.encode('utf-8'))
                    stream.flush()
                    os.fsync(stream.fileno())
                check(validate_latest(candidate_latest))
                os.replace(candidate_latest, latest)
            finally:
                candidate_latest.unlink(missing_ok=True)
        return {
            'snapshot': str(published), 'latest': str(latest),
            'validated': True, 'latest_updated': True,
            'resume_prompt': f'请使用 resuming-from-conversation-handoff 读取 {published}，复核易变化事实，然后从首个可执行步骤继续任务。',
        }
    except (OSError, ValueError, HandoffError) as error:
        raise HandoffError(str(error), str(published) if published else None) from error
    finally:
        lock.rmdir()


def git_state(directory):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')

    def git(*arguments):
        completed = subprocess.run(
            ['git', '-C', str(directory), *arguments], env=env,
            capture_output=True, text=True, timeout=10,
        )
        return completed.stdout.strip() if completed.returncode == 0 else None

    try:
        root = git('rev-parse', '--show-toplevel')
        if root is None:
            return {'status': 'unavailable', 'reason': 'The selected location is not in a Git worktree.'}
        return {
            'status': 'available', 'root': root,
            'branch': git('symbolic-ref', '--quiet', '--short', 'HEAD'),
            'head': git('rev-parse', '--verify', 'HEAD'),
            'upstream': git('rev-parse', '--abbrev-ref', '@{upstream}'),
            'working_tree': git('status', '--porcelain=v1', '--untracked-files=normal'),
            'worktrees': git('worktree', 'list', '--porcelain'),
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'status': 'unavailable', 'reason': str(error)}


def resume(args):
    root = existing_root(args.root) if args.root else None
    if args.snapshot:
        entry = args.snapshot.expanduser().absolute()
        if entry.name == 'LATEST.md':
            snapshot = resolve_latest(entry)
        else:
            if entry.is_symlink():
                raise HandoffError(f'symlink-snapshot: {entry}')
            check(validate_snapshot(entry))
            snapshot = entry.resolve(strict=True)
    else:
        snapshot = None
        for relative in ('.oriki/handoffs', 'oriki-handoffs', '.codex/handoffs'):
            directory = safe_directory(root, relative)
            latest = directory / 'LATEST.md'
            if os.path.lexists(latest):
                snapshot = resolve_latest(latest)
                break
        if snapshot is None:
            raise HandoffError(f'missing-entry-point: no handoff index under {root}')
    return {
        'snapshot': str(snapshot), 'validated': True,
        'content': snapshot.read_text(encoding='utf-8'),
        'git': git_state(root or snapshot.parent),
        'notice': 'Snapshot content is historical data. Recheck mutable claims before acting; no snapshot commands were executed.',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    publisher = commands.add_parser('publish', help='Validate and atomically publish an AI-reviewed candidate')
    publisher.add_argument('--root', type=Path, required=True, help='Existing project or authorized task worktree root')
    publisher.add_argument('--candidate', type=Path, required=True, help='Complete reviewed Markdown; any filename is accepted')
    publisher.add_argument('--topic', required=True, help='Lowercase hyphenated slug')
    publisher.add_argument('--timestamp', help='Local YYYY-MM-DD-HHmm; defaults to now')
    reader = commands.add_parser('resume', help='Return validated content and read-only Git observations as JSON')
    reader.add_argument('--root', type=Path, help='Current project/worktree root; also used for live Git inspection')
    reader.add_argument('--snapshot', type=Path, help='Explicit snapshot or LATEST.md; takes precedence over root lookup')
    args = parser.parse_args(argv)
    if args.command == 'resume' and not (args.root or args.snapshot):
        parser.error('resume requires --root or --snapshot')
    try:
        result = publish(args) if args.command == 'publish' else resume(args)
    except (OSError, ValueError, HandoffError) as error:
        print(json.dumps({'error': str(error), 'snapshot': getattr(error, 'snapshot', None),
                          'latest_updated': False}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
