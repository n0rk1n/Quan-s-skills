# Quan's Skills

Cross-host Agent Skills for Codex, OpenCode, and compatible hosts.

## Skills

Skills are grouped by subject under `skills/`; every leaf directory is a complete, independently installable skill.

| Category | Repository path | Skill |
| --- | --- | --- |
| Conversation | `skills/conversation/archiving-ai-conversation` | `archiving-ai-conversation`: Save an AI conversation to Downloads as a concise Chinese Markdown retrospective plus a separate original transcript Markdown file. |
| Bilibili | `skills/bilibili/archiving-bilibili-favorites` | `archiving-bilibili-favorites`: Save video records and cover images to Downloads, then safely unfavorite one batch of up to 40. |
| Bilibili | `skills/bilibili/archiving-bilibili-following` | `archiving-bilibili-following`: Save account records and avatar images to Downloads, then safely unfollow one current-page batch of 24. |
| Douyin | `skills/douyin/archiving-douyin-favorites` | `archiving-douyin-favorites`: Archive explicitly selected Douyin favorites into a dated folder under `/Users/oriki/Downloads`, with one local page link and matching cover image per item before any confirmed exact-ID cleanup. |
| Conversation | `skills/conversation/creating-conversation-handoffs` | `creating-conversation-handoffs`: Create a validated timestamped snapshot and stable `.oriki/handoffs/LATEST.md` index before continuing in a new conversation; create that directory when absent, while existing `oriki-handoffs/` and `.codex/handoffs/` indexes remain readable. |
| Conversation | `skills/conversation/resuming-from-conversation-handoff` | `resuming-from-conversation-handoff`: Read a handoff, recheck mutable state, and continue the first unblocked step without repeating completed work. |

## Required Capabilities

**Bilibili list skills** (`archiving-bilibili-favorites`, `archiving-bilibili-following`) require:
- Authenticated browser automation that can inspect and operate the signed-in session, match stable content IDs, and verify removals.
- Writable local filesystem access to `~/Downloads`, Python 3.10+, `curl`, and `file` for the bundled `scripts/archive_bilibili.py` CLI.

They stop safely before observing the source list if either capability is unavailable. Each dated batch contains `archive.json`, one ID directory per item with `record.md` and its downloaded image, and `summary.md`. All records and images must pass read-back verification before any unfavorite/unfollow action. Image failures stop cleanup for the whole batch. Both independently installable skills bundle the same CLI for preflight, archive, verify, resume, and status/summary updates. Browser automation supplies observed JSON and cleanup evidence; the script never performs account actions. Read each skill’s `references/script-usage.md` for schemas and commands.

Bilibili archives use `~/Downloads/YYYY-MM-DD Archived Bilibili Favorites Batch NN/` or `~/Downloads/YYYY-MM-DD Archived Bilibili Following Batch NN/`. Image saving is built into both archive skills; the former standalone cover skill has been removed. Existing archives are not migrated. Installed copies are separate from this repository: when updating an installation, replace both complete archive skill directories and remove the obsolete cover skill directory from that host’s skill discovery path.

**Douyin favorites** (`archiving-douyin-favorites`) requires:

- Authenticated browser automation with the same exact-ID and delayed-removal verification safeguards.
- Writable local filesystem access to `/Users/oriki/Downloads` for the dated archive directory, `.webloc` page links, and matching cover images (verified with macOS `file` and `sips`).
- Python 3 for the bundled `scripts/archive_douyin_favorites.py` writer and read-back verifier.

It stops safely before observing favorites if either capability is unavailable.

**Conversation archiving** (`archiving-ai-conversation`) requires:
- Readable current conversation context (or an optional supported export source).
- Writable local filesystem access to `~/Downloads/YYYY-MM-DD Archived AI Conversations/`, including read-back verification. Both Markdown files are retained permanently; no DEVONthink connection is required.
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

Copy a complete skill directory into Codex's local skills directory. The destination stays flat: `SKILL.md` must be at `~/.codex/skills/<name>/SKILL.md`.

```sh
mkdir -p ~/.codex/skills
cp -R Quan-s-skills/skills/<category>/<name> ~/.codex/skills/
```

Use the category shown in the table above; for example, `skills/conversation/creating-conversation-handoffs`.

To update an existing install:

```sh
git -C Quan-s-skills pull
rm -rf ~/.codex/skills/<name>
cp -R Quan-s-skills/skills/<category>/<name> ~/.codex/skills/
```

## Install for OpenCode

Clone this repository as shown above, then copy a skill into OpenCode's skill discovery path:

```sh
mkdir -p ~/.config/opencode/skills
cp -R Quan-s-skills/skills/<category>/<name> ~/.config/opencode/skills/<name>
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

- New conversation archives are kept in `~/Downloads/YYYY-MM-DD Archived AI Conversations/`. Existing DEVONthink archives are untouched.
- The archive skill includes `scripts/archive_conversation.py` for Downloads access checks, paired Markdown generation, collision handling, transcript links, and read-back verification. It requires Python 3.10+ on macOS/Linux and uses only the standard library. See the skill's `references/script-usage.md` for JSON input and commands.
- The archive skill includes a bundled transcript exporter under `archiving-ai-conversation/scripts/conversation_exporter` for optional Codex JSONL and ChatGPT export support.
