#!/usr/bin/env bash
# Usage: ./scripts/new-ticket.sh T-001 "Title" <<'EOF' ...body... EOF
source "$(dirname "$0")/_common.sh"
ID="${1:?ticket id required, e.g. T-001}"; TITLE="${2:?title required}"
FILE="$TICKETS/$ID.md"
{ echo "# $ID: $TITLE"; echo; cat; } > "$FILE"
set_status "$ID" "TODO"
echo "Created $FILE"
