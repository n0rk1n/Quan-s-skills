---
name: archiving-to-devonthink
description: Use when the user asks to tidy, summarize, preserve, or prepare a Codex thread/conversation/session as Markdown records for manual DEVONthink archiving, especially with phrases like 整理归档, 归档到 DEVONthink, 收件箱, 经验总结, 避坑点, lessons learned, retrospective, or archive note.
---

# Preparing Codex Archive Records

## Overview

Create a Chinese retrospective and transcript, save them locally, and hand their paths to the user. The user decides whether to import or archive.

**Never** import into DEVONthink, delete generated files, or archive a Codex thread as part of this skill.

## Prerequisites

- Thread reading, a writable safe output path, and Python 3 when using `scripts/conversation_exporter`.

DEVONthink MCP and thread-archive tools are neither required nor permitted. If Desktop thread tools are absent, check `CODEX_THREAD_ID`, local rollout JSONL, `session_index.jsonl`, and `archived_sessions/`. Stop and name missing reading capability.

## Workflow

1. Confirm the target thread. Use the current thread for “this thread”; otherwise locate the named thread. Ask one concise question only when it is unclear.
2. Resolve a durable output directory. Use the user's directory when specified; otherwise use `codex-archives/` at the current workspace repository root. Create it if needed. Keep both files there for manual review.
3. Gather available metrics, decisions, repeated problems, anchors, and outcomes. Mark estimates; never invent precision or include private chain-of-thought.
4. Create the transcript. Prefer the bundled exporter:

   ```bash
   PYTHONPATH="$PWD/scripts" python3 -m conversation_exporter.cli codex --input <jsonl-or-directory> --thread <thread-id> --out <output-dir>
   ```

   ```bash
   PYTHONPATH="$PWD/scripts" python3 -m conversation_exporter.cli chatgpt --input <export.zip-or-conversations.json> --out <output-dir>
   ```

   Otherwise create an equivalent concise transcript manually.
5. Write the retrospective beside it: Chinese headings, no level-one heading, one blank line after headings; background, task, actions, result, decisions, lessons, hard issues, anchors, `## 原文记录` local path, and follow-ups.
6. Validate names, durable location, no private reasoning, metrics (or unavailable note), and the rules below.
7. Report the exact two local paths and state: files were retained for manual DEVONthink import and optional manual thread archiving. Do not call DEVONthink MCP, AppleScript, database-package operations, `set_thread_archived`, or equivalent tools; do not delete either file; do not claim import or thread archival succeeded.

## File and Transcript Rules

- Retrospective: `YYYY-MM-DD <对话解决的问题>（Codex 归档）.md`
- Transcript: `YYYY-MM-DD <对话解决的问题>（Codex 原文）.md`
- Same short solved-problem phrase in both names; no `HH:mm`, slashes, or newlines.
- Transcript role markers are the only body level-two headings: `## 用户` and `## AI`.
- Normalize all other message headings outside code blocks to `###`; preserve headings in code blocks.
- Omit tool calls, raw arguments/results, and long pasted material unless forensic detail is requested.
- Preserve useful wording; never paste the transcript into the retrospective.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Auto-importing, deleting, or archiving | Stop after local validation and hand over both paths. |
| DEVONthink package or disposable output | Use the durable local directory. |
| Summary only, arbitrary `##`, or tool dumps | Create both files; retain role-only level-two headings and omit raw tools. |
