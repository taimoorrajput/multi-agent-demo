#!/usr/bin/env bash
# Usage: ./scripts/new-adr.sh "Title" <<'EOF' ...body... EOF
source "$(dirname "$0")/_common.sh"
TITLE="${1:?title required}"
DIR="$AGENTS_HOME/docs/adr"; mkdir -p "$DIR"
LAST=$(ls "$DIR" | grep -oE '^[0-9]{4}' | sort -n | tail -1 || true)
NUM=$(printf "%04d" $((10#${LAST:-0} + 1)))
SLUG=$(echo "$TITLE" | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')
FILE="$DIR/$NUM-$SLUG.md"
{ echo "# ADR-$NUM: $TITLE"; echo; cat; } > "$FILE"
git -C "$AGENTS_HOME" add "$FILE"
git -C "$AGENTS_HOME" commit -qm "docs(adr): ADR-$NUM $TITLE" -- "$FILE"
git -C "$AGENTS_HOME" push -q origin "$BASE_BRANCH" || true
echo "Created $FILE"
