#!/usr/bin/env bash
OUT="$HOME/.autonomy/health.json"
LOG="$HOME/.autonomy/logs/nightly-$(date +%F).log"

mkdir -p "$HOME/.autonomy/logs"

./autonomy-selftest.sh --json > "$OUT" 2> "$LOG"
RC=$?

if [ "$RC" -eq 0 ]; then
  notify-send "🧠 Autonomy Nightly Check" "System healthy ✅"
else
  notify-send "🧠 Autonomy Nightly Check" "Issues detected ❌ ($RC failures)"
fi

exit 0
