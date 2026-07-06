---
name: archiving-to-devonthink
description: Use when the user asks Codex to archive, tidy, summarize, preserve, or send a Codex thread/conversation/session to DEVONthink, especially with phrases like 整理归档, 归档到 DEVONthink, 收件箱, 经验总结, 避坑点, lessons learned, retrospective, or archive note.
---

# Archiving to DEVONthink

## Overview

Turn a Codex thread into a concise Chinese Markdown retrospective, import it into DEVONthink, delete the temporary local file only after confirmed import, then ask before archiving the Codex thread unless the user already authorized that final step.

Write for the user's future self: natural, concrete, first-person where appropriate, focused on what the conversation solved and why the path mattered. A good archive is worth rereading months later: it preserves concrete evidence, the shape of the work, repeated sticking points, decisions, and lessons. Never dump the transcript or include private chain-of-thought.

## Required Capabilities

Before starting, confirm equivalent capabilities exist:

- Codex thread tools for identifying, reading, and archiving threads, such as `read_thread`, `list_threads`, `set_thread_archived`, or equivalents.
- DEVONthink tools for selecting a destination and importing files, such as `get_databases`, `import_file`, or equivalents.
- A normal writable temporary filesystem path outside any `.dtBase2`, `.dtSparse`, or `.dtArchive` package.

In Codex Desktop, explicit thread tools may be unavailable even when local equivalents exist. Before declaring thread access missing or offering a reduced workflow, check for `CODEX_THREAD_ID`, `~/.codex/sessions/**/rollout-*-<thread-id>.jsonl`, `~/.codex/session_index.jsonl`, and `~/.codex/archived_sessions/`. These can satisfy identifying and reading the current thread. Treat them as equivalent capabilities when they exist and are readable; use narrow metadata/count checks first and do not dump raw transcript content into the response.

If a required capability, MCP server, plugin, app integration, or dependency is missing and no equivalent exists, stop and name the missing item. Do not silently skip DEVONthink import or thread archiving unless the user explicitly chooses a reduced workflow.

## Workflow

1. Confirm the target thread.
   - If the user says "this thread", use the calling thread when supported.
   - If they refer to another thread, use thread tools to list or read it.
   - If unclear, ask one concise clarification question.

2. Gather enough context and conversation evidence.
   - For the current thread, start with visible conversation context.
   - Use thread/app tools when context is incomplete, aggressively summarized, or missing decisions, failures, lessons, commands, files, or outcomes.
   - Include older pages only when needed for a useful retrospective.
   - Collect thread metrics when available: start time, end time or archive time, total elapsed duration, user message count, assistant response count, tool-call count, and number of resumptions or context-compaction events.
   - If exact metrics are unavailable, estimate from available timestamps or thread-tool metadata and label the value as approximate. Do not invent precision.
   - Identify repeated or difficult discussion loops: errors that appeared more than once, decisions revisited, assumptions corrected, blocked capabilities, approval or permission friction, and changes in direction.
   - Preserve concrete anchors for later recall: important commands, files, tool names, destination names, dates, links, and error text.

3. Write the temporary Markdown note.
   - Save in a normal output location, never inside a DEVONthink database package.
   - Filename must follow the filename rule below.
   - Use Chinese section headings and no level-one heading (`# ...`).
   - Leave exactly one blank line after every section heading before body text or lists.
   - Prefer STAR shape: background/situation, task, actions, result, decisions, lessons, useful commands/files/links, follow-ups.
   - Include a concise conversation summary block with the metrics from step 2 when they are available or useful.
   - Include a section for hard or repeated issues when the thread contained friction, retries, reversals, debugging loops, unclear requirements, missing tools, or permission boundaries.
   - Optimize for future review, not completeness: omit trivial turn-by-turn narration and keep the material that explains what was learned, decided, fixed, or still needs attention.

