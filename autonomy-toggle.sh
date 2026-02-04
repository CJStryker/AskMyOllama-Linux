#!/usr/bin/env bash

STATE="$HOME/.autonomy/enabled"

if [ -f "$STATE" ]; then
  rm -f "$STATE"
  systemctl --user stop autonomy.service
  notify-send "Autonomy" "OFF"
else
  touch "$STATE"
  systemctl --user start autonomy.service
  notify-send "Autonomy" "ON"
fi
