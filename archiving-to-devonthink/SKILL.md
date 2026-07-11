---
name: archiving-to-devonthink
description: Use when the user asks Codex to archive, tidy, summarize, preserve, or send a Codex thread/conversation/session to DEVONthink, especially with phrases like 整理归档, 归档到 DEVONthink, 收件箱, 经验总结, 避坑点, lessons learned, retrospective, or archive note.
---

# Archiving to DEVONthink

## Overview

Turn a Codex thread into two Markdown archive records: a concise Chinese retrospective and a lightweight readable transcript. Import both into DEVONthink, delete temporary local files only after both imports are confirmed, then archive the Codex thread only after the DEVONthink records are identifiable and the temporary files have been deleted. Once that gate passes, archive the Codex thread yourself without asking for a separate final confirmation.

Write the retrospective for the user's future self: natural, concrete, first-person where appropriate, focused on what the conversation solved and why the path mattered. Preserve the transcript separately for evidence and search, but keep it compact: user/assistant wording matters more than raw skill dumps, tool arguments, or tool outputs. Never include private chain-of-thought.

## Required Capabilities

Before starting, confirm these capabilities exist:

- Codex thread tools for identifying, reading, and archiving threads, such as `read_thread`, `list_threads`, `set_thread_archived`, or equivalents.
- DEVONthink MCP tools for discovering databases, finding or creating groups, and importing files.
- A normal writable temporary filesystem path outside any `.dtBase2`, `.dtSparse`, or `.dtArchive` package.
- Python 3 for the bundled transcript exporter at `scripts/conversation_exporter`.

DEVONthink MCP is a hard requirement. Before generating either temporary Markdown file, confirm the MCP can discover the Global Inbox, find or create a group, and import files. If DEVONthink MCP is unavailable or any of those operations is unsupported, stop and name the missing capability. Do not offer or run a local-only, AppleScript, direct database-package, or skipped-import fallback, even if the user asks to preserve partial progress.

In Codex Desktop, explicit thread tools may be unavailable even when local equivalents exist. Before declaring thread access missing or offering a reduced workflow, check for `CODEX_THREAD_ID`, `~/.codex/sessions/**/rollout-*-<thread-id>.jsonl`, `~/.codex/session_index.jsonl`, and `~/.codex/archived_sessions/`. These can satisfy identifying and reading the current thread. Treat them as equivalent capabilities when they exist and are readable; use narrow metadata/count checks first and do not dump raw transcript content into the response.

If a required Codex thread capability or dependency is missing and no local equivalent exists, stop and name the missing item. Do not silently skip thread archiving unless the user explicitly chooses a reduced workflow.

## Workflow

1. Confirm the target thread.
   - If the user says "this thread", use the calling thread when supported.
   - If they refer to another thread, use thread tools to list or read it.
   - If unclear, ask one concise clarification question.

2. Resolve the daily DEVONthink destination.
   - Use the Global Inbox database (`is_inbox: true`). If it is unavailable, stop; do not fall back to another database or ask for another destination.
   - Name the group exactly `YYYY-MM-DD Archived Codex Conversations`, using the current local date.
   - Search the Global Inbox for that exact group name. Reuse its group UUID when found; create it only when absent.
   - Treat the group as resolved only when DEVONthink MCP returns an identifiable group UUID. Use that UUID as `daily_archive_group_uuid` for the rest of the workflow.

3. Gather enough context and conversation evidence.
   - For the current thread, start with visible conversation context.
   - Use thread/app tools when context is incomplete, aggressively summarized, or missing decisions, failures, lessons, commands, files, or outcomes.
   - Include older pages only when needed for a useful retrospective.
   - Collect thread metrics when available: start time, end time or archive time, total elapsed duration, user message count, assistant response count, tool-call count, and number of resumptions or context-compaction events.
   - If exact metrics are unavailable, estimate from available timestamps or thread-tool metadata and label the value as approximate. Do not invent precision.
   - Identify repeated or difficult discussion loops: errors that appeared more than once, decisions revisited, assumptions corrected, blocked capabilities, approval or permission friction, and changes in direction.
   - Preserve concrete anchors for later recall: important commands, files, tool names, destination names, dates, links, and error text. Keep anchors concise; do not copy raw tool payloads or long reference documents just because they appeared in the thread.

