#!/usr/bin/env bash
# Print known local coding CLIs that are currently available on PATH.
set -euo pipefail

found=false
for candidate in reasonix claude codex aider gemini opencode goose amp pi qwen copilot cursor-agent; do
  path=$(command -v "$candidate" 2>/dev/null || true)
  if [[ -n "$path" ]]; then
    printf '%s\t%s\n' "$candidate" "$path"
    found=true
  fi
done

if ! "$found"; then
  printf '%s\n' 'No known coding CLI found on PATH. The user may provide an executable path.'
fi
