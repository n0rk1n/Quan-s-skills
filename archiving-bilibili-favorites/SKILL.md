---
name: archiving-bilibili-favorites
description: Use when explicitly invoked to archive a signed-in user's Bilibili favorites to DEVONthink exactly one bounded batch of 40.
---

# Archiving Bilibili Favorites

## Manual-Only Operation

Run this Skill only when the user explicitly names or invokes this skill through the current host. Do not require a particular invocation syntax.

## Required Capabilities

- authenticated browser automation that can inspect and operate the signed-in Bilibili session, match BV IDs and canonical URLs, inspect the final dialog, reload, and verify removals.
- DEVONthink MCP operations that can discover a writable Inbox and create, look up, update, tag, and verify groups and bookmark/Markdown records.

Map the current host's tools to these semantic capabilities before observing favorites. Stop before observing favorites if either required capability is unavailable; do not offer a reduced fallback.

Before observing or acting on favorites, read [references/workflow.md](references/workflow.md) completely and follow every checklist item.

## Safety Invariant

Preserve this order without exception:

`verify DEVONthink MCP → create fresh Inbox group → observe exactly 40 → create bookmarks → verify one-to-one mapping → select exact BV IDs → verify confirmation dialog → cancel → reload and verify → write Chinese summary`

Each invocation archives 40 favorites. The DEVONthink destination is the Global Inbox folder named exactly `YYYY-MM-DD Archived Bilibili Favorites Batch NN`, using the current local date, where NN is the next available sequential batch number.

Deadline pressure, cached page state, or assumed reconstructability never permits canceling before a one-to-one DEVONthink bookmark archive for the batch is written and verified. The same-folder summary is still required for completion, but it is not a gate before cleanup. Treat archived BV IDs, not card positions or visible order, as the only destructive-action target.

Once the bookmark archive is verified, only cancel the exact BV IDs from that verified batch. Never extend cleanup to an ID outside the verified bookmark archive. If delayed verification already shows an archived BV ID absent, do not submit another unfavorite action for it.

Stop immediately when the user says not to continue. Preserve completed archive work, report exact verified and unresolved IDs, and do not collect another batch unless the user explicitly invokes the Skill again.
