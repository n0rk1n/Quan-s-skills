---
name: archiving-ai-conversation
description: Use when the user explicitly names or invokes archiving-ai-conversation or 归档 AI 对话 to tidy, summarize, or preserve an AI conversation/session in Codex, OpenCode, or another capable host.
---

# Archiving AI Conversations to Downloads

## Overview

Save a concise transcript and Chinese retrospective, one Markdown file per eligible SOP, and copies of conversation-produced files not tracked by Git in the user's Downloads directory. Verify the complete set before closing the source conversation. Keep all files as the permanent archive. Exclude procedures and formats about this archiving skill itself from SOP output.

This skill does not require or write to DEVONthink.

## Explicit Selection

Run this Skill only when the user explicitly names or invokes this skill through the current host. Do not require a particular invocation syntax or infer selection from a merely related request.

## Required Capabilities

- Readable current conversation context, or an explicitly selected supported export source.
- Local filesystem access to create and read back files in the user's Downloads directory (`~/Downloads` on macOS; resolve `~` to the actual user's home).
- Python 3.10+ on macOS/Linux for the bundled writer (standard library only); Git CLI when checking produced files.
- Optional: a conversation close or archive capability that can target the exact source conversation.

Map the current host's tools to these semantic capabilities before reading an external export source or creating output. If neither host context nor a selected adapter can produce a faithful transcript, or writable Downloads access is unavailable, report the missing capability. Stop before generating files. Do not silently use a repository, Desktop, temporary directory, or remote service as the archive destination.

## Downloads Permissions

Use the host's existing authorization to run the commands below without asking for redundant confirmation. Uncertainty alone is not evidence that Downloads access is missing. If the host requires approval or a command is denied for permissions, use its supported approval flow for that operation and explain the failed command, path, and reason; stop if access remains unavailable. Do not bypass host restrictions or request broad access preemptively.

A successful Markdown write does not establish permission for another command or the Downloads-root probe. Diagnose the actual failure: malformed JSON, invalid content, or a missing directory is not a reason to request broader permissions.

## Source Selection

For the current conversation, build the lightweight transcript from the readable current conversation context supplied by the host. Codex rollout JSONL and official ChatGPT exports are optional source adapters for higher-fidelity input; they are not general prerequisites. Never present a retrospective as the original transcript.

## Workflow

1. Confirm the source conversation. Use the current one for "this conversation"; otherwise locate it and retain its source/host ID. Ask only if unclear. Detect archival support without archiving yet.
2. Set `SKILL_DIR` to the absolute installed skill directory. Before preparing output, run the access probe:

   ```bash
   python3 "$SKILL_DIR/scripts/archive_conversation.py" preflight
   ```

   It creates, reads, and removes a temporary probe in the existing Downloads root; `save` repeats this check before writing to the daily subdirectory. Stop on a nonzero exit. The default archive destination is `~/Downloads/YYYY-MM-DD Archived AI Conversations/`, using the local date. Use `--downloads-dir` only for the actual Downloads location on another host, an explicitly requested destination, or a disposable test fixture.
3. Gather useful metrics, decisions, repeated problems, anchors, and outcomes. Mark estimates; omit private chain-of-thought. Prepare a UTF-8 JSON object following [the input contract](references/script-usage.md). The model supplies the faithful `messages`, short `title`, seven retrospective sections, an explicit `artifacts` list of produced file paths, and an explicit `sops` list with each candidate's `scope` after the assessments below. The script generates headings and the `## 原文记录` link.
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

   The writer checks each supplied artifact in its own Git repository, filters out Git-tracked files and archive-skill SOPs, creates the daily directory, selects free transcript, retrospective, individual SOP, artifact, and manifest filenames under a shared lock, normalizes embedded headings while preserving fenced code, generates the encoded transcript link, writes the Markdown files first, copies eligible artifacts byte-for-byte, writes their JSON manifest, and flushes all files to disk using exclusive creation. Read all final files back as UTF-8 for Markdown/JSON: the writer does this automatically and compares their exact bytes with the generated content. Binary artifacts use streaming SHA-256 and size checks against both source and destination; source changes fail verification. It verifies directory placement and generated links, then returns JSON containing `verified`, `directory`, `transcript`, `retrospective`, the `sops` array of absolute paths, `skipped_sops`, `artifacts`, `skipped_artifacts`, and `artifact_manifest`. See the input contract for their shapes. A hidden `.archive.lock` is retained for concurrent runs; do not delete it.
6. Require exit code 0 and `verified: true`. Then inspect every returned file for source fidelity, useful content, and omissions. Confirm that `sops` contains exactly one path per eligible SOP and that copied plus skipped artifacts account for all unique supplied files. All 2 + N Markdown files, copied artifacts, and the manifest must pass before closing. Script success verifies storage and structure, not factual accuracy or completeness. It never closes a conversation.
7. Keep all Markdown files permanently, together with copied artifacts and their manifest; do not delete them as temporary files. After successful verification, remove only this run's temporary JSON or adapter staging files. Never remove source exports. On any save, read-back, link, or cleanup failure, preserve every saved file, source artifact, and the active source conversation; report the incomplete step and returned paths. A failed save returns nonzero with `verified: false`, an error, and the planned paths when available; inspect which files exist instead of assuming a complete set.
8. Follow the closing table only after storage and content checks pass. Report the absolute daily directory, clickable links to all files, verification result, host capability, and closing result.

