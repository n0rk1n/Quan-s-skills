# Quan's Skills

Personal Codex skills collection.

## Skills

- `archiving-to-devonthink`: archive a Codex thread into DEVONthink as a concise Chinese Markdown retrospective.

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
