#!/usr/bin/env bash
set -euo pipefail

# ---------------- Configuration ----------------
MODEL_DEFAULT="PopPooB-D:latest"
API_DEFAULT="http://96.242.172.92:11434/api/generate"
LOG_DEFAULT="$HOME/.autonomy/ask-operator.log"

MODEL="${ASK_OPERATOR_MODEL:-$MODEL_DEFAULT}"
API="${ASK_OPERATOR_API:-$API_DEFAULT}"
LOG="${ASK_OPERATOR_LOG:-$LOG_DEFAULT}"
AUTO_APPROVE="false"
MAX_STEPS=0

mkdir -p "$HOME/.autonomy"

print_help() {
  cat <<'USAGE'
Usage:
  ask-operator.sh [options] [task]

Options:
  --model <name>      Override model
  --api <url>         Override API endpoint
  --log <path>        Override log path
  --auto-approve      Automatically approve proposed steps
  --max-steps <n>     Stop after n steps (0 = unlimited)
  -h | --help         Show this help
USAGE
}

print_models() {
  cat <<'MODELS'
Available models:
  PopPooB-D:latest
  PopPooB-G:latest
  PopPooB-Uncensored:latest
  PopPooB-Pin-Yin:latest
MODELS
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing dependency: $1" >&2
    exit 1
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="${2:-}"; shift ;;
    --api) API="${2:-}"; shift ;;
    --log) LOG="${2:-}"; shift ;;
    --auto-approve) AUTO_APPROVE="true" ;;
    --max-steps) MAX_STEPS="${2:-}"; shift ;;
    -h|--help) print_help; print_models; exit 0 ;;
    *) TASK="${TASK:-} $1" ;;
  esac
  shift
done

TASK="${TASK:-}"
TASK="${TASK# }"

log() {
  echo "[ASK-OPERATOR] $1"
  echo "[$(date -Is)] $1" >> "$LOG"
}

# ---------------- Get task ----------------
if [ -z "${TASK:-}" ] && ! tty -s; then
  TASK="$(cat)"
fi

if [ -z "${TASK:-}" ]; then
  read -p "Operator task: " TASK
fi

if [ -z "$TASK" ]; then
  echo "No task provided. Exiting."
  exit 1
fi

require_cmd jq
require_cmd curl

log "TASK: $TASK"

# ---------------- System context ----------------
CONTEXT="You are a cautious Linux system operator.

RULES (MANDATORY):
- Propose EXACTLY ONE shell command per step
- No explanations, no markdown, no backticks
- If sudo is required, prefix the command with [SUDO]
- Never propose destructive commands (rm -rf, mkfs, dd, wipefs, shutdown, reboot)
- Wait for command output before continuing
- If the task is complete, respond with exactly: DONE
"

LAST_OUTPUT="(none yet)"
STEP_COUNT=0

# ---------------- Main loop ----------------
while true; do
  PROMPT=$(jq -Rn --arg p "
$CONTEXT

Task:
$TASK

Previous command output:
$LAST_OUTPUT

Next step (ONE command only or DONE):" '$p')

  RAW=$(curl -s "$API" -d "{
    \"model\": \"$MODEL\",
    \"stream\": false,
    \"prompt\": $PROMPT
  }")

  STEP=$(echo "$RAW" | jq -r '.response // empty' | head -n 1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  if [ -z "$STEP" ]; then
    echo "❌ Model returned no usable response."
    LAST_OUTPUT="Model returned empty response."
    continue
  fi

  echo
  echo "🤖 Proposed step:"
  echo "  $STEP"
  log "PROPOSED: $STEP"

  if [[ "$STEP" == "DONE" ]]; then
    echo "✅ Task completed."
    log "TASK COMPLETED"
    break
  fi

  if [ "$AUTO_APPROVE" = "true" ]; then
    A="y"
  else
    read -p "Approve this step? [y/n/q] " A
  fi
  case "$A" in
    y|Y)
      ;;
    q|Q)
      echo "Quit."
      log "USER QUIT"
      exit 0
      ;;
    *)
      LAST_OUTPUT="User declined the proposed command: $STEP"
      log "DECLINED: $STEP"
      continue
      ;;
  esac

  # ---------------- Command execution ----------------
  if [[ "$STEP" == "[SUDO]"* ]]; then
    CMD="sudo ${STEP#\[SUDO\] }"
  else
    CMD="$STEP"
  fi

  echo "▶ Running: $CMD"
  log "EXECUTING: $CMD"

  OUTPUT=$(bash -c "$CMD" 2>&1 || true)

  echo "$OUTPUT"
  log "OUTPUT: $OUTPUT"

  LAST_OUTPUT="$OUTPUT"

  if [ "$MAX_STEPS" -gt 0 ]; then
    STEP_COUNT=$((STEP_COUNT + 1))
    if [ "$STEP_COUNT" -ge "$MAX_STEPS" ]; then
      echo "⚠️ Reached max steps ($MAX_STEPS)."
      log "MAX STEPS REACHED"
      break
    fi
  fi
done
