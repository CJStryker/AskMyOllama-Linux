#!/usr/bin/env bash
set -e

POLICY="$HOME/.autonomy/policy.conf"
CMD="$*"

# Read policy safely
DENY_PATTERNS=()
ALLOW_PREFIXES=()

while IFS='=' read -r key value; do
  case "$key" in
    DENY)  DENY_PATTERNS+=("$value") ;;
    ALLOW) ALLOW_PREFIXES+=("$value") ;;
  esac
done < <(grep -E '^(DENY|ALLOW)=' "$POLICY")

# Enforce deny rules
for pat in "${DENY_PATTERNS[@]}"; do
  if echo "$CMD" | grep -Fq "$pat"; then
    echo "❌ DENIED by policy: $pat"
    exit 1
  fi
done

# Enforce allow rules
ALLOWED=false
for pre in "${ALLOW_PREFIXES[@]}"; do
  if [[ "$CMD" == "$pre"* ]]; then
    ALLOWED=true
    break
  fi
done

if [ "$ALLOWED" != true ]; then
  echo "❌ Command not in allowlist"
  exit 1
fi

echo "✅ Policy check passed"
bash -c "$CMD"
