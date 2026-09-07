---
name: archiving-ai-conversation
description: Use when the user explicitly names or invokes archiving-ai-conversation or 归档 AI 对话 to tidy, summarize, or preserve an AI conversation/session in Codex, OpenCode, or another capable host.
---

# Archiving AI Conversations to Downloads

## Overview

Save a concise transcript and Chinese retrospective as two Markdown files in the user's Downloads directory, verify both files, then close the source conversation as far as the host allows. Keep both files as the permanent archive.

This skill does not require or write to DEVONthink.

**Complete everything the host supports:** agents archive conversations themselves when a tool exists; otherwise they ask the user to archive or delete manually.

## Explicit Selection

Run this Skill only when the user explicitly names or invokes this skill through the current host. Do not require a particular invocation syntax or infer selection from a merely related request.

## Required Capabilities

- Readable current conversation context, or an explicitly selected supported export source.
- Local filesystem access to create and read back files in the user's Downloads directory (`~/Downloads` on macOS; resolve `~` to the actual user's home).
- Optional: a conversation close or archive capability that can target the exact source conversation.

Map the current host's tools to these semantic capabilities before reading an external export source or creating output. If readable source content or writable Downloads access is unavailable, report the missing capability. Stop before generating files. Do not silently use a repository, Desktop, temporary directory, or remote service as the archive destination.

## Source Selection

For the current conversation, build the lightweight transcript from the readable current conversation context supplied by the host. Codex rollout JSONL and official ChatGPT exports are optional source adapters for higher-fidelity input; they are not general prerequisites. Stop if neither the host context nor a selected adapter can produce a trustworthy transcript, and never present a retrospective as the original transcript.

Without readable host context or a selected optional adapter that can produce a faithful original transcript, stop and report the limitation.

## Workflow

1. Confirm the source conversation. Use the current one for "this conversation"; otherwise locate it and retain its source/host ID. Ask only if unclear. Detect archival support without archiving yet.
2. Resolve the user's Downloads directory and create or reuse `~/Downloads/YYYY-MM-DD Archived AI Conversations/` for the local date. Use an absolute path for filesystem operations and final links.
3. Gather useful metrics, decisions, repeated problems, anchors, and outcomes. Mark estimates; omit private chain-of-thought.
4. Create a lightweight transcript in that daily directory from the current host context. Optional source adapters may be used only when the host context is insufficient and an export source is explicitly available. Set `SKILL_DIR` to this installed skill directory and `ARCHIVE_DIR` to the absolute daily directory, then use the applicable command:

   ```bash
   PYTHONPATH="$SKILL_DIR/scripts" python3 -m conversation_exporter.cli codex --input <jsonl-or-directory> --thread <thread-id> --out "$ARCHIVE_DIR"
   PYTHONPATH="$SKILL_DIR/scripts" python3 -m conversation_exporter.cli chatgpt --input <conversations-json-or-zip> --out "$ARCHIVE_DIR"
   ```

   The ChatGPT CLI exports every conversation in its input. Before running it, prepare a separate input containing only the exact requested conversation in a safe temporary directory; leave the original export untouched. Remove only that temporary input after verification. Do not archive unrelated conversations. Rename only the generated transcript for that source to the naming convention below, without overwriting existing files.
5. Write the retrospective beside it with Chinese headings, no level-one heading, one blank line after headings, context/actions/result/decisions/lessons, hard issues, anchors, `## 原文记录`, and follow-ups. Under `## 原文记录`, include a Markdown link to the sibling transcript using its actual filename (URL-encode spaces and special characters).
6. Read both final files back as UTF-8. Verify they are nonempty, contain the intended source transcript and retrospective, follow the rules below, and reside in the resolved daily directory. Verify the retrospective link resolves to the saved transcript.
7. Keep both Markdown files permanently; do not delete them as temporary files. If writing, read-back, or link verification fails, keep any files already written and the source conversation active, report the incomplete step and paths, and stop.
8. Follow the closing table only after both files pass verification. Report the absolute daily directory, clickable links to both files, verification result, host capability, and closing result.

## Conversation Closing

| Host capability | Required finish |
| --- | --- |
| Available, such as a `set_thread_archived` or equivalent close/archive operation | Use the host's conversation close or archive capability for the exact source. Omit the source ID only for the calling conversation; otherwise pass its exact source/host IDs. Never close a different conversation or executor. |
| Unavailable | After successful file verification, tell the user to archive or delete the source conversation manually. Do not invent a fallback. |
| Tool call fails | Report that the Markdown files were saved but conversation archival failed, request manual archive/deletion, and do not claim full automatic completion. Preserve both files. |

## File and Transcript Rules

- Retrospective: `YYYY-MM-DD <对话解决的问题>（AI 对话归档）.md`; transcript: `YYYY-MM-DD <对话解决的问题>（AI 对话原文）.md`.
- Use the same short phrase; no `HH:mm`, slashes, or newlines.
- Never overwrite existing archives. If either filename exists, append the same available numeric suffix to the short phrase in both filenames before writing; update the transcript link accordingly. Use exclusive creation to avoid overwrites during concurrent runs.
- Only `## 用户` and `## AI` may be level-two transcript headings. Normalize other headings outside code to `###`.
- Omit tool calls, raw arguments/results, and long pasted material unless forensic detail is requested.
- Preserve useful wording; never paste the transcript into the retrospective.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Missing Downloads access | Report the access gap before generating files. |
| Treating saved Markdown as temporary output | Retain both files in the daily Downloads directory. |
| Host cannot archive conversations | Finish file verification, then request manual closing. |
| Supported conversation left to the user | Call the archival tool after both saved files pass verification. |
| Wrong conversation targeted | Use the retained source/host IDs. |
| Partial result followed by closing | Keep the conversation active until every check passes. |
