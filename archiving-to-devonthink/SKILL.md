---
name: archiving-to-devonthink
description: Use when the user asks to tidy, summarize, preserve, or send a Codex thread/conversation/session to DEVONthink, especially with phrases like 整理归档, 归档到 DEVONthink, 收件箱, 经验总结, 避坑点, lessons learned, retrospective, or archive note.
---

# Archiving to DEVONthink

## Overview

Create two temporary Markdown records, import both into the DEVONthink Global Inbox daily group, verify them, then delete the temporary files. The user alone decides whether to archive the Codex thread.

**Never** archive a Codex thread automatically.

## Prerequisites

- Thread reading, a writable temporary path outside DEVONthink packages/source inputs, and Python 3 when using `scripts/conversation_exporter`.
- DEVONthink MCP must discover Global Inbox, find/create a group, and import files. If unavailable, stop before generation: no local-only, AppleScript, or direct-package fallback.

If Desktop thread tools are absent, check `CODEX_THREAD_ID`, local rollout JSONL, `session_index.jsonl`, and `archived_sessions/`; stop if no readable equivalent exists.

## Workflow

1. Confirm the target thread; use the current thread for “this thread”, otherwise locate it. Ask only if unclear.
2. Resolve `daily_archive_group_uuid`: in Global Inbox, find or create exactly `YYYY-MM-DD Archived Codex Conversations` for the local date. Reuse an existing UUID; stop if unresolved.
3. Gather available metrics, decisions, repeated problems, anchors, and outcomes. Mark estimates; never include private chain-of-thought.
4. Create a lightweight transcript in a normal temporary directory. Prefer:

   ```bash
   PYTHONPATH="$PWD/scripts" python3 -m conversation_exporter.cli codex --input <jsonl-or-directory> --thread <thread-id> --out <temporary-output-dir>
   ```

   Use the `chatgpt` source mode for official ChatGPT exports; otherwise create an equivalent concise transcript manually.
5. Write the retrospective beside it: Chinese headings, no level-one heading, one blank line after headings, useful context/actions/result/decisions/lessons, hard issues, anchors, `## 原文记录`, and follow-ups.
6. Import transcript then retrospective using `mode: import` and destination `daily_archive_group_uuid`. Each must return an identifiable record whose parent equals that UUID. Before retrospective import, include the transcript record in `## 原文记录` when available.
7. Only after step 6, validate names and the rules below; then delete only these two generated temporary Markdown files. Keep/report paths if either import or deletion is ambiguous. Do not archive the Codex thread.
8. Report MCP preflight, group name/UUID, both record destinations, cleanup status, and that thread archival remains with the user.

## File and Transcript Rules

- Retrospective: `YYYY-MM-DD <对话解决的问题>（Codex 归档）.md`; transcript: `YYYY-MM-DD <对话解决的问题>（Codex 原文）.md`.
- Use the same short phrase; no `HH:mm`, slashes, or newlines.
- Only `## 用户` and `## AI` may be level-two transcript headings. Normalize other headings outside code to `###`.
- Omit tool calls, raw arguments/results, and long pasted material unless forensic detail is requested.
- Preserve useful wording; never paste the transcript into the retrospective.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| MCP/group unavailable | Stop before generation; no fallback. |
| Either record is outside the daily group | Keep temporary files; fix/import again. |
| Deleting before both parents match `daily_archive_group_uuid` | Wait for both verified imports. |
| Archiving the Codex thread after cleanup | Leave it for the user. |
