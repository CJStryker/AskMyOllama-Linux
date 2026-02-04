#!/usr/bin/env bash
H="$HOME/.autonomy/health.json"

if [ ! -f "$H" ]; then
  echo "unknown"
  exit 0
fi

FAILS=$(jq -r '.failures // 0' "$H")

if [ "$FAILS" -eq 0 ]; then
  echo "green"
elif [ "$FAILS" -le 3 ]; then
  echo "yellow"
else
  echo "red"
fi
