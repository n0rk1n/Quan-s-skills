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
- Python 3.10+ on macOS/Linux for the bundled writer (standard library only).
- Optional: a conversation close or archive capability that can target the exact source conversation.

Map the current host's tools to these semantic capabilities before reading an external export source or creating output. If readable source content or writable Downloads access is unavailable, report the missing capability. Stop before generating files. Do not silently use a repository, Desktop, temporary directory, or remote service as the archive destination.

## Source Selection

For the current conversation, build the lightweight transcript from the readable current conversation context supplied by the host. Codex rollout JSONL and official ChatGPT exports are optional source adapters for higher-fidelity input; they are not general prerequisites. Stop if neither the host context nor a selected adapter can produce a trustworthy transcript, and never present a retrospective as the original transcript.

Without readable host context or a selected optional adapter that can produce a faithful original transcript, stop and report the limitation.

## Workflow

1. Confirm the source conversation. Use the current one for "this conversation"; otherwise locate it and retain its source/host ID. Ask only if unclear. Detect archival support without archiving yet.
2. Set `SKILL_DIR` to the absolute installed skill directory. Before preparing output, run the access probe:

   ```bash
   python3 "$SKILL_DIR/scripts/archive_conversation.py" preflight
   ```

   It probes read/write access to the existing Downloads directory without retaining probe files. Stop on a nonzero exit. The default archive destination is `~/Downloads/YYYY-MM-DD Archived AI Conversations/`, using the local date. Use `--downloads-dir` only for the actual Downloads location on another host, an explicitly requested destination, or a disposable test fixture.
3. Gather useful metrics, decisions, repeated problems, anchors, and outcomes. Mark estimates; omit private chain-of-thought. Prepare a UTF-8 JSON object following [the input contract](references/script-usage.md). The model supplies the faithful `messages`, short `title`, and seven retrospective sections. The script generates headings and the `## 原文记录` link.
4. Use readable current context first. Optional source adapters may be used only when the host context is insufficient and an export source is explicitly available. Export into a safe temporary staging directory, then select the exact source and turn its transcript into the JSON `messages` array:

   ```bash
   PYTHONPATH="$SKILL_DIR/scripts" python3 -m conversation_exporter.cli codex --input <jsonl-or-directory> --thread <thread-id> --out <temporary-output-dir>
   PYTHONPATH="$SKILL_DIR/scripts" python3 -m conversation_exporter.cli chatgpt --input <conversations-json-or-zip> --out <temporary-output-dir>
   ```

   The ChatGPT CLI exports every conversation in its input. Prepare an input containing only the requested conversation before running it; leave the original export untouched. The Codex filter can match substrings, so confirm the exact source ID before using its output. Do not archive unrelated conversations.
5. Send JSON through stdin to the writer, or save it as a temporary input and run:

   ```bash
   python3 "$SKILL_DIR/scripts/archive_conversation.py" save --input <archive-input.json>
   ```

   The writer creates the daily directory, selects a free pair of filenames under a shared lock, normalizes embedded headings while preserving fenced code, generates the encoded transcript link, writes both files exclusively, and flushes them to disk. Read both final files back as UTF-8: the writer does this automatically and compares their exact bytes with the generated content. It verifies directory placement and the transcript link, then returns JSON containing `verified`, `directory`, `transcript`, and `retrospective` absolute paths. A hidden `.archive.lock` is retained for concurrent runs; do not delete it.
6. Require exit code 0 and `verified: true`. Then inspect the returned files for source fidelity, useful content, and omissions. Script success verifies storage and structure, not factual accuracy or completeness. It never closes a conversation.
7. Keep both Markdown files permanently; do not delete them as temporary files. After successful verification, remove only this run's temporary JSON or adapter staging files. Never remove source exports. On any save, read-back, link, or cleanup failure, preserve the saved Markdown and the active source conversation; report the incomplete step and returned paths. A failed save returns nonzero with `verified: false`, an error, and the planned paths when available; inspect which files exist instead of assuming a full pair.
8. Follow the closing table only after storage and content checks pass. Report the absolute daily directory, clickable links to both files, verification result, host capability, and closing result.

## Conversation Closing

| Host capability | Required finish |
| --- | --- |
| Available, such as a `set_thread_archived` or equivalent close/archive operation | Use the host's conversation close or archive capability for the exact source. Omit the source ID only for the calling conversation; otherwise pass its exact source/host IDs. Never close a different conversation or executor. |
| Unavailable | After successful file verification, tell the user to archive or delete the source conversation manually. Do not invent a fallback. |
| Tool call fails | Report that the Markdown files were saved but conversation archival failed, request manual archive/deletion, and do not claim full automatic completion. Preserve both files. |

## File and Transcript Rules

- Retrospective: `YYYY-MM-DD <对话解决的问题>（AI 对话归档）.md`; transcript: `YYYY-MM-DD <对话解决的问题>（AI 对话原文）.md`.
- Use the same short phrase; no `HH:mm`, slashes, or newlines. The script rejects titles over 150 UTF-8 bytes, colons, or control characters.
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
