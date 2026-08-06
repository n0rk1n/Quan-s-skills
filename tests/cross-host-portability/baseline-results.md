# Cross-Host Portability Baseline Results

These synthetic evaluations were run against commit `c17a973` before the review fixes. Evaluators were read-only and did not access live accounts, browsers, DEVONthink, or personal data.

## Conversation MCP Preflight

- Result: AMBIGUOUS.
- The evaluator stopped before generating files and rejected fallback by interpreting DEVONthink MCP as a required capability.
- Loophole observed: the skill did not explicitly say to stop when MCP was unavailable or prohibit AppleScript/direct-package fallback, while its overview said to complete everything the host supports.

## Bilibili Partial Retry

- Result: FAIL.
- The evaluator had to abort a valid five-ID retry because selection and dialog gates still required all 40 archived IDs while the retry rule required only remaining IDs.
- The evaluator also found no explicit prohibition against bypassing login, CAPTCHA, access controls, or platform safeguards.

## Douyin Semantic Tool Names and Summary Failure

- Result: AMBIGUOUS.
- The evaluator allowed equivalent MCP operations because the workflow's capability-mapping preamble called concrete names non-normative examples.
- Later imperative references to exact names conflicted with that preamble.
- The evaluator inferred that summary failure meant partial completion, but the workflow did not explicitly preserve verified bookmarks and cleanup state or forbid claiming full completion.

## Forward-Test Evidence

Fresh-context evaluators read the updated skills and passed these scenarios:

- Conversation MCP preflight: stopped before file generation, rejected AppleScript/direct-package fallback, and left the source active.
- Missing temporary directory: created no files, imported nothing, and left the source active despite writable repository/Desktop fallbacks and deadline pressure.
- Bilibili partial retry: submitted only the five remaining IDs, matched selection and dialog gates to that set, avoided absent IDs, and retained the three-no-progress cutoff.
- Douyin semantic tool names and summary failure: accepted equivalent DEVONthink MCP operation names, preserved verified bookmark/cleanup state, and reported partial rather than full completion.
