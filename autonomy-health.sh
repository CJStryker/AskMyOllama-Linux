#!/usr/bin/env bash
./autonomy-selftest.sh >/tmp/autonomy-health.log 2>&1
if [ $? -eq 0 ]; then
  notify-send "🧠 Autonomy" "All systems healthy ✅"
else
  notify-send "🧠 Autonomy" "Issues detected ❌"
fi