4. Import into DEVONthink.
   - Use DEVONthink MCP tools only; never modify database package contents directly.
   - Prefer the Global Inbox database when present (`is_inbox: true`).
   - If no Global Inbox is available, use the current database's `incomingGroupUUID` or ask the user for a destination.
   - Import with `mode: import`.
   - Treat import as confirmed only when the tool returns success plus an identifiable destination: database/group name, record UUID, item URL, or imported path.

5. Validate before deletion.
   - DEVONthink reported success.
   - Destination is identifiable.
   - Imported item name matches the filename rule.
   - No file was written inside `.dtBase2`, `.dtSparse`, or `.dtArchive`.
   - Generated note has no level-one heading, all generated headings are Chinese, heading spacing is correct, and no private chain-of-thought is present.
   - Generated note includes conversation metrics when available, or clearly says when they were unavailable.
   - If the thread had repeated or difficult issues, generated note names them and explains the final resolution or remaining uncertainty.

6. Delete the temporary local Markdown file.
   - Delete only the file created for this workflow.
   - Delete only after confirmed import with identifiable destination.
   - If import is ambiguous or deletion fails, keep/report the local path.

7. Ask before archiving the Codex thread.
   - After successful import, ask whether to archive the Codex thread now.
   - Use `set_thread_archived` only after confirmation, or when the original request explicitly pre-authorized archiving after import.
   - If import fails, do not ask for archive confirmation and do not archive unless the user explicitly says to archive anyway.

8. Report import and thread-archive status separately.
   - Mention the DEVONthink destination.
   - Mention whether the temporary local file was deleted or provide its path.
   - Mention whether the Codex thread was archived, is waiting for confirmation, or cannot be archived because a required capability is unavailable.
   - A successful DEVONthink import with an unarchived thread is partial completion, not a failed archive note.

## Filename Rule

Use this exact pattern:

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

## Writing Style

- Match the thread language; use Chinese when the user asked in Chinese or the thread is mainly Chinese.
- Prefer `我` for the user's intent, decisions, and reminders.
- Use `Codex` only for assistant actions.
- Avoid assistant-centric phrasing like "the user asked..." when first-person is clearer.
- Do not invent emotions, motives, preferences, commands, files, destinations, or outcomes.
- Preserve exact names for paths, commands, tool names, dates, links, and DEVONthink destinations.
- Keep prose concise unless the thread has substantial implementation or debugging history.
- Prefer synthesis over chronology: write what changed, what was decided, and what I should remember, not every message in order.
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

## 后续事项

暂无
```

Use the template as a guide, not a rigid form. Omit sections only when they add no value; otherwise write `暂无` for no follow-up.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Exact example tool name is unavailable | Use an equivalent capability; stop only when the capability is missing. |
| Codex Desktop lacks `read_thread`/`list_threads` tools | Check `CODEX_THREAD_ID`, local rollout JSONL files, and `session_index.jsonl` before claiming the thread cannot be read. |
| Writing inside a DEVONthink database package | Write temporary files elsewhere and import through DEVONthink tools. |
| Naming file `YYYY-MM-DD-codex-archive-...md` or adding `HH:mm` | Use `YYYY-MM-DD <对话解决的问题>（Codex 归档）.md`. |
| Transcript dump or assistant-centric summary | Write a first-person retrospective with context, actions, results, decisions, and lessons. |
| Only summarizing outcome, without thread evidence | Include available duration, turn counts, tool-call count, concrete anchors, and key output. |
| Omitting repeated friction because it feels messy | Summarize the repeated issue, why it mattered, and how it was resolved or left open. |
| Inventing exact metrics when tools do not expose them | Use approximate language or say the metric was unavailable. |
| Body text directly under a heading | Leave exactly one blank line after each section heading. |
| Archiving before import or immediately after import | Import first, then ask for confirmation unless pre-authorized. |
| Deleting after ambiguous import | Keep the local file until destination is identifiable. |
| Treating unarchived thread as failed DEVONthink import | Report import status and Codex thread archive status separately. |
