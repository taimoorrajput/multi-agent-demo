#!/usr/bin/env bash
# Status board for all tickets.
source "$(dirname "$0")/_common.sh"
printf "%-8s %-40s %s\n" TICKET TITLE STATUS
printf "%-8s %-40s %s\n" ------ ----- ------
for f in "$TICKETS"/T-*.md; do
  [[ -e "$f" ]] || { echo "(no tickets yet)"; exit 0; }
  id=$(basename "$f" .md)
  title=$(sed -n '1s/^# *T-[0-9]*: *//p' "$f" | cut -c1-40)
  printf "%-8s %-40s %s\n" "$id" "$title" "$(status_of "$id")"
done