## Produced Files Assessment (Required on Every Archive)

List the actual files produced or updated as deliverables in the selected conversation in `artifacts`, using absolute paths. Include files outside repositories and ignored/untracked files inside repositories; submit Git-tracked candidates too so the script records why they were skipped. Use `artifacts: []` only when there are no produced files. Do not sweep unrelated directory contents, source inputs, caches, or this archive run's temporary JSON into the list. For a deliverable directory, enumerate its relevant regular files. Supply the actual file path rather than a symlink.

The script decides Git tracking with the file's own repository index, including linked worktrees: tracked files are recorded but not copied; ignored files, untracked files, and files outside Git are copied into the returned daily `directory`. Being inside a repository or listed in `.gitignore` does not mean a file is tracked. No `git add`, commit, move, or source deletion is performed.

Copies retain their original bytes and extension; name collisions receive numeric suffixes. The retrospective links to each copy and its manifest, which records source, destination, size, SHA-256, and Git-tracked skips. Missing/unreadable files, unavailable Git, uncertain Git checks, copy failures, or hash mismatches make the run incomplete. Recover a missing deliverable from an available original or rerun its established generation command and verify it before retrying; do not silently omit it or substitute a summary/link for its contents.

**Script all deterministic operations.** Use the bundled writer for path validation, Git inspection, SOP scope filtering, collision handling, copying, manifest/link generation, and storage verification. Do not replace these with manual agent steps or one-off copy commands. The model's remaining work is source selection, produced-file identification, semantic SOP classification, and factual review. Script success cannot establish that the model supplied every relevant file or classified its subject correctly.

## SOP Assessment (Required on Every Archive)

Review the final conversation for reusable standard procedures **and standard formats**. Classify each candidate by subject before writing its sections: `scope: "archiving-ai-conversation"` for the use, configuration, implementation, repair, or maintenance of this archiving skill itself; `scope: "general"` for other subjects. Archive-skill candidates need only title and scope: the writer excludes them and records the exclusion, so do not draft their SOP sections. One occurrence is sufficient for an eligible general item: create one independent Markdown document for **each**. Use `sops: []` only after finding no candidates.

| Conversation content | Required output |
| --- | --- |
| One reusable procedure or format unrelated to this archiving skill | One SOP file, plus transcript and retrospective |
| Multiple independently reusable eligible items | One file per item; retrospective links to all |
| Only procedures/formats about this archiving skill | Transcript and retrospective with an explicit exclusion finding; no SOP file |
| Archive-skill content plus an unrelated reusable item | Exclude only archive-skill candidates; create an SOP for the unrelated item |
| No reusable procedure or format | Transcript and retrospective with an explicit no-SOP finding |

Keep consecutive steps of one procedure together. Combine duplicate descriptions of the same method. Separate independently usable procedures or formats. A one-off answer without a reusable structure is not an SOP.

Each SOP uses the five required sections in [the input contract](references/script-usage.md): purpose/scope, prerequisites/inputs, steps or a copyable format, outputs/acceptance, and exceptions/boundaries. Write it in Chinese so it can be used without reading the conversation. Base it on the final agreed approach; label unverified proposals `待验证` and missing information `待补充`. Preserve known prerequisites and limitations; do not invent operational details or present abandoned approaches as standards.

For example, a conversation establishing a file-checking procedure and an independent report template produces two SOP files. The checking procedure's read, compare, and failure-handling steps remain together in one file.

Common mistakes: generating an SOP about this archiving skill; excluding unrelated SOPs merely because this skill was used to save them; skipping an item because it appeared only once; combining unrelated SOPs into one document; splitting every step into a separate SOP; closing after verifying only the two base files or omitting produced files from `artifacts`. Check the identified items against the returned `sops` paths before closing.

## Conversation Closing

| Host capability | Required finish |
| --- | --- |
| Available, such as a `set_thread_archived` or equivalent close/archive operation | Use the host's conversation close or archive capability for the exact source. Omit the source ID only for the calling conversation; otherwise pass its exact source/host IDs. Never close a different conversation or executor. |
| Unavailable | After successful file verification, tell the user to archive or delete the source conversation manually. Do not invent a fallback. |
| Tool call fails | Report that the Markdown files were saved but conversation archival failed, request manual archive/deletion, and do not claim full automatic completion. Preserve all files. |

## File and Transcript Rules

- Retrospective: `YYYY-MM-DD <对话解决的问题>（AI 对话归档）.md`; transcript: `YYYY-MM-DD <对话解决的问题>（AI 对话原文）.md`.
- SOP: `YYYY-MM-DD <SOP 名称>（SOP）.md`, one file per SOP in the same directory. Each links to the transcript; the retrospective lists every SOP. SOP names use the same title restrictions and get independent numeric suffixes on collision, including duplicate names within one run.
- For the transcript and retrospective, use the same short phrase; no `HH:mm`, slashes, or newlines. The script rejects titles over 150 UTF-8 bytes, colons, or control characters.
- Never overwrite existing archives. If either filename exists, append the same available numeric suffix to the short phrase in both filenames before writing; update the transcript link accordingly. Use exclusive creation to avoid overwrites during concurrent runs.
- Only `## 用户` and `## AI` may be level-two transcript headings. Normalize other headings outside code to `###`.
- Omit tool calls, raw arguments/results, and long pasted material unless forensic detail is requested.
- Preserve useful wording; never paste the transcript into the retrospective.
