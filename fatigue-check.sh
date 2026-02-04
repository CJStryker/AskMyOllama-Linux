#!/usr/bin/env bash
LOGS=$(ls ~/.autonomy/logs 2>/dev/null | wc -l)
if [ "$LOGS" -gt 20 ]; then
  rm -f ~/.autonomy/enabled
  systemctl --user stop autonomy.service
  notify-send "Autonomy paused" "Fatigue detected"
fi
