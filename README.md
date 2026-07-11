# Quan's Skills

Personal Codex skills collection.

## Skills

- `archiving-to-devonthink`: archive a Codex or ChatGPT conversation into DEVONthink as a concise Chinese Markdown retrospective plus a separate original transcript Markdown record.
- `archiving-douyin-favorites`: archive explicitly selected Douyin favorites to verified Markdown before any confirmed exact-ID cleanup.

The archive skill includes a bundled transcript exporter under
`archiving-to-devonthink/scripts/conversation_exporter`. It supports local
Codex JSONL sessions/archives and official ChatGPT `conversations.json` or ZIP
exports. Transcript Markdown reserves `## 用户` and `## AI` for role markers and
keeps generated content at heading level three or shallower outside code blocks.

## Install

Clone this repository on another machine:

```sh
git clone https://github.com/n0rk1n/Quan-s-skills.git
```

Copy the skill into Codex's local skills directory:

```sh
mkdir -p ~/.codex/skills
cp -R Quan-s-skills/archiving-to-devonthink ~/.codex/skills/
```

To update an existing install:

```sh
git -C Quan-s-skills pull
rm -rf ~/.codex/skills/archiving-to-devonthink
cp -R Quan-s-skills/archiving-to-devonthink ~/.codex/skills/
```

Install the Douyin favorites Skill from this repository's local checkout:

```sh
ln -s "/Users/oriki/Documents/Quan's skills/archiving-douyin-favorites" \
  "$HOME/.codex/skills/archiving-douyin-favorites"
```

Invoke it explicitly with `$archiving-douyin-favorites`. It does not trigger
implicitly.
