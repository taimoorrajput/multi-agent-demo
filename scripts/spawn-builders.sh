#!/usr/bin/env bash
# One git worktree + branch + tmux pane per TODO ticket. Run inside tmux.
# BUILDER_MODE=auto -> --dangerously-skip-permissions (sandbox only!)
source "$(dirname "$0")/_common.sh"
MAX="${MAX_BUILDERS:-6}"
SESSION="$(tmux display-message -p '#S' 2>/dev/null || echo agents)"
tmux has-session -t "$SESSION" 2>/dev/null || tmux new-session -d -s "$SESSION"
WIN="builders"
git -C "$AGENTS_HOME" fetch -q origin "$BASE_BRANCH"
mkdir -p "$WT_ROOT"

PERM="--permission-mode acceptEdits"
[[ "${BUILDER_MODE:-}" == "auto" ]] && PERM="--dangerously-skip-permissions"

n=0
for f in "$TICKETS"/T-*.md; do
  id=$(basename "$f" .md)
  [[ "$(status_of "$id")" == "TODO" ]] || continue
  (( n < MAX )) || break
  wt=$(worktree_of "$id"); br=$(branch_of "$id")
  [[ -d "$wt" ]] || git -C "$AGENTS_HOME" worktree add -q -b "$br" "$wt" "origin/$BASE_BRANCH"
  set_status "$id" "IN_PROGRESS"
  cmd="cd '$wt' && export AGENTS_HOME='$AGENTS_HOME' TICKET='$id' && (uv sync -q 2>/dev/null || (python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt -r requirements-dev.txt) || true) && \
claude --settings '$SETTINGS/builder.json' $PERM \
  --append-system-prompt \"\$(cat '$PROMPTS/builder.md')\" \
  'You are the builder for $id. Read \$AGENTS_HOME/.agents/tickets/$id.md and complete it end to end.'"
  if (( n == 0 )) && ! tmux list-windows -t "$SESSION" -F '#W' | grep -qx "$WIN"; then
    tmux new-window -t "$SESSION" -n "$WIN" "bash -lc \"$cmd\"; bash"
  else
    tmux split-window -t "$SESSION:$WIN" "bash -lc \"$cmd\"; bash"
    tmux select-layout -t "$SESSION:$WIN" tiled
  fi
  tmux select-pane -t "$SESSION:$WIN" -T "$id"
  echo "Spawned builder for $id on $br ($wt)"
  n=$((n+1))
done
tmux set -t "$SESSION:$WIN" pane-border-status top 2>/dev/null || true
echo "$n builder(s) running in tmux window '$SESSION:$WIN'"
