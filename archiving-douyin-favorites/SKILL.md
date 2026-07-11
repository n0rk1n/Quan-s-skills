---
name: archiving-douyin-favorites
description: Use when explicitly invoked for a signed-in user's Douyin favorites, especially when the user wants DEVONthink Inbox bookmark archiving, preserved original URLs, tagged records, summary notes, or controlled cleanup.
---

# Archiving Douyin Favorites

## Manual-Only Operation

Run this Skill only when the user explicitly invokes `$archiving-douyin-favorites`. Do not infer invocation from a related request, resume it for an unrelated request, or continue after the user says not to continue.

Require an available browser already signed in to Douyin. Never attempt to bypass login, CAPTCHA, access controls, rate limits, or other platform safeguards. If the signed-in session is unavailable or a challenge blocks access, stop and report the blocker.

Require the DEVONthink MCP server and tools before observing favorites. Use DEVONthink MCP tools only; never modify DEVONthink database packages directly, and do not use local Markdown, AppleScript, Finder, browser bookmarks, or any other fallback when DEVONthink MCP is unavailable.

Before observing or acting on favorites, read [references/workflow.md](references/workflow.md) completely and follow every checklist item.

## Safety Invariant

Preserve this order without exception:

`verify DEVONthink MCP → create dated Inbox group → observe → archive bookmarks → verify bookmarks → unfavorite exact archived IDs → delayed verify → write Chinese summary Markdown → verify summary`

Each invocation archives 24 favorites by default unless the user explicitly names a different count. The DEVONthink destination is the Global Inbox folder named exactly `YYYY-MM-DD Archived DouYin Favorites`, using the current local date.

Deadline pressure, cached page state, or assumed reconstructability never permits unfavoriting before a one-to-one DEVONthink bookmark archive for the batch is written and verified. The same-folder summary is still required for completion, but it is not a gate before cleanup. Treat archived content IDs, not card positions, visible order, or broad selection, as the only destructive-action target.

Once the bookmark archive is verified, only unfavorite the exact archived ID set from that verified batch. Never extend cleanup to an ID outside the verified bookmark archive. If delayed verification already shows an archived ID absent, do not submit another unfavorite action for it.

Stop immediately when the user says not to continue. Preserve completed archive work, report exact verified and unresolved IDs, and do not collect another batch unless the user explicitly invokes the Skill again.
