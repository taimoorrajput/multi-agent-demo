#!/usr/bin/env bash
# Launch the SUPERVISOR: Edit/Write tools denied, so it physically cannot write code.
source "$(dirname "$0")/_common.sh"
cd "$AGENTS_HOME"
exec claude \
  --settings "$SETTINGS/supervisor.json" \
  --append-system-prompt "$(cat "$PROMPTS/supervisor.md")" \
  "$@"