4. Generate the original transcript Markdown.
   - Use the bundled exporter in this skill when local Codex JSONL or ChatGPT official export files are available.
   - From this skill directory, run Codex exports with:

     ```bash
     PYTHONPATH="$PWD/scripts" python3 -m conversation_exporter.cli codex --input <jsonl-or-directory> --thread <thread-id> --out <temporary-output-dir>
     ```

   - For ChatGPT official export files, run:

     ```bash
     PYTHONPATH="$PWD/scripts" python3 -m conversation_exporter.cli chatgpt --input <chatgpt-export.zip-or-conversations.json> --out <temporary-output-dir>
     ```

   - If the current thread is only available through conversation context or thread tools, build an equivalent transcript manually using the transcript Markdown rules below.
   - Save transcript files in a normal temporary output directory, never inside source input directories or DEVONthink database packages.
   - The transcript should preserve the useful shape of user/assistant wording, but it is intentionally lightweight. Omit raw tool-call sections, tool arguments, tool outputs, full skill contents, and other long pasted reference blocks unless the user explicitly asks for a forensic transcript.

5. Write the temporary Markdown retrospective note.
   - Save in a normal output location, never inside a DEVONthink database package.
   - Filename must follow the retrospective filename rule below.
   - Use Chinese section headings and no level-one heading (`# ...`).
   - Leave exactly one blank line after every section heading before body text or lists.
   - Prefer STAR shape: background/situation, task, actions, result, decisions, lessons, useful commands/files/links, follow-ups.
   - Include a concise conversation summary block with the metrics from step 3 when they are available or useful.
   - Include an `## 原文记录` section naming the transcript file and, after import, the DEVONthink record UUID/link when available.
   - Include a section for hard or repeated issues when the thread contained friction, retries, reversals, debugging loops, unclear requirements, missing tools, or permission boundaries.
   - Optimize for future review, not completeness: omit trivial turn-by-turn narration and keep the material that explains what was learned, decided, fixed, or still needs attention.

6. Import both Markdown files into DEVONthink.
   - Use DEVONthink MCP tools only; never modify database package contents directly.
   - Import both files with destination `daily_archive_group_uuid`; importing either file into the Global Inbox root or another group is not success.
   - Import with `mode: import`.
   - Treat import as confirmed only when the tool returns success plus an identifiable destination: database/group name, record UUID, item URL, or imported path.
   - Import the transcript and retrospective as separate records. Prefer importing the transcript first, then the retrospective with its `## 原文记录` section updated to reference the imported transcript.
   - If DEVONthink tools support tags or comments, tag/link the two records consistently; do not rely on tags as the only relationship.

7. Validate before deletion.
   - DEVONthink reported success for both retrospective and transcript.
   - Both destinations are identifiable.
   - Confirm both imported record parents equal `daily_archive_group_uuid` before deleting temporary files.
   - Imported retrospective item name matches the retrospective filename rule.
   - Imported transcript item name matches the transcript filename rule.
   - No file was written inside `.dtBase2`, `.dtSparse`, `.dtArchive`, or source input directories.
   - Retrospective note has no level-one heading, all generated headings are Chinese, heading spacing is correct, and no private chain-of-thought is present.
   - Retrospective note includes conversation metrics when available, or clearly says when they were unavailable.
   - Retrospective note includes an `## 原文记录` section pointing to the transcript import when DEVONthink returns an identifiable record.
   - Transcript role markers are second-level headings: `## 用户` and `## AI`.
   - Transcript body content outside frontmatter and code blocks has no level-one headings, no non-role second-level headings, and no headings deeper than level three.
   - Transcript omits raw tool-call sections, `call_id`, tool arguments, tool outputs, and full skill/document dumps unless the user explicitly asked for a forensic transcript.
   - If the thread had repeated or difficult issues, retrospective note names them and explains the final resolution or remaining uncertainty.

8. Delete the temporary local Markdown files.
   - Delete only files created for this workflow.
   - Delete only after both imports are confirmed with identifiable destinations.
   - If either import is ambiguous or deletion fails, keep/report the local paths.

