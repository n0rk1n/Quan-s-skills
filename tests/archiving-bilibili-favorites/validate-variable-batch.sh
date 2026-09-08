#!/bin/sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"

skill="$repo_root/skills/bilibili/archiving-bilibili-favorites/SKILL.md"
workflow="$repo_root/skills/bilibili/archiving-bilibili-favorites/references/workflow.md"
agent="$repo_root/skills/bilibili/archiving-bilibili-favorites/agents/openai.yaml"

# The skill must define one dynamic batch: all currently available stable items,
# capped at 40. A non-empty short batch must remain eligible for the full flow.
rg -Fq 'batch_size = min(40, available_stable_items)' "$skill"
rg -Fq '1–39' "$skill"
rg -Fq 'batch_size' "$workflow"
rg -Fq '最多 40' "$agent"

# Fixed-count wording would silently restore the old stop-at-less-than-40 behavior.
if rg -n 'exactly 40|observe exactly 40|fewer than 40.*stop|少于 40 个.*停止|均为 40|同一批 40 个|显示数量为 40|覆盖全部 40 条|严格只处理 40 条' "$skill" "$workflow"; then
  echo 'fixed-count behavior remains in the Bilibili archive skill' >&2
  exit 1
fi

echo 'variable Bilibili batch contract verified'
