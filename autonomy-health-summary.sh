#!/usr/bin/env bash
H="$HOME/.autonomy/health.json"

if [ ! -f "$H" ]; then
  echo "No health data yet"
  exit 0
fi

FAILS=$(jq -r '.failures // "?"' "$H")
TIME=$(stat -c %y "$H" | cut -d'.' -f1)

if [ "$FAILS" = "0" ]; then
  STATUS="HEALTHY"
else
  STATUS="ISSUES ($FAILS)"
fi

echo "Autonomy: $STATUS | Last check: $TIME"
