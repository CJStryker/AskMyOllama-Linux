#!/usr/bin/env bash
set -euo pipefail

LANG_MODE="en"
TASK=""

usage() {
  cat <<'USAGE'
Usage:
  ask-operator-simulate.sh [options] [task]

Options:
  --en | --zh         Response language (default: en)
  -h | --help         Show this help
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --en) LANG_MODE="en" ;;
    --zh) LANG_MODE="zh" ;;
    -h|--help) usage; exit 0 ;;
    *) TASK="$TASK $1" ;;
  esac
  shift
 done

TASK="${TASK# }"
if [ -z "$TASK" ] && ! tty -s; then
  TASK="$(cat)"
fi
if [ -z "$TASK" ]; then
  read -p "Simulate task: " TASK
fi
[ -n "$TASK" ] || { echo "No task provided. Exiting." >&2; exit 1; }

PROMPT="Simulate the following Linux task.
Do NOT give commands.
Explain what would likely happen step by step."

ask --"$LANG_MODE" --task "$PROMPT" "$TASK"
