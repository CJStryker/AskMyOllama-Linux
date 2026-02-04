#!/usr/bin/env bash
set -e
OUT="$HOME/.autonomy/observer.json"
mkdir -p "$(dirname "$OUT")"

errors=$(journalctl -p err -n 20 --no-pager 2>/dev/null || true)
services=$(systemctl --failed --no-pager 2>/dev/null || true)
disk=$(df -h / | tail -1)
mem=$(free -h | sed -n '2p')

jq -n \
  --arg errors "$errors" \
  --arg services "$services" \
  --arg disk "$disk" \
  --arg mem "$mem" \
  '{errors:$errors, failed_services:$services, disk:$disk, mem:$mem}' \
  > "$OUT"
