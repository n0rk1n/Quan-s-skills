# Handoff CLI Implementation Plan

**Goal:** Add publish and read-only resume commands to the existing handoff tools.
**Architecture:** One standard-library Python CLI beside handoff_contract.py; both skills resolve that shared tool. AI authors and reviews the content; scripts handle validation and filesystem operations.
**Spec:** User-approved publish/resume proposal in this task.

- [x] Add CLI integration tests for publish/read round trip, invalid input, index preservation, collisions, legacy priority, unsafe links, and Git inspection without mutation. Run them before implementation.
- [x] Implement scripts/handoff.py in creating-conversation-handoffs. Require an explicit root for publishing; accept root or snapshot for resume. Validate staged content, atomically link snapshots without clobbering, then atomically replace the validated index. Report partial publication accurately.
- [x] Update both SKILL.md files with executable commands and shared-tool dependency. Preserve AI semantic review, authorization, and live-state recheck requirements.
- [x] Run handoff and repository Python tests, inspect diff and original checkout status, commit task files only. Retain branch and worktree without merging or pushing.

Tests use unittest and temporary directories; runtime needs Python 3.9+ and no third-party packages. Do not create tasks, archive conversations, execute snapshot commands, or infer roots from skill paths. No subagents per user policy.

Verification: 49 handoff tests and all 105 Python tests pass. Fault injection confirms a failed index replacement preserves the previous index and reports the published snapshot. Concurrent CLI publishers either publish unique snapshots or fail explicitly on the lock. Original checkout changes were not copied into this worktree.
