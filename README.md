# Quan's Skills

Cross-host Agent Skills for Codex, OpenCode, and compatible hosts.

## Skills

- `archiving-to-devonthink`: Archive an AI conversation into DEVONthink as a concise Chinese Markdown retrospective plus a separate original transcript Markdown record.
- `archiving-douyin-favorites`: Archive explicitly selected Douyin favorites into DEVONthink Global Inbox bookmark records with comments, tags, and a same-folder Markdown summary before any confirmed exact-ID cleanup.
- `archiving-bilibili-favorites`: Archive and safely unfavorite Bilibili favorites in fixed batches of 40.

## Required Capabilities

**Favorites skills** (`archiving-douyin-favorites`, `archiving-bilibili-favorites`) require:
- Authenticated browser automation that can inspect and operate the signed-in session, match stable content IDs, and verify removals.
- DEVONthink MCP operations that can discover Global Inbox and create, look up, update, tag, and verify groups and records.

They stop safely before observing favorites if either capability is unavailable.

**Conversation archiving** (`archiving-to-devonthink`) requires:
- Readable current conversation context (or an optional supported export source).
- DEVONthink MCP operations that can discover Global Inbox, find or create groups, import files, and verify record parents.
- A safe writable temporary directory.
- Optional: a conversation close or archive capability. When unavailable, the skill instructs the user to archive or delete manually.

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

Replace `<name>` with one of: `archiving-to-devonthink`, `archiving-douyin-favorites`, `archiving-bilibili-favorites`.

To update an existing install:

```sh
git -C Quan-s-skills pull
rm -rf ~/.codex/skills/<name>
cp -R Quan-s-skills/<name> ~/.codex/skills/
```

The complete skill directory is copied (not only `SKILL.md`) so that references, workflows, and scripts remain available.

## Install for OpenCode

Clone this repository as shown above, then copy a skill into OpenCode's skill discovery path:

```sh
mkdir -p ~/.config/opencode/skills
cp -R Quan-s-skills/<name> ~/.config/opencode/skills/<name>
```

OpenCode discovers the skill and loads it through its native `skill` tool. Users may explicitly name the skill in their request.

## Invoke a Skill

- **Codex:** The skill triggers automatically when the request matches its description. The optional `agents/openai.yaml` metadata can tune invocation behavior.
- **OpenCode:** Load the skill with the `skill` tool; then explicitly name or invoke the skill in your prompt. Favorites skills only run when explicitly invoked.

## Optional Host Metadata

Files under `agents/`, including `agents/openai.yaml`, are optional OpenAI/Codex interface metadata. OpenCode executes the host-neutral contract from `SKILL.md` and does not need those files.

## Notes

- New conversation archives use `Archived AI Conversations` daily groups. Existing Codex-named DEVONthink groups (e.g., `Archived Codex Conversations`) remain untouched and are not discovered or reused.
- The archive skill includes a bundled transcript exporter under `archiving-to-devonthink/scripts/conversation_exporter` for optional Codex JSONL and ChatGPT export support.
