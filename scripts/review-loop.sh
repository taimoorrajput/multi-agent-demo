#!/usr/bin/env bash
# Reviewer <-> builder fix loop, MAX 3 rounds, then escalate.
# Usage: ./scripts/review-loop.sh T-001
source "$(dirname "$0")/_common.sh"
ID="${1:?ticket}"; MAX_ROUNDS=3
PR=$(pr_of "$ID"); [[ -n "$PR" ]] || { echo "No open PR for $ID"; exit 1; }
WT=$(worktree_of "$ID")
LOG="$EVIDENCE/$ID"; mkdir -p "$LOG"

for round in $(seq 1 $MAX_ROUNDS); do
  echo "=== $ID PR #$PR - review round $round/$MAX_ROUNDS ==="
  out=$(cd "$AGENTS_HOME" && claude -p \
    --settings "$SETTINGS/reviewer.json" \
    --append-system-prompt "$(cat "$PROMPTS/reviewer.md")" \
    "Review PR #$PR for ticket $ID (round $round of $MAX_ROUNDS). Ticket: $(cat "$TICKETS/$ID.md")" \
    | tee "$LOG/review-round-$round.md")
  verdict=$(echo "$out" | grep -oE 'VERDICT: (APPROVE|CHANGES)' | tail -1 || true)

  if [[ "$verdict" == "VERDICT: APPROVE" ]]; then
    set_status "$ID" "APPROVED (round $round)"; echo "Approved in round $round"; exit 0
  fi

  set_status "$ID" "CHANGES_REQUESTED (round $round)"
  if (( round == MAX_ROUNDS )); then break; fi

  echo "--- builder fixing round $round comments ---"
  comments=$(gh pr view "$PR" --comments --json reviews,comments \
             -q '[.reviews[].body, .comments[].body] | map(select(. != "")) | .[-3:] | join("\n---\n")')
  (cd "$WT" && AGENTS_HOME="$AGENTS_HOME" TICKET="$ID" claude -p \
    --settings "$SETTINGS/builder.json" --permission-mode acceptEdits \
    --append-system-prompt "$(cat "$PROMPTS/builder.md")" \
    "Address these review comments on PR #$PR for $ID, rerun tests, commit and push:
$comments" | tee "$LOG/fix-round-$round.md")
done

set_status "$ID" "ESCALATED after $MAX_ROUNDS rounds"
gh pr comment "$PR" --body "Escalated to supervisor: not approved after $MAX_ROUNDS review rounds."
echo "ESCALATED: supervisor must re-scope $ID"; exit 2
