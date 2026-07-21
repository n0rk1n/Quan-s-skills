#!/usr/bin/env bash
# Create a dedicated, branch-backed worktree for one local CLI plan run.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: create-plan-worktree.sh --repo REPO --base BASE --branch BRANCH --worktree PATH

Creates a new branch and linked worktree. It never reuses an existing path or branch.
EOF
}

repo=""
base=""
branch=""
worktree=""

while (($#)); do
  case "$1" in
    --repo) repo=${2:?"--repo needs a path"}; shift 2 ;;
    --base) base=${2:?"--base needs a ref"}; shift 2 ;;
    --branch) branch=${2:?"--branch needs a name"}; shift 2 ;;
    --worktree) worktree=${2:?"--worktree needs a path"}; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 64 ;;
  esac
done

[[ -n "$repo" && -n "$base" && -n "$branch" && -n "$worktree" ]] || {
  printf '%s\n' 'All options are required.' >&2; usage >&2; exit 64;
}
[[ -d "$repo" ]] || { printf 'Repository does not exist: %s\n' "$repo" >&2; exit 66; }
repo=$(cd "$repo" && pwd -P)
if [[ "$worktree" != /* ]]; then worktree="$PWD/$worktree"; fi
worktree_parent=$(dirname "$worktree")
[[ -d "$worktree_parent" ]] || { printf 'Worktree parent does not exist: %s\n' "$worktree_parent" >&2; exit 66; }
repo_root=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) || {
  printf 'Not a Git repository: %s\n' "$repo" >&2; exit 69;
}
[[ "$repo" == "$repo_root" ]] || { printf 'Use the repository root, not a subdirectory.\n' >&2; exit 64; }
git -C "$repo" rev-parse --verify --quiet "$base^{commit}" >/dev/null || {
  printf 'Base ref is not a commit: %s\n' "$base" >&2; exit 65;
}
git -C "$repo" check-ref-format --branch "$branch" >/dev/null || {
  printf 'Invalid branch name: %s\n' "$branch" >&2; exit 65;
}
git -C "$repo" show-ref --verify --quiet "refs/heads/$branch" && {
  printf 'Branch already exists: %s\n' "$branch" >&2; exit 73;
}
[[ ! -e "$worktree" ]] || { printf 'Worktree path already exists: %s\n' "$worktree" >&2; exit 73; }

git -C "$repo" worktree add -b "$branch" "$worktree" "$base"
worktree=$(cd "$worktree" && pwd -P)
printf 'worktree=%s\nbranch=%s\nbase_commit=%s\n' \
  "$worktree" "$branch" "$(git -C "$worktree" rev-parse HEAD)"
