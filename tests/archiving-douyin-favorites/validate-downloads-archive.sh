#!/bin/zsh

set -euo pipefail

repo_root="${0:A:h:h:h}"
skill_dir="$repo_root/skills/douyin/archiving-douyin-favorites"

if rg -n -i 'DEVONthink' "$skill_dir"; then
  print -u2 "FAIL: douyin skill still contains DEVONthink-specific behavior"
  exit 1
fi

rg -q -F '/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites' \
  "$skill_dir/SKILL.md" "$skill_dir/references/workflow.md"

rg -q '\.webloc' "$skill_dir/references/workflow.md"
rg -q '详情.*\.md|metadata.*\.md' "$skill_dir/references/workflow.md"
rg -q '归档总结\.md' "$skill_dir/references/workflow.md"

rg -q 'authenticated browser automation' "$skill_dir/SKILL.md"
rg -q 'writable local filesystem' "$skill_dir/SKILL.md"

rg -q 'verified local archive|本地归档' "$skill_dir/SKILL.md" \
  "$skill_dir/references/workflow.md"

print "PASS: douyin skill uses a verified Downloads archive with local page links, metadata, and summary"
