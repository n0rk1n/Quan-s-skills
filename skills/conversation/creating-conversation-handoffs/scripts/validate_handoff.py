#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
# How to run:
# python3 validate_handoff.py snapshot <snapshot.md>
# python3 validate_handoff.py latest <LATEST.md>
# python3 validate_handoff.py next-path <directory> --timestamp <value> --topic <slug>

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from handoff_contract import (
    next_snapshot_path,
    validate_latest,
    validate_snapshot,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate conversation handoffs")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("snapshot", "latest"):
        validation = commands.add_parser(command)
        validation.add_argument("path", type=Path)
    next_path = commands.add_parser("next-path")
    next_path.add_argument("directory", type=Path)
    next_path.add_argument("--timestamp", required=True)
    next_path.add_argument("--topic", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "next-path":
        try:
            path = next_snapshot_path(
                args.directory,
                args.timestamp,
                args.topic,
            )
        except ValueError as error:
            print(f"ERROR invalid-next-path-input: {error}", file=sys.stderr)
            return 1
        print(path)
        return 0
    path = args.path
    issues = (
        validate_snapshot(path)
        if args.command == "snapshot"
        else validate_latest(path)
    )
    if issues:
        for issue in issues:
            print(f"ERROR {issue.code}: {issue.message}", file=sys.stderr)
        return 1
    print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