9. Archive the Codex thread after the completion gate.
   - The Codex thread archive gate is: both DEVONthink imports are confirmed with identifiable destinations in the identified `daily_archive_group_uuid`, both imported record parents equal that group UUID, the retrospective points to the transcript record when possible, and the temporary local Markdown files have been deleted.
   - After the gate above passes, use `set_thread_archived` without asking for additional permission. This skill has standing authorization to archive the Codex thread only after successful DEVONthink import and verified cleanup.
   - This completion gate is absolute: never archive the Codex thread when DEVONthink MCP is unavailable, `daily_archive_group_uuid` is unresolved, either import failed or is ambiguous, or either imported record parent differs from that group UUID. Do not bypass these conditions even if the user explicitly asks to archive anyway.
   - If temporary file deletion fails or remains unverified, do not archive the Codex thread. Report the local paths that were kept.

10. Report import and thread-archive status separately.
   - Report the `MCP preflight status`: whether DEVONthink MCP confirmed Global Inbox discovery, daily-group find/create support, and file-import support.
   - Report the exact daily group name and its `daily_archive_group_uuid`.
   - Report the transcript and retrospective separately, including each import result and whether its imported record parent equals `daily_archive_group_uuid`.
   - Mention the DEVONthink destinations for both retrospective and transcript.
   - Mention whether the temporary local files were deleted or provide their paths.
   - Mention whether the Codex thread was archived or could not be archived because a required capability or completion-gate condition is unavailable.
   - A successful DEVONthink import with an unarchived thread is partial completion, not a failed archive note, only when thread archiving is blocked by missing capability or an unmet completion gate.

## Filename Rules

Retrospective file:

```text
YYYY-MM-DD <对话解决的问题>（Codex 归档）.md
```

Example:

```text
2026-06-30 解决 sql 查询报错（Codex 归档）.md
```

Rules:

- Use the local date when the note is created.
- Do not include a time field such as `HH:mm` in the filename.
- `<对话解决的问题>` is a short natural phrase from the user's perspective.
- Prefer solved-problem phrasing, such as `解决 sql 查询报错`, `梳理 DEVONthink 归档流程`, or `总结支付回调排查经验`.
- Remove or replace filename-unsafe characters such as `/` and newlines.

Transcript file:

```text
YYYY-MM-DD <对话解决的问题>（Codex 原文）.md
```

Use the same solved-problem phrase as the retrospective whenever possible, so the two records sort together.

## Transcript Markdown Rules

- One conversation becomes one Markdown file.
- Metadata may be written in YAML frontmatter.
- Role markers are the only second-level headings in transcript body:
  - `## 用户`
  - `## AI`
- Message content outside frontmatter and code blocks must not render as headings deeper than level three.
- Normalize user/assistant content headings outside code blocks:
  - `# ...`, `## ...`, `#### ...`, and deeper become `### ...`.
  - Setext headings (`Title` followed by `---` or `===`) become `### Title`.
  - Preserve headings inside fenced code blocks, blockquote/list-contained fenced code blocks, and indented code blocks.
- Tool calls are not rendered by default. Use them for metrics and retrospective synthesis only.
- Do not render `call_id`, status, raw arguments, or tool output summaries in the transcript.
- Omit full skill contents and long pasted reference blocks from message bodies; leave a short placeholder such as `[已省略 skill 原文：archiving-to-devonthink]`.
- If tool use is necessary for later recall, mention the outcome briefly in the retrospective, not as raw transcript payload.
- For Codex local JSONL, parse `function_call`, `custom_tool_call`, `tool_search_call`, and `web_search_call` style events when available for counts and context, but keep them out of the transcript body.
- For ChatGPT official exports, follow the current-node conversation path and preserve only user/assistant turns.

## Writing Style

