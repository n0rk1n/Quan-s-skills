#!/bin/zsh

set -euo pipefail

repo_root="${0:A:h:h}"
script="$repo_root/skills/bilibili/adding-bilibili-covers-to-devonthink/scripts/process-bilibili-covers.zsh"
test_dir="$(mktemp -d /tmp/test-bilibili-cover-skill.XXXXXX)"
trap 'rm -rf "$test_dir"' EXIT

manifest="$test_dir/manifest.jsonl"
: > "$manifest"

for i in {1..8}; do
  jq -nc --arg uuid "missing-$i" --arg name "Missing $i" \
    '{uuid:$uuid,name:$name,filename:($name + ".webloc"),coverUrl:null}' >> "$manifest"
done

for i in {1..65}; do
  padded=$(printf '%02d' "$i")
  jq -nc --arg uuid "eligible-$padded" --arg name "重复标题" \
    --arg filename "重复标题.webloc" \
    --arg url "https://i0.hdslb.com/bfs/archive/$padded.webp" \
    '{uuid:$uuid,name:$name,filename:$filename,coverUrl:$url}' >> "$manifest"
done

plan="$($script --plan-manifest "$manifest")"

[[ "$(jq -r '.selected_count' <<< "$plan")" == "50" ]]
[[ "$(jq -r '.selected[0].uuid' <<< "$plan")" == "eligible-01" ]]
[[ "$(jq -r '.selected[49].uuid' <<< "$plan")" == "eligible-50" ]]
[[ "$(jq -r '[.selected[].uuid == "eligible-51"] | any' <<< "$plan")" == "false" ]]
[[ "$(jq -r '[.selected[].name == "重复标题"] | all' <<< "$plan")" == "true" ]]

small_manifest="$test_dir/small.jsonl"
: > "$small_manifest"
for i in {1..12}; do
  jq -nc --arg uuid "small-$i" --arg name "Small $i" \
    --arg url "https://i1.hdslb.com/bfs/archive/$i.webp" \
    '{uuid:$uuid,name:$name,filename:($name + ".webloc"),coverUrl:$url}' >> "$small_manifest"
done

small_plan="$($script --plan-manifest "$small_manifest")"
[[ "$(jq -r '.selected_count' <<< "$small_plan")" == "12" ]]

help_text="$($script --help)"
[[ "$help_text" == "Usage:"$'\n'"  process-bilibili-covers.zsh --root <DEVONthink UUID> [--plan-only]"* ]]
[[ "$help_text" == *"--root <DEVONthink UUID>"* ]]
[[ "$help_text" == *"at most 50"* ]]

grep -Fq '页面可见封面地址|可见封面 URL|封面 URL' "$script"
grep -Fq 'i0.hdslb.com/i1.hdslb.com' "$script"
grep -Fq 'pic.name=title' "$script"
grep -Fq '封面来源书签 UUID：' "$script"
grep -Fq 'app.move({record:bm,from:src,to:dst})' "$script"

print -- "bilibili_cover_batch_limit=PASS"
print -- "bilibili_cover_stable_identity=PASS"
print -- "bilibili_cover_exact_display_name=PASS"
print -- "bilibili_cover_live_workflow_contract=PASS"
