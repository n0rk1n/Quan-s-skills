# Douyin Favorites Archive Workflow

## Workflow Checklist

1. Confirm the Skill was explicitly invoked and a signed-in browser is available.
2. Observe one bounded batch and record stable content IDs and visible facts.
3. Write the batch to durable Markdown before any destructive action.
4. Verify item-heading count, ID count, canonical-URL count, and uniqueness.
5. Ask for action-time confirmation of the exact archived ID set and count.
6. Unfavorite only the confirmed IDs, then reload, wait for lazy loading, and verify every confirmed ID.
7. Report verified removals and unresolved IDs. Stop if requested.

Never reorder these gates: `observe → archive → verify archive → confirm → unfavorite exact IDs → delayed verify`.

## Collecting a Batch

Use a bounded batch whose content IDs can be captured reliably. Record each card's stable content ID, content type (`video` or `note`), and only facts visible in the signed-in browser. Do not identify a destructive target by card position, visible order, “first N,” or a broad page selection.

Do not bypass login, CAPTCHA, access controls, rate limits, or platform safeguards. Stop if the session or page state is not trustworthy. Do not pre-read another batch after the user asks to stop.

## Archive Contract

Write one numbered item heading and exactly one canonical URL for every archived item:

```markdown
## 1. Visible title or concise label
https://www.douyin.com/video/1234567890
```

The URL must be either `https://www.douyin.com/video/<id>` or `https://www.douyin.com/note/<id>` and its `<id>` must match the archived content ID. Preserve the original Douyin link as the canonical URL; do not replace it with a search result, short link, author page, or reconstructed noncanonical URL.

Label visible facts as facts. Clearly mark any summary, interpretation, or inferred context as inference, and do not invent missing details. Add explicit caution rather than endorsement when recording medical, financial, benchmark, income, popularity, or product claims; visible engagement counts and creator assertions are not independent verification.

Before confirmation, count numbered item headings, archived IDs, canonical URLs, unique IDs, and unique canonical URLs. All counts must equal the batch size, and every ID and canonical URL must map one-to-one. Correct any mismatch before proceeding.

## Action-Time Confirmation

After the durable archive passes its counts and uniqueness checks, ask immediately before the destructive action. Name the exact content-ID set and its count, and state that only those archived items will be unfavorited. An initial request to archive or clean up is not action-time confirmation.

Any batch containing a new ID requires a new confirmation. Authorization covers retries only for a subset of the same confirmed IDs; it never expands to another ID. If the user declines or says not to continue, do not unfavorite anything.

## Exact-ID Unfavorite Procedure

Set `confirmed_ids` to the archived IDs approved at action time. For the initial submit, set `submission_ids = confirmed_ids`. For each partial-success retry, set `submission_ids = remaining_ids`. Require `submission_ids` to be a subset of `confirmed_ids`; never add an ID outside the confirmed set.

Locate and select items by matching `submission_ids`, never by card index or position. Require the UI-selected ID set to equal `submission_ids` for that submit; stop on any extra or missing ID. Submit only when the sets match. If delayed verification has already established that an ID is absent, treat it as verified removed and do not submit another action for it. Record the submitted ID set and the platform result without treating a success toast or changed visible count as final verification.

## Delayed Verification and Partial Success

After each submission, reload the favorites view and wait for lazy-loaded favorite cards before checking every confirmed ID. Use this exact retry model:

```text
confirmed_ids = archived IDs approved by the user
submit exact IDs
reload and wait for lazy-loaded favorite cards
remaining_ids = confirmed_ids still present
while remaining_ids is non-empty and progress is being made:
    submit only remaining_ids under the same batch authorization
    reload, wait, and recompute remaining_ids
```

Track the remaining set after each attempt. If the same remaining set persists across three attempts, stop and report it. Never expand the authorization to new IDs. Report partial success with exact verified-absent IDs and exact remaining IDs; mark the batch complete only when delayed verification finds none of `confirmed_ids` present.

## Stopping and Merging

When the user says not to continue, stop before collecting or acting on another batch. Keep already written notes and distinguish complete, partially successful, and unresolved batches. A later unrelated request must not implicitly resume this Skill.

When merging archive notes, deduplicate only by stable content ID. Preserve one numbered heading and one canonical URL per item, retain useful visible facts and cautions, and re-run all counts and uniqueness checks. Never use merging as permission to unfavorite.

## Common Mistakes

- Unfavoriting first because cached data appears sufficient to rebuild the archive.
- Selecting “the first N cards” instead of matching archived content IDs.
- Counting headings or unique URLs only after the destructive action.
- Treating the original request as fresh action-time confirmation.
- Trusting a toast or immediate viewport without reload and lazy-loading delay.
- Retrying all items, or adding newly observed IDs, after partial success.
- Repeating an unfavorite action after delayed verification already shows the ID absent.
- Continuing or pre-reading the next batch after the user says to stop.
