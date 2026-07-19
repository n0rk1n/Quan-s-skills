---
name: archiving-bilibili-favorites
description: Use when explicitly invoked to archive a signed-in user's Bilibili favorites to DEVONthink and, when requested, cancel exactly the verified archived favorites in a bounded batch of 40.
---

# Archiving Bilibili Favorites

## Overview

Archive exactly one bounded batch of 40 Bilibili favorites before changing the Bilibili account. Treat the canonical video URL/BV ID as the sole cleanup identity, never card order or a broad selection.

## Preconditions

- Run only after explicit `$archiving-bilibili-favorites` invocation.
- Require a signed-in Bilibili browser session and working DEVONthink MCP. Do not bypass login, CAPTCHA, or platform safeguards.
- Require the user to explicitly request cancellation before changing favorites. Archive-only requests stop after verification and summary.
- Read [references/workflow.md](references/workflow.md) completely before observing favorites or creating DEVONthink records.

## Non-Negotiable Invariant

`verify DEVONthink → create fresh group → observe exactly 40 → create bookmarks → verify one-to-one mapping → select exact BV IDs → verify confirmation dialog → cancel → reload and verify → write Chinese summary`

Do not archive another batch in the same invocation. If fewer than 40 stable video identities are available, stop and report the shortfall; do not expand scope or use unstable cards.

## Completion

Report the DEVONthink folder, 40 bookmark count, summary record, verified removed IDs/URLs, and unresolved IDs. Record cover URLs in comments when visible; do not claim a cover was set as a DEVONthink thumbnail unless the available API actually supports writing it.
