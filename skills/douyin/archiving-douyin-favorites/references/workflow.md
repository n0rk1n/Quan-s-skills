# Douyin Favorites Archive Workflow

## Workflow Checklist

Map host tools by semantic capability, not by exact name.

1. Confirm explicit invocation, authenticated browser automation, Python 3, `file`, `sips`, HTTPS access to observed cover URLs, and writable local filesystem access to `/Users/oriki/Downloads`.
2. Observe one bounded batch: 24 favorites by default, or the user's requested count. Record stable ID, type, canonical URL, concise content title, and the actual cover URL associated with that ID.
3. Pass the batch to `scripts/archive_douyin_favorites.py`; it creates or reuses `/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites` with the current local date.
4. Require exit code 0, empty `failed_items`, and `verified_ids` equal to the entire observed batch before cleanup.
5. Unfavorite the exact verified archived IDs, following the selection, confirmation dialog, and delayed verification gates below.
6. Report destination, verified link/cover count, verified removals, and unresolved IDs. Stop after this batch.

Never reorder: `verify capabilities → observe → run archive script → accept complete verified_ids → select exact archived IDs → inspect dialog → unfavorite → delayed verify`.

## Collecting Covers

Use authenticated browser evidence to associate each cover with its stable content ID. Read the actual image source from the matching favorite card or video page (for example its image source or video poster). For a note, use the visible first-image cover. Wait for lazy-loaded images and reject placeholders, avatars, unrelated recommendations, and guessed URLs. Preserve the full observed HTTPS URL, including query parameters. Do not reconstruct CDN addresses or save a screenshot in place of the cover.

If no trustworthy cover URL can be obtained, stop and report the unresolved ID. Do not fall back to a detail file and do not clean up the batch. If an image request fails, refresh the same item's browser evidence and retry with its newly observed URL; do not bypass login, CAPTCHA, access controls, or rate limits. The script uses a Douyin Referer and a browser User-Agent, but does not extract browser cookies or guarantee access to every CDN URL.

## Archive Script Contract

Run Python 3 with the installed skill's helper:

```text
python3 <skill-directory>/scripts/archive_douyin_favorites.py
python3 <skill-directory>/scripts/archive_douyin_favorites.py --input <batch-json>
```

Both forms accept one JSON object with a non-empty `items` array. Keep an input file outside the dated archive directory. Each item is:

```json
{
  "id": "7530000000000000001",
  "type": "video",
  "url": "https://www.douyin.com/video/7530000000000000001",
  "title": "基于页面内容的简洁标题",
  "cover_url": "https://<observed-cover-host>/<observed-image-path>"
}
```

Replace the illustrative cover URL with the real browser-observed URL. Canonical URLs must be exactly `https://www.douyin.com/video/<id>` or `https://www.douyin.com/note/<id>`; type and ID must agree. Duplicate IDs, noncanonical URLs, and missing or non-HTTPS cover URLs fail validation before directory creation.

The script downloads each cover with a 30-second request timeout and a 20 MiB limit. It checks actual MIME with `file` and readable nonzero dimensions with macOS `sips`, then uses the detected jpg/png/webp/gif extension. It writes atomically and rechecks both files before adding the ID to `verified_ids`. MIME and dimensions are technical checks; the browser observation must establish that the picture belongs to the item.

The JSON result is:

```json
{
  "destination": "/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites",
  "verified_ids": ["7530000000000000001"],
  "failed_items": [],
  "pairs_written": 1
}
```

Exit 0 means the complete batch passed verification. Exit 1 means item failures: preserve completed files, report failures, and do not clean up any of the batch. Exit 2 means invalid input or destination preconditions. Never infer success from file presence or extend `verified_ids` manually.

## Local Files and Reuse

The exact daily destination is `/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites`. Do not use a repository, Desktop, temporary directory, cloud drive, or other substitute for real archives. Temporary test fixtures are separate from real archival runs.

Each new favorite produces exactly two files:

```text
<concise-content-title>.webloc
<concise-content-title> 封面.jpg
```

The cover extension reflects its actual format. Use the same filesystem-safe title for both. Resolve unrelated title collisions with ` (2)`, ` (3)`, etc. New filenames omit long content IDs. The `.webloc` is an XML property list whose `URL` is the exact canonical URL, preserving the ID without a separate metadata file.

Do not create `详情.md`, summaries, or manifests in the archive directory. Existing legacy detail files remain untouched. Repeat invocations identify an existing item by the canonical URL in its `.webloc`, reuse that filename (including legacy ID suffixes), and add a missing cover. Existing valid cover/link pairs are verified and reused without downloading again. Multiple matching links, multiple covers, invalid existing covers, or conflicting legacy ID links are failures, not permission to overwrite. Preserve unrelated files.

## Cleanup Gate

Maintain a one-to-one ID/URL mapping between browser evidence and canonical link contents, and visually confirm the observed cover belongs to that same ID. An item is archived only when its link and matching cover both pass read-back verification. A link alone, a cover URL alone, or an old detail file is insufficient.

Only accept the complete batch's `verified_ids` with exit 0 and no failures. A cover failure blocks cleanup for the batch. Use the script for naming, downloading, writing, and verification rather than recreating its logic. Do not ask for extra confirmation solely for cleanup within an explicitly invoked archive run; respect a user stop immediately.

## Exact-ID Unfavorite Procedure

Set `archived_ids` to the script's complete-batch `verified_ids`. For the initial submit, set `submission_ids = archived_ids`. For each partial-success retry, set `submission_ids = remaining_ids`. Require `submission_ids` to be a subset of `archived_ids`; never add an ID outside the verified local archive.

Locate and select items by matching `submission_ids`, never by card index or position. Require the UI-selected ID set to equal `submission_ids` for that submit; stop on any extra or missing ID.

Before the final destructive submit, inspect Douyin's confirmation dialog. Verify that its displayed destructive scope and count match the current `submission_ids`; if the dialog exposes item identifiers, verify those identifiers too. Abort before final submission on any mismatch, extra item, unverifiable scope, or unexpected count.

Submit only after both the selection and dialog gates match. If delayed verification has already established that an ID is absent, treat it as verified removed and do not submit another action for it. Record the submitted ID set and platform result without treating a success toast or changed visible count as final verification.

## Delayed Verification and Partial Success

After each submission, reload the favorites view and wait for lazy-loaded favorite cards before checking every archived ID submitted for cleanup:

```text
archived_ids = IDs from verified local link/cover pairs
submit exact IDs
reload and wait for lazy-loaded favorite cards
remaining_ids = archived_ids still present
while remaining_ids is non-empty and progress is being made:
    submit only remaining_ids from the same verified local batch
    reload, wait, and recompute remaining_ids
```

If the same remaining set persists across three attempts, stop and report it. Never expand cleanup to new IDs. Report partial success with exact verified-absent IDs and exact remaining IDs; mark the batch complete only when delayed verification finds none of `archived_ids` present.

## Stopping

When the user says not to continue, stop before collecting or acting on another batch. Keep already written files and distinguish complete, partially successful, and unresolved batches. A later unrelated request must not implicitly resume this Skill.
