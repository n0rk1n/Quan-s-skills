# Douyin Downloads Archive RED/GREEN Results

Date: 2026-09-03

Subagents were not used because the repository policy permits them only when explicitly requested. The baseline therefore used the repeatable static contract in `validate-downloads-archive.sh` plus manual scenario review.

## RED

Before this revision, the updated contract exited 1 because the workflow still:

- generated `YYYY-MM-DD DouYin 收藏归档总结.md`;
- included summary writing and verification in the mandatory sequence; and
- treated the daily summary as a completion requirement.

This was the expected failure: the skill required a third artifact even though the desired contract contains only the page link and matching detail file.

## GREEN

After the minimal behavior change, the contract exited 0:

```text
PASS: douyin skill uses verified Downloads page links and matching detail files without a standalone summary
```

Manual review of the evaluation scenarios confirmed that the exact-ID selection, confirmation-dialog check, delayed verification, bounded retry, partial-completion reporting, and stop-on-request safeguards remain in place.

## REFACTOR

The workflow now uses one stable local shape for every favorite:

```text
<content-title>--<content-id>.webloc
<content-title>--<content-id> 详情.md
```

The stable content ID prevents filename collisions and enables safe same-day folder reuse. A current-batch item is complete only when both its `.webloc` and matching `详情.md` file pass read-back verification; no separate aggregate Markdown file is created.