- Match the thread language; use Chinese when the user asked in Chinese or the thread is mainly Chinese.
- Prefer `我` for the user's intent, decisions, and reminders.
- Use `Codex` only for assistant actions.
- Avoid assistant-centric phrasing like "the user asked..." when first-person is clearer.
- Do not invent emotions, motives, preferences, commands, files, destinations, or outcomes.
- Preserve exact names for paths, commands, tool names, dates, links, and DEVONthink destinations when they are useful anchors. Do not preserve full skill text or raw tool payloads unless explicitly requested.
- Keep prose concise unless the thread has substantial implementation or debugging history.
- Prefer synthesis over chronology: write what changed, what was decided, and what I should remember, not every message in order.
- Do not paste the full transcript into the retrospective. Link or name the separate transcript record instead.
- When including metrics, use readable phrasing such as `约 42 分钟`, `我发起 6 轮请求`, `Codex 使用 14 次工具调用`. Mark uncertain numbers with `约` or `可见记录中`.
- For repeated issues, name the pattern and consequence: `反复卡在权限边界`, `多次确认目标 skill`, `工具能力缺失导致降级方案`.

## Note Template

```md
日期：<YYYY-MM-DD>
时间：<HH:mm>
线程：<thread id or "current thread">
目标位置：DEVONthink <database/group>

## 对话概览

- 总时长：<exact or approximate duration, or unavailable>
- 对话轮次：我 <N> 轮，Codex <N> 轮
- 工具调用：<N or unavailable>
- 关键产出：<one-line result>

## 背景

我发起这次对话，是为了……

## 任务

我希望这次最终能……

## 行动

1. 我先……
2. Codex 随后……

## 反复讨论与难点

1. 难点是……，我们反复处理它是因为……
2. 最终的处理方式是……

## 结果

这次对话最后……

## 关键决策

1. 我决定……，因为……

## 经验与避坑

1. 下次遇到类似情况时，我需要记住……

## 有用的命令、文件与链接

- `command`
- [file](absolute path)

## 原文记录

- 原文文件：<transcript filename>
- DEVONthink 记录：<record UUID or item URL, or unavailable>

## 后续事项

暂无
```

Use the template as a guide, not a rigid form. Omit sections only when they add no value; otherwise write `暂无` for no follow-up.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Exact example tool name is unavailable | Use an equivalent capability; stop only when the capability is missing. |
| DEVONthink MCP unavailable but another automation path exists | Stop; DEVONthink MCP has no fallback. |
| Same-day archive group already exists | Reuse its UUID; do not create a duplicate group. |
| One file imported into the Global Inbox root | Treat the workflow as incomplete; both files must be children of the daily group. |
| Codex Desktop lacks `read_thread`/`list_threads` tools | Check `CODEX_THREAD_ID`, local rollout JSONL files, and `session_index.jsonl` before claiming the thread cannot be read. |
| Writing inside a DEVONthink database package | Write temporary files elsewhere and import through DEVONthink tools. |
| Naming file `YYYY-MM-DD-codex-archive-...md` or adding `HH:mm` | Use `YYYY-MM-DD <对话解决的问题>（Codex 归档）.md`. |
| Transcript dump inside the retrospective | Generate a separate `（Codex 原文）` transcript and link it from `## 原文记录`. |
| Assistant-centric summary | Write a first-person retrospective with context, actions, results, decisions, and lessons. |
| Only summarizing outcome, without thread evidence | Include available duration, turn counts, tool-call count, concrete anchors, and key output. |
| Generating only the summary and losing original wording | Produce and import both records, then delete temporary files only after both imports are confirmed. |
| Transcript Markdown uses arbitrary `##` headings from message content | Normalize message headings so only `## 用户` and `## AI` remain as body second-level headings. |
| Transcript includes raw tool calls or skill dumps | Omit them by default; keep only concise placeholders or retrospective anchors. |
| Omitting repeated friction because it feels messy | Summarize the repeated issue, why it mattered, and how it was resolved or left open. |
| Inventing exact metrics when tools do not expose them | Use approximate language or say the metric was unavailable. |
| Body text directly under a heading | Leave exactly one blank line after each section heading. |
| Archiving the Codex thread before cleanup | Import both files, confirm identifiable DEVONthink records, delete temporary Markdown files, then archive automatically without a separate confirmation. |
| Deleting after ambiguous import | Keep the local file until destination is identifiable. |
| Treating unarchived thread as failed DEVONthink import | Report import status and Codex thread archive status separately. |
