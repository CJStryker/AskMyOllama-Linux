#!/usr/bin/env bash
set -e
while true; do
  ~/.local/bin/planner.py | grep -vq NO_ACTION && ~/.local/bin/proposal-ui.py
  sleep 300
done
