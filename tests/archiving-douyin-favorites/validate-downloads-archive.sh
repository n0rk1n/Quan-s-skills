#!/bin/zsh

set -euo pipefail

repo_root="${0:A:h:h:h}"
skill_dir="$repo_root/skills/douyin/archiving-douyin-favorites"
archive_script="$skill_dir/scripts/archive_douyin_favorites.py"

if rg -n -i 'DEVONthink' "$skill_dir"; then
  print -u2 "FAIL: douyin skill still contains DEVONthink-specific behavior"
  exit 1
fi

rg -q -F '/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites' \
  "$skill_dir/SKILL.md" "$skill_dir/references/workflow.md"

rg -q '\.webloc' "$skill_dir/references/workflow.md"
rg -q '封面.*\.jpg' "$skill_dir/references/workflow.md"
rg -q -F '<concise-content-title>.webloc' "$skill_dir/references/workflow.md"
rg -q -F '<concise-content-title> 封面.jpg' "$skill_dir/references/workflow.md"
rg -q -F ' (2)' "$skill_dir/references/workflow.md"

if rg -n -F '<concise-content-title>--<content-id>' "$skill_dir"; then
  print -u2 "FAIL: new Douyin archive filenames still require a content-ID suffix"
  exit 1
fi

if rg -n '归档总结\.md|Summary Markdown File|daily summary|same-folder.*summary|Chinese summary Markdown|write Chinese summary' "$skill_dir"; then
  print -u2 "FAIL: douyin skill still requires a standalone summary Markdown file"
  exit 1
fi

rg -q 'authenticated browser automation' "$skill_dir/SKILL.md"
rg -q 'writable local filesystem' "$skill_dir/SKILL.md"

rg -q 'verified local archive|本地归档' "$skill_dir/SKILL.md" \
  "$skill_dir/references/workflow.md"

test -x "$archive_script"
python3 "$archive_script" --help >/dev/null
rg -q 'scripts/archive_douyin_favorites\.py' \
  "$skill_dir/SKILL.md" "$skill_dir/references/workflow.md" "$skill_dir/agents/openai.yaml"
rg -q 'verified_ids' "$skill_dir/references/workflow.md"

if rg -n -F 'If cleanup is requested' "$skill_dir"; then
  print -u2 "FAIL: verified Douyin cleanup is still optional"
  exit 1
fi

rg -q -F 'Unfavorite the exact verified archived IDs' \
  "$skill_dir/references/workflow.md"

print "PASS: douyin skill uses verified Downloads page links and matching cover images without a standalone summary"
