# Douyin Downloads Archive RED/GREEN Results

Date: 2026-09-03

Subagents were not used because the repository policy permits them only when explicitly requested. The baseline therefore used the repeatable static contract in `validate-downloads-archive.sh` plus manual scenario review.

## RED

Before editing the skill, the contract exited 1 because:

- integration-specific behavior was still required throughout the skill;
- `/Users/oriki/Downloads` did not appear as the destination; and
- no `.webloc` plus matching `详情.md` local artifact contract existed.

This was the expected failure: the old skill could not satisfy a local-only Downloads archive request.

## GREEN

After the minimal behavior change, the contract exited 0:

```text
PASS: douyin skill uses a verified Downloads archive with local page links, metadata, and summary
```

Manual review of the evaluation scenarios confirmed that the exact-ID selection, confirmation-dialog check, delayed verification, bounded retry, partial-completion reporting, and stop-on-request safeguards remain in place.

## REFACTOR

The workflow now uses one stable local shape for every favorite:

```text
<content-title>--<content-id>.webloc
<content-title>--<content-id> 详情.md
```

The stable content ID prevents filename collisions and enables safe same-day folder reuse. The detail file replaces record-only metadata, while the Chinese daily summary remains an aggregate artifact rather than the cleanup gate.
