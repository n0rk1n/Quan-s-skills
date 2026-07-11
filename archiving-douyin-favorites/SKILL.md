---
name: archiving-douyin-favorites
description: Use when explicitly invoked for a signed-in user's Douyin favorites, especially when the user wants durable Markdown notes, preserved original URLs, or controlled cleanup.
---

# Archiving Douyin Favorites

## Manual-Only Operation

Run this Skill only when the user explicitly invokes `$archiving-douyin-favorites`. Do not infer invocation from a related request, resume it for an unrelated request, or continue after the user says not to continue.

Require an available browser already signed in to Douyin. Never attempt to bypass login, CAPTCHA, access controls, rate limits, or other platform safeguards. If the signed-in session is unavailable or a challenge blocks access, stop and report the blocker.

Before observing or acting on favorites, read [references/workflow.md](references/workflow.md) completely and follow every checklist item.

## Safety Invariant

Preserve this order without exception:

`observe → archive → verify archive → confirm → unfavorite exact IDs → delayed verify`

Deadline pressure, cached page state, or assumed reconstructability never permits unfavoriting before the archive is written and verified. Treat archived content IDs—not card positions, visible order, or broad selection—as the only destructive-action target.

Ask for action-time confirmation naming the exact ID set and count. Never extend that authorization to an ID not named in the confirmed batch. If delayed verification already shows a confirmed ID absent, do not submit another unfavorite action for it.

Stop immediately when the user says not to continue. Preserve completed archive work, report exact verified and unresolved IDs, and do not collect another batch unless the user explicitly invokes the Skill again.
