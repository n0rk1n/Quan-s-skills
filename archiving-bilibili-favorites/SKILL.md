---
name: archiving-bilibili-favorites
description: Use when explicitly invoked to archive a signed-in user's Bilibili favorites to DEVONthink in one bounded batch of up to 40.
---

# Archiving Bilibili Favorites

## Overview

Archive exactly one bounded batch of up to 40 Bilibili favorites before changing the Bilibili account. Treat the canonical video URL/BV ID as the sole cleanup identity, never card order or a broad selection.

## Preconditions

- Run only after explicit `$archiving-bilibili-favorites` invocation.
- Require a signed-in Bilibili browser session and working DEVONthink MCP. Do not bypass login, CAPTCHA, or platform safeguards.
- The explicit invocation authorizes cancellation of exactly the favorites in this batch that pass the DEVONthink one-to-one verification. Do not request a second confirmation.
- If the archive verification does not pass, stop without changing Bilibili favorites; archive-only completion is not a supported outcome of this skill.
- Read [references/workflow.md](references/workflow.md) completely before observing favorites or creating DEVONthink records.

## Non-Negotiable Invariant

Set `batch_size = min(40, available_stable_items)`, where `available_stable_items` is the number of unique, stable BV ID/canonical URL pairs in the current favorites folder after reaching either 40 pairs or the confirmed end of the folder.

`verify DEVONthink → create fresh group → determine batch_size → create batch_size bookmarks → verify one-to-one mapping → select exact BV IDs → verify confirmation dialog count equals batch_size → cancel → reload and verify → write Chinese summary`

Do not archive another batch in the same invocation. If `batch_size` is 1–39, continue with all currently available stable items. If it is 0, stop without changing Bilibili. Never expand scope or use unstable cards to fill the batch.

## Completion

Report the DEVONthink folder, `batch_size` bookmark count, summary record, verified removed IDs/URLs, and unresolved IDs. Record cover URLs in comments when visible; do not claim a cover was set as a DEVONthink thumbnail unless the available API actually supports writing it.
