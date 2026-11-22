#!/usr/bin/env bash
# Supervisor answers a BLOCKED builder by typing into its tmux pane.
# Usage: ./scripts/unblock.sh T-003 "answer"
source "$(dirname "$0")/_common.sh"
ID="${1:?ticket}"; ANSWER="${2:?answer}"
SESSION="$(tmux display-message -p '#S' 2>/dev/null || echo agents)"
PANE=$(tmux list-panes -t "$SESSION:builders" -F '#{pane_id} #{pane_title}' | awk -v id="$ID" '$2==id{print $1}')
[[ -n "$PANE" ]] || { echo "No pane for $ID"; exit 1; }
printf '\n## Supervisor answer (%s)\n%s\n' "$(date -Iseconds)" "$ANSWER" >> "$TICKETS/$ID.md"
tmux send-keys -t "$PANE" "SUPERVISOR: $ANSWER  -- continue the ticket and set status back to IN_PROGRESS." Enter
set_status "$ID" "IN_PROGRESS"
echo "Unblocked $ID"
