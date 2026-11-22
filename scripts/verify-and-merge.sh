#!/usr/bin/env bash
# Merge gate: approved + API tests + recorded e2e run (Swagger UI video) + CI green -> squash merge.
# Usage: ./scripts/verify-and-merge.sh T-001
source "$(dirname "$0")/_common.sh"
ID="${1:?ticket}"; KEY="${ID//-/}"          # T-001 -> T001 (pytest -k)
[[ "$(status_of "$ID")" == APPROVED* ]] || { echo "$ID is not APPROVED (status: $(status_of "$ID"))"; exit 1; }
PR=$(pr_of "$ID"); WT=$(worktree_of "$ID")
OUT="$EVIDENCE/$ID"; mkdir -p "$OUT"
RUN="uv run"; command -v uv >/dev/null || RUN=""

cd "$WT"
git fetch -q origin && git rebase -q "origin/$BASE_BRANCH" && git push -q --force-with-lease

echo "== lint =="
$RUN ruff check . 2>&1 | tee "$OUT/lint.log"

echo "== API tests =="
$RUN pytest tests -q 2>&1 | tee "$OUT/api-tests.log"

echo "== recorded feature run (Swagger UI via Playwright, video on) =="
$RUN pytest e2e -k "$KEY" -v --video on --output "$OUT/playwright" 2>&1 | tee "$OUT/e2e.log"
grep -qE "[1-9][0-9]* passed" "$OUT/e2e.log" || { echo "No e2e test for $KEY passed"; exit 1; }
VIDEO=$(find "$OUT/playwright" -name '*.webm' | head -1)
[[ -n "$VIDEO" ]] || { echo "No recording found"; exit 1; }
echo "Recording: $VIDEO"

echo "== CI checks =="
gh pr checks "$PR" --watch || { echo "CI failed"; exit 1; }

gh pr comment "$PR" --body "Verification passed for $ID
- Lint + API tests: passed
- E2E \`$KEY\` through Swagger UI: passed, video at \`.agents/evidence/$ID/\`
- CI: green"
gh pr merge "$PR" --squash --delete-branch
set_status "$ID" "MERGED"
git -C "$AGENTS_HOME" worktree remove --force "$WT" || true
echo "$ID merged."
