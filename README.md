# Quan's Skills

Cross-host Agent Skills for Codex, OpenCode, and compatible hosts.

## Skills

- `archiving-to-devonthink`: Archive an AI conversation into DEVONthink as a concise Chinese Markdown retrospective plus a separate original transcript Markdown record.
- `archiving-douyin-favorites`: Archive explicitly selected Douyin favorites into DEVONthink Global Inbox bookmark records with comments, tags, and a same-folder Markdown summary before any confirmed exact-ID cleanup.
- `archiving-bilibili-favorites`: Archive and safely unfavorite Bilibili favorites in fixed batches of 40.
- `archiving-bilibili-following`: Archive and safely unfollow Bilibili accounts in fixed current-page batches of 24.
- `creating-conversation-handoffs`: Create a validated timestamped snapshot and stable `.oriki/handoffs/LATEST.md` index before continuing in a new conversation; create that directory when absent, while existing `oriki-handoffs/` and `.codex/handoffs/` indexes remain readable.
- `resuming-from-conversation-handoff`: Read a handoff, recheck mutable state, and continue the first unblocked step without repeating completed work.

## Required Capabilities

**Bilibili and Douyin list skills** (`archiving-douyin-favorites`, `archiving-bilibili-favorites`, `archiving-bilibili-following`) require:
- Authenticated browser automation that can inspect and operate the signed-in session, match stable content IDs, and verify removals.
- DEVONthink MCP operations that can discover Global Inbox and create, look up, update, tag, and verify groups and records.

They stop safely before observing the source list if either capability is unavailable.

**Conversation archiving** (`archiving-to-devonthink`) requires:
- Readable current conversation context (or an optional supported export source).
- DEVONthink MCP operations that can discover Global Inbox, find or create groups, import files, and verify record parents.
- A safe writable temporary directory.
- Optional: a conversation close or archive capability. When unavailable, the skill instructs the user to archive or delete manually.

**Conversation handoff pair** (`creating-conversation-handoffs`, `resuming-from-conversation-handoff`) requires:

- Readable current conversation context for generation.
- A writable current project or task worktree.
- Git, filesystem, test, and external-state inspection appropriate to the task.
- Optional task, thread, or session reading by source conversation reference when the handoff is insufficient.

New snapshots use a host-qualified source reference such as `opencode:session-123`.
Legacy UUID-only snapshots remain valid. If a host provides neither a stable ID nor
a lookup capability, the snapshot records `不可用：<原因>` and remains usable as a
file-based handoff.

Generation requires explicit invocation. It may be recommended when context-risk symptoms appear, but it does not write automatically and does not archive the source conversation.

## Install for Codex

Clone this repository:

```sh
git clone https://github.com/n0rk1n/Quan-s-skills.git
```

Copy a skill into Codex's local skills directory:

```sh
mkdir -p ~/.codex/skills
cp -R Quan-s-skills/<name> ~/.codex/skills/
```

Replace `<name>` with one of: `archiving-to-devonthink`, `archiving-douyin-favorites`, `archiving-bilibili-favorites`, `archiving-bilibili-following`, `creating-conversation-handoffs`, `resuming-from-conversation-handoff`.

To update an existing install:

```sh
git -C Quan-s-skills pull
rm -rf ~/.codex/skills/<name>
cp -R Quan-s-skills/<name> ~/.codex/skills/
```

## Install for OpenCode

Clone this repository as shown above, then copy a skill into OpenCode's skill discovery path:

```sh
mkdir -p ~/.config/opencode/skills
cp -R Quan-s-skills/<name> ~/.config/opencode/skills/<name>
```

OpenCode discovers the skill and loads it through its native `skill` tool. Users may explicitly name the skill in their request.

The complete skill directory is copied (not only `SKILL.md`), so references and scripts remain available.

## Invoke a Skill

- **Codex:** Explicitly name or invoke the skill in your request. The optional `agents/openai.yaml` metadata helps present the skill but does not replace explicit selection.
- **OpenCode:** Load the skill with the `skill` tool, then explicitly name or invoke the skill in your request.

Conversation handoff examples:

```text
Use creating-conversation-handoffs to prepare this task for a new conversation.
Use resuming-from-conversation-handoff to read this project's latest handoff and continue.
```

## Optional Host Metadata

Files under `agents/`, including `agents/openai.yaml`, are optional OpenAI/Codex interface metadata. OpenCode executes the host-neutral contract from `SKILL.md` and does not need those files.

## Notes

- New conversation archives use `Archived AI Conversations` daily groups. Existing Codex-named DEVONthink groups (e.g., `Archived Codex Conversations`) remain untouched and are not discovered or reused.
- The archive skill includes a bundled transcript exporter under `archiving-to-devonthink/scripts/conversation_exporter` for optional Codex JSONL and ChatGPT export support.
