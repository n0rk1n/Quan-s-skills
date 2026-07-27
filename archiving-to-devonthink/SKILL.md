---
name: archiving-to-devonthink
description: Use when the user asks to tidy, summarize, preserve, or send a Codex thread/conversation/session to DEVONthink, especially with phrases like 整理归档, 归档到 DEVONthink, 收件箱, 经验总结, 避坑点, lessons learned, retrospective, or archive note.
---

# Archiving to DEVONthink

## Overview

Import a concise transcript and retrospective into the DEVONthink Global Inbox daily group, verify and clean up, then close the source conversation as far as the host allows.

**Complete everything the host supports:** agents archive conversations themselves when a tool exists; otherwise they ask the user to archive or delete manually.

## Prerequisites

- Readable conversation, a safe writable temporary path, and Python 3 when using `scripts/conversation_exporter`.
- DEVONthink MCP must discover Global Inbox, find/create a group, and import files. If unavailable, stop before generation; do not use AppleScript or direct-package fallbacks.

Without Desktop thread tools, check `CODEX_THREAD_ID`, rollout JSONL, `session_index.jsonl`, and `archived_sessions/`; stop if none is readable. Conversation archival is optional and never blocks DEVONthink import.

## Workflow

1. Confirm the source conversation. Use the current one for “this thread”; otherwise locate it and retain its thread ID/host ID. Ask only if unclear. Detect archival support without archiving yet.
2. In Global Inbox, find or create exactly `YYYY-MM-DD Archived Codex Conversations` for the local date; retain its UUID.
3. Gather useful metrics, decisions, repeated problems, anchors, and outcomes. Mark estimates; omit private chain-of-thought.
4. Create a lightweight transcript in a normal temporary directory. Prefer:

   ```bash
   PYTHONPATH="$PWD/scripts" python3 -m conversation_exporter.cli codex --input <jsonl-or-directory> --thread <thread-id> --out <temporary-output-dir>
   ```

   Use `chatgpt` mode for official ChatGPT exports; otherwise create an equivalent manually.
5. Write the retrospective beside it with Chinese headings, no level-one heading, one blank line after headings, context/actions/result/decisions/lessons, hard issues, anchors, `## 原文记录`, and follow-ups.
6. Import transcript then retrospective using `mode: import` and the daily-group UUID. Verify both returned records have that parent. Link the transcript record from `## 原文记录` when available.
7. Validate names and the rules below, then delete only the two generated files. If any import, parent check, or deletion is ambiguous, keep the files and source conversation active, report the incomplete step, and stop.
8. Follow the closing table. Report MCP preflight, group name/UUID, record destinations, cleanup, host capability, and closing result.

## Conversation Closing

| Host capability | Required finish |
| --- | --- |
| Available, such as Codex | Call `set_thread_archived` (or equivalent) with archival enabled for the exact source. Omit `threadId` only for the calling conversation; otherwise pass its exact thread/host IDs. Never archive a different executor. |
| Unavailable, such as Reasonix or Claude Code | After successful import and cleanup, tell the user to archive or delete the source conversation manually. Do not invent a fallback. |
| Tool call fails | Report that DEVONthink succeeded but conversation archival failed, request manual archive/deletion, and do not claim full automatic completion. |

## File and Transcript Rules

- Retrospective: `YYYY-MM-DD <对话解决的问题>（Codex 归档）.md`; transcript: `YYYY-MM-DD <对话解决的问题>（Codex 原文）.md`.
- Use the same short phrase; no `HH:mm`, slashes, or newlines.
- Only `## 用户` and `## AI` may be level-two transcript headings. Normalize other headings outside code to `###`.
- Omit tool calls, raw arguments/results, and long pasted material unless forensic detail is requested.
- Preserve useful wording; never paste the transcript into the retrospective.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Host cannot archive conversations | Finish DEVONthink, then request manual cleanup. |
| Supported conversation left to the user | Call the archival tool after verified import and cleanup. |
| Wrong conversation targeted | Use the retained source thread/host IDs. |
| Partial result followed by closing | Keep the conversation active until every check passes. |
