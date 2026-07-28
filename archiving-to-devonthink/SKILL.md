---
name: archiving-to-devonthink
description: Use when the user asks to tidy, summarize, preserve, or send an AI conversation/session to DEVONthink, especially with phrases like 整理归档, 归档到 DEVONthink, 收件箱, 经验总结, 避坑点, lessons learned, retrospective, or archive note. Compatible with Codex, OpenCode, and other agent hosts that provide the required capabilities.
---

# Archiving to DEVONthink

## Overview

Import a concise transcript and retrospective into the DEVONthink Global Inbox daily group, verify and clean up, then close the source conversation as far as the host allows.

**Complete everything the host supports:** agents archive conversations themselves when a tool exists; otherwise they ask the user to archive or delete manually.

## Required Capabilities

- Readable current conversation context, or an explicitly selected supported export source.
- DEVONthink MCP operations that can discover Global Inbox, find or create a group, import files, and verify record parents.
- A safe writable temporary directory.
- Optional: a conversation close or archive capability that can target the exact source conversation.

## Source Selection

For the current conversation, build the lightweight transcript from the readable current conversation context supplied by the host. Codex rollout JSONL and official ChatGPT exports are optional source adapters for higher-fidelity input; they are not general prerequisites. Stop if neither the host context nor a selected adapter can produce a trustworthy transcript, and never present a retrospective as the original transcript.

Without readable host context or a selected optional adapter that can produce a faithful original transcript, stop and report the limitation.

## Workflow

1. Confirm the source conversation. Use the current one for "this conversation"; otherwise locate it and retain its source/host ID. Ask only if unclear. Detect archival support without archiving yet.
2. In Global Inbox, find or create exactly `YYYY-MM-DD Archived AI Conversations` for the local date; retain its UUID. Historical `Archived Codex Conversations` groups are not discovered, reused, renamed, migrated, or merged.
3. Gather useful metrics, decisions, repeated problems, anchors, and outcomes. Mark estimates; omit private chain-of-thought.
4. Create a lightweight transcript in a safe temporary directory from the current host context. Optional source adapters (Codex JSONL via `conversation_exporter.cli codex`, official ChatGPT exports via `conversation_exporter.cli chatgpt`) may be used when the host context is insufficient and an export source is explicitly available.
5. Write the retrospective beside it with Chinese headings, no level-one heading, one blank line after headings, context/actions/result/decisions/lessons, hard issues, anchors, `## 原文记录`, and follow-ups.
6. Import transcript then retrospective using `mode: import` and the daily-group UUID. Verify both returned records have that parent. Link the transcript record from `## 原文记录` when available.
7. Validate names and the rules below, then delete only the two generated files. If any import, parent check, or deletion is ambiguous, keep the files and source conversation active, report the incomplete step, and stop.
8. Follow the closing table. Report MCP preflight, group name/UUID, record destinations, cleanup, host capability, and closing result.

## Conversation Closing

| Host capability | Required finish |
| --- | --- |
| Available, such as a `set_thread_archived` or equivalent close/archive operation | Use the host's conversation close or archive capability for the exact source. Omit the source ID only for the calling conversation; otherwise pass its exact source/host IDs. Never close a different conversation or executor. |
| Unavailable | After successful import and cleanup, tell the user to archive or delete the source conversation manually. Do not invent a fallback. |
| Tool call fails | Report that DEVONthink succeeded but conversation archival failed, request manual archive/deletion, and do not claim full automatic completion. |

## File and Transcript Rules

- Retrospective: `YYYY-MM-DD <对话解决的问题>（AI 对话归档）.md`; transcript: `YYYY-MM-DD <对话解决的问题>（AI 对话原文）.md`.
- Use the same short phrase; no `HH:mm`, slashes, or newlines.
- Only `## 用户` and `## AI` may be level-two transcript headings. Normalize other headings outside code to `###`.
- Omit tool calls, raw arguments/results, and long pasted material unless forensic detail is requested.
- Preserve useful wording; never paste the transcript into the retrospective.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Host cannot archive conversations | Finish DEVONthink, then request manual cleanup. |
| Supported conversation left to the user | Call the archival tool after verified import and cleanup. |
| Wrong conversation targeted | Use the retained source/host IDs. |
| Partial result followed by closing | Keep the conversation active until every check passes. |
