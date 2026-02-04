#!/usr/bin/env bash
set -e

# ---------------- Configuration ----------------
MODEL="gpt-oss:120b-cloud"
API="http://69.142.141.135:11434/api/generate"
LOG="$HOME/.autonomy/ask-operator.log"

mkdir -p "$HOME/.autonomy"

log() {
  echo "[ASK-OPERATOR] $1"
  echo "[$(date -Is)] $1" >> "$LOG"
}

# ---------------- Get task ----------------
if [ "$#" -gt 0 ]; then
  TASK="$*"
else
  read -p "Operator task: " TASK
fi

if [ -z "$TASK" ]; then
  echo "No task provided. Exiting."
  exit 1
fi

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

  read -p "Approve this step? [y/n/q] " A
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
done
