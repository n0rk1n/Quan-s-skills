#!/usr/bin/env bash
# Delegate one implementation plan to a stdin-driven local coding CLI.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run-plan-cli.sh --plan PLAN [--repo REPO] [--evidence-dir DIR] [--dry-run] -- CLI [ARG...]

Example:
  run-plan-cli.sh --repo /repo --plan /repo/docs/superpowers/plan.md -- reasonix run --max-steps 80

The CLI receives a task on stdin. Evidence defaults to a new directory under TMPDIR.
EOF
}

plan=""
repo="$PWD"
evidence_dir=""
dry_run=false
cli=()

while (($#)); do
  case "$1" in
    --plan) plan=${2:?"--plan needs a path"}; shift 2 ;;
    --repo) repo=${2:?"--repo needs a path"}; shift 2 ;;
    --evidence-dir) evidence_dir=${2:?"--evidence-dir needs a path"}; shift 2 ;;
    --dry-run) dry_run=true; shift ;;
    --help|-h) usage; exit 0 ;;
    --) shift; cli=("$@"); break ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 64 ;;
  esac
done

[[ -n "$plan" ]] || { printf '%s\n' 'Missing --plan' >&2; usage >&2; exit 64; }
[[ ${#cli[@]} -gt 0 ]] || { printf '%s\n' 'Missing CLI command after --' >&2; usage >&2; exit 64; }
[[ -d "$repo" ]] || { printf 'Repository directory does not exist: %s\n' "$repo" >&2; exit 66; }

repo=$(cd "$repo" && pwd -P)
if [[ "$plan" != /* ]]; then plan="$PWD/$plan"; fi
[[ -f "$plan" ]] || { printf 'Plan does not exist: %s\n' "$plan" >&2; exit 66; }
plan_dir=$(cd "$(dirname "$plan")" && pwd -P)
plan="$plan_dir/$(basename "$plan")"

# A relative executable path is evaluated after cd'ing into the repository.
# Resolve it now so wrappers outside that repository work as expected.
if [[ "${cli[0]}" == */* ]]; then
  cli_dir=$(cd "$(dirname "${cli[0]}")" && pwd -P)
  cli[0]="$cli_dir/$(basename "${cli[0]}")"
fi

git -C "$repo" rev-parse --show-toplevel >/dev/null 2>&1 || {
  printf 'Not a Git repository: %s\n' "$repo" >&2; exit 69;
}
repo_root=$(git -C "$repo" rev-parse --show-toplevel)
[[ "$repo" == "$repo_root" ]] || {
  printf 'Use the linked worktree root, not a subdirectory: %s\n' "$repo_root" >&2; exit 64;
}
[[ -f "$repo/.git" ]] || {
  printf 'Refusing the primary checkout. Create a linked worktree with create-plan-worktree.sh.\n' >&2; exit 73;
}
worktree_branch=$(git -C "$repo" branch --show-current)
[[ -n "$worktree_branch" ]] || {
  printf 'Refusing a detached worktree; use a dedicated branch.\n' >&2; exit 73;
}

if [[ -z "$evidence_dir" ]]; then
  evidence_dir=$(mktemp -d "${TMPDIR:-/tmp}/plan-cli.XXXXXX")
else
  mkdir -p "$evidence_dir"
  evidence_dir=$(cd "$evidence_dir" && pwd -P)
fi

baseline="$evidence_dir/baseline.txt"
{
  printf 'timestamp=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'repo=%s\nbranch=%s\nplan=%s\ncli=' "$repo" "$worktree_branch" "$plan"
  printf '%q ' "${cli[@]}"; printf '\n'
  printf '\n[HEAD]\n'; git -C "$repo" rev-parse HEAD
  printf '\n[STATUS]\n'; git -C "$repo" status --short
  printf '\n[DIFF-STAT]\n'; git -C "$repo" diff --stat
} > "$baseline"

plan_in_repo=""
if [[ "$plan" == "$repo/"* ]]; then
  plan_in_repo=${plan#"$repo"/}
fi
unrelated_dirty=false
while IFS= read -r entry; do
  entry_path=${entry:3}
  [[ -n "$plan_in_repo" && "$entry_path" == "$plan_in_repo" ]] || unrelated_dirty=true
done < <(git -C "$repo" status --porcelain)
if "$unrelated_dirty"; then
  printf 'Refusing unrelated dirty worktree changes. Capture is in %s; use a clean worktree or get explicit direction.\n' "$baseline" >&2
  exit 73
fi

prompt="$evidence_dir/task.md"
cat > "$prompt" <<EOF
You are implementing exactly one approved plan in a local Git repository.

Repository: $repo
Plan (read it before editing): $plan

First inspect the plan and repository. Implement every plan step within scope. Do not commit, push, change credentials, access production, run destructive data operations, or make unrelated cleanup changes. If a step conflicts with the repository or cannot be completed, leave the code safe and record it as blocked rather than claiming completion.

Run the most relevant tests/build checks. Before exiting, print a report using this exact shape:

<plan-execution-report>
status: complete | partial | blocked
plan_steps:
  - step: <plan section or checklist item>
    status: implemented | deferred | blocked
    evidence: <files changed and test/behaviour evidence>
tests:
  - command: <exact command>
    result: pass | fail | not-run
deviations:
  - <none, or explanation>
</plan-execution-report>
EOF

printf 'Evidence directory: %s\n' "$evidence_dir"
if "$dry_run"; then
  printf 'Dry run: would invoke:'; printf ' %q' "${cli[@]}"; printf '\n'
  exit 0
fi

set +e
(cd "$repo" && "${cli[@]}" < "$prompt") 2>&1 | tee "$evidence_dir/execution.log"
cli_status=${PIPESTATUS[0]}
set -e
printf 'cli_exit_status=%s\n' "$cli_status" > "$evidence_dir/exit-status.txt"
awk '
  /<plan-execution-report>/ { capture=1 }
  capture { print }
  /<\/plan-execution-report>/ { capture=0; found=1 }
  END { exit(found ? 0 : 1) }
' "$evidence_dir/execution.log" > "$evidence_dir/report.md" ||
  printf 'No structured plan-execution-report was emitted.\n' > "$evidence_dir/report.md"
git -C "$repo" status --short > "$evidence_dir/status-after.txt"
git -C "$repo" diff --stat > "$evidence_dir/diff-stat-after.txt"
git -C "$repo" diff > "$evidence_dir/diff-after.patch"
exit "$cli_status"
