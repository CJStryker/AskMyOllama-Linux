#!/usr/bin/env bash
ls -1 ~/.autonomy/logs
read -p "Replay which log? " FILE
cat ~/.autonomy/logs/"$FILE" | jq
