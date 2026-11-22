#!/usr/bin/env bash
# Shared helpers. AGENTS_HOME = main checkout (not a worktree).
set -euo pipefail
AGENTS_HOME="${AGENTS_HOME:-$(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)}"
export AGENTS_HOME
TICKETS="$AGENTS_HOME/.agents/tickets"
STATUS="$AGENTS_HOME/.agents/status"
EVIDENCE="$AGENTS_HOME/.agents/evidence"
PROMPTS="$AGENTS_HOME/.agents/prompts"
SETTINGS="$AGENTS_HOME/.agents/settings"
WT_ROOT="${WT_ROOT:-$AGENTS_HOME/../$(basename "$AGENTS_HOME")-worktrees}"
BASE_BRANCH="${BASE_BRANCH:-main}"
mkdir -p "$TICKETS" "$STATUS" "$EVIDENCE"

status_of()   { cat "$STATUS/$1" 2>/dev/null || echo "TODO"; }
set_status()  { echo "$2" > "$STATUS/$1"; }
slug_of()     { sed -n '1s/^# *T-[0-9]*: *//p' "$TICKETS/$1.md" | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-40; }
branch_of()   { echo "feat/$1-$(slug_of "$1")"; }
worktree_of() { echo "$WT_ROOT/$1"; }
pr_of()       { gh pr list --head "$(branch_of "$1")" --state open --json number -q '.[0].number'; }
