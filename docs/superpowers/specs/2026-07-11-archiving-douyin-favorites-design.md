# Archiving Douyin Favorites Skill Design

## Goal

Create a personal Codex Skill that archives a signed-in user's Douyin favorites into durable Markdown notes, preserves every original content URL, and optionally unfavorites only the items already archived and explicitly confirmed by the user.

The Skill is user-level and explicit-invocation only. It must never enter model context implicitly.

## Scope

The Skill supports:

- Reading Douyin's “我的 → 收藏 → 视频” page through an available signed-in browser.
- Processing a bounded batch, defaulting to 20 items unless the user specifies another size.
- Summarizing visible captions, metadata, cards, frames, and chapter information without inventing missing details.
- Saving a Markdown archive containing one original URL per item before any unfavorite action.
- Asking for action-time confirmation before each destructive batch.
- Selecting items by stable Douyin content ID rather than card position.
- Reloading, waiting for lazy-loaded results, and retrying only the still-present IDs when Douyin partially applies a confirmed batch.
- Stopping without reading another batch when the user says to stop.
- Merging completed batch archives and verifying item count, URL count, URL uniqueness, and absence of pending status.

The Skill does not automate login, bypass CAPTCHA or safety interstitials, download videos, or treat medical, financial, income, benchmark, popularity, or product claims as verified facts.

## Package Layout

```text
archiving-douyin-favorites/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    └── workflow.md
```

- `SKILL.md`: concise operational contract, safety gates, and reference routing.
- `references/workflow.md`: detailed batch procedure, archive shape, partial-submit recovery, and verification checklist.
- `agents/openai.yaml`: UI metadata and `policy.allow_implicit_invocation: false`.

No executable script is planned. Browser DOM and UI state are variable, while archive merging and count checks are simple mechanical operations that Codex can perform with available filesystem tools.

## Invocation and Installation

- Skill name and folder: `archiving-douyin-favorites`.
- Canonical source: `/Users/oriki/Documents/Quan's skills/archiving-douyin-favorites`.
- User installation: `~/.codex/skills/archiving-douyin-favorites` points to the canonical source.
- Explicit invocation: `$archiving-douyin-favorites`.
- `agents/openai.yaml` sets `policy.allow_implicit_invocation: false`; ordinary requests must not inject the Skill automatically.

## Workflow Contract

1. Confirm browser/login readiness, output location, and batch size.
2. Read only the current batch and capture content IDs, authors, visible text, and canonical URLs.
3. Write the batch archive with a processing-status line and one numbered section per item.
4. Verify the archive has matching section, URL, and unique-URL counts.
5. Ask for confirmation naming the exact number of items to unfavorite.
6. After confirmation, select only archived content IDs and inspect the site's confirmation dialog before submitting.
7. Reload, wait for lazy loading, and compare all confirmed IDs against the page.
8. If a subset remains, repeat only for that subset under the same narrowly confirmed batch; do not add new IDs.
9. Mark the archive complete only after all confirmed IDs are absent.
10. Continue to another batch only when the user asks. On request, merge archives and verify aggregate counts.

## Output Contract

Each batch archive contains:

- Scope, evidence limitations, and current status.
- A short cross-item knowledge synthesis.
- Numbered item headings.
- Author/type when visible.
- One canonical Douyin URL.
- A factual content summary.
- A reusable knowledge takeaway with appropriate uncertainty.
- Optional executable checklist when the batch contains actionable material.

Missing titles, captions, or steps are labeled as insufficient metadata rather than reconstructed.

## Safety and Failure Handling

- Archiving always precedes unfavoriting.
- Each new destructive batch requires action-time confirmation.
- A confirmation covers only the named archived IDs, even if the UI exposes more favorites.
- Douyin's partial batch application is expected: verify after delayed loading rather than trusting a toast or an initially empty DOM.
- CAPTCHA, login, permission, and safety prompts return control to the user.
- If archive verification fails, do not unfavorite.
- If final ID verification fails repeatedly, preserve the archive, report remaining IDs, and stop.

## Test Strategy

Follow RED-GREEN-REFACTOR for documentation:

1. RED: run fresh subagent scenarios without the Skill that combine time pressure, destructive action pressure, and misleading page state. Capture failures such as unfavoriting before saving, trusting immediate reload state, selecting by position, skipping reconfirmation, or continuing beyond the requested stop point.
2. GREEN: implement the minimal Skill that directly addresses observed failures, then repeat the same scenarios with explicit Skill loading.
3. REFACTOR: run variation scenarios for partial server application, missing metadata, stop-after-current-batch, and manual-only invocation. Tighten wording only for observed gaps.
4. Validate package structure and metadata with `quick_validate.py`.
5. Verify `allow_implicit_invocation: false`, the explicit `$archiving-douyin-favorites` default prompt, path layout, word/line limits, and README entry.

Forward tests must not operate the live Douyin account. They evaluate decisions and proposed actions against synthetic page states.

## Git Delivery

Update the repository README, commit the implementation after tests and validation pass, and push `main` to the configured `origin`. Before pushing, verify the worktree is clean except for intended files and confirm the commit contains no archived personal Douyin content.
