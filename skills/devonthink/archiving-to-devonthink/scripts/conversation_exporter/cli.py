from __future__ import annotations

import argparse
from pathlib import Path

from conversation_exporter.sources.chatgpt import load_chatgpt_export
from conversation_exporter.sources.codex import default_codex_paths, parse_codex_paths
from conversation_exporter.writer import UnsafeOutputPathError, write_conversations


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    protected_roots: list[Path] = []
    if args.command == "codex":
        input_paths = [Path(value).expanduser() for value in args.input] if args.input else default_codex_paths()
        protected_roots = input_paths
        result = parse_codex_paths(input_paths)
        if args.thread:
            result.conversations = [
                conversation
                for conversation in result.conversations
                if args.thread in conversation.conversation_id
                or args.thread in str(conversation.metadata.get("source_path", ""))
            ]
    elif args.command == "chatgpt":
        input_path = Path(args.input).expanduser()
        protected_roots = [input_path]
        result = load_chatgpt_export(input_path)
    else:
        parser.error("unknown command")
        return 2

    try:
        written = write_conversations(result.conversations, Path(args.out).expanduser(), protected_roots=protected_roots)
    except UnsafeOutputPathError as exc:
        print(f"error: {exc}")
        return 2
    print(f"exported={len(written)} warnings={len(result.warnings)} skipped={len(result.skipped)}")
    for warning in result.warnings:
        print(f"warning: {warning.path}: {warning.message}")
    for skipped in result.skipped:
        print(f"skipped: {skipped}")
    return 0 if result.conversations else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conversation-exporter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    codex = subparsers.add_parser("codex", help="Export Codex local rollout JSONL records")
    codex.add_argument("--input", action="append", default=[], help="Codex JSONL file or directory. May be repeated.")
    codex.add_argument("--out", required=True, help="Output directory for Markdown files")
    codex.add_argument("--all", action="store_true", help="Use default Codex session and archive paths")
    codex.add_argument("--thread", help="Filter exported Codex conversations by thread id")

    chatgpt = subparsers.add_parser("chatgpt", help="Export ChatGPT official conversations.json records")
    chatgpt.add_argument("--input", required=True, help="ChatGPT export ZIP, directory, or conversations.json file")
    chatgpt.add_argument("--out", required=True, help="Output directory for Markdown files")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
