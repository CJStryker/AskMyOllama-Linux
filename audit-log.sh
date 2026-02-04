#!/usr/bin/env bash
LOG="$HOME/.autonomy/logs/$(date +%F_%H-%M-%S).json"
mkdir -p "$(dirname "$LOG")"

jq -n \
  --arg time "$(date)" \
  --arg action "$1" \
  --arg content "$2" \
  '{time:$time, action:$action, content:$content}' \
  > "$LOG"
