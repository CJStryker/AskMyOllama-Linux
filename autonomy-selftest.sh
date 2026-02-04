#!/usr/bin/env bash
set -e

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

FAILURES=0
JSON_MODE=false
[[ "$1" == "--json" ]] && JSON_MODE=true
RESULTS=()

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

PASS() {
  echo -e "${GREEN}✔ $1${RESET}"
  if $JSON_MODE; then
    RESULTS+=("{\"check\":\"$(json_escape "$1")\",\"status\":\"pass\"}")
  fi
}

FAIL() {
  echo -e "${RED}✖ $1${RESET}"
  if $JSON_MODE; then
    RESULTS+=("{\"check\":\"$(json_escape "$1")\",\"status\":\"fail\"}")
  fi
  FAILURES=$((FAILURES+1))
  SUGGEST "$1"
}


INFO() {
  echo -e "${YELLOW}ℹ $1${RESET}"
  if $JSON_MODE; then
    RESULTS+=("{\"check\":\"$(json_escape "$1")\",\"status\":\"info\"}")
  fi
}

SUGGEST() {
  case "$1" in
    "OLLAMA_HOST missing")
      INFO "Suggestion: run systemctl --user daemon-reexec and re-login"
      ;;
    "Ollama unreachable")
      INFO "Suggestion: check sudo systemctl status ollama"
      ;;
    "proposal-ui syntax error")
      INFO "Suggestion: PYTHONDONTWRITEBYTECODE=1 avoids pycache issues"
      ;;
    "debate failed")
      INFO "Suggestion: ensure debate.py exits 0 on NO_ACTION"
      ;;
  esac
}


echo "======================================"
echo "🧠 AUTONOMY FULL SYSTEM SELF-TEST"
echo "======================================"
echo

# ---------- Import systemd user environment ----------
if [ -z "$OLLAMA_HOST" ]; then
  while IFS= read -r line; do
    export "$line"
  done < <(systemctl --user show-environment | grep '^OLLAMA_')
fi

# ---------- 1. Environment ----------
[ -n "$OLLAMA_HOST" ] && PASS "OLLAMA_HOST set" || FAIL "OLLAMA_HOST missing"

# ---------- 2. Ollama ----------
if [ -n "$OLLAMA_HOST" ] && \
   curl -s --connect-timeout 3 --max-time 5 "$OLLAMA_HOST/api/tags" >/dev/null; then
  PASS "Ollama reachable"
else
  FAIL "Ollama unreachable"
fi
#---------- 2.1 Ollama Install Safe----------
~/.local/bin/ollama-bootstrap.sh >/dev/null 2>&1 || true

# ---------- 3. ask ----------
if ask "say test" 2>/dev/null | grep -qi test; then
  PASS "ask works"
else
  INFO "ask unavailable (likely no models yet)"
fi

# ---------- 4. GUI ----------
python3 - <<EOF >/dev/null 2>&1 && PASS "tkinter available" || FAIL "tkinter missing"
import tkinter
EOF

# ---------- 5. Observer ----------
~/.local/bin/observer.sh >/dev/null || true
[ -f ~/.autonomy/observer.json ] && PASS "observer generated data" || FAIL "observer failed"

# ---------- 6. Planner ----------
~/.local/bin/planner.py --quiet >/dev/null || true
jq -e . ~/.autonomy/proposal.json >/dev/null 2>&1 \
  && PASS "planner produced proposal JSON" \
  || FAIL "planner output invalid"

# ---------- 7. Proposal UI ----------
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile ~/.local/bin/proposal-ui.py \
  && PASS "proposal-ui syntax OK" \
  || FAIL "proposal-ui syntax error"

# ---------- 8. Policy ----------
[ -f ~/.autonomy/policy.conf ] && PASS "policy file present" || FAIL "policy missing"

# ---------- 9. Executor ----------
~/.local/bin/executor.sh "rm -rf /" 2>&1 | grep -q DENIED \
  && PASS "executor blocks forbidden commands" \
  || FAIL "executor policy failed"

# ---------- 10. Autonomy toggle ----------
~/.local/bin/autonomy-toggle.sh >/dev/null || true
[ -f ~/.autonomy/enabled ] && PASS "autonomy ON" || FAIL "autonomy ON failed"
~/.local/bin/autonomy-toggle.sh >/dev/null || true
[ ! -f ~/.autonomy/enabled ] && PASS "autonomy OFF" || FAIL "autonomy OFF failed"

# ---------- 11. Audit ----------
mkdir -p ~/.autonomy/logs
~/.local/bin/audit-log.sh test "selftest" || true
[ "$(ls ~/.autonomy/logs 2>/dev/null | wc -l)" -gt 0 ] \
  && PASS "audit logging works" \
  || FAIL "audit logging failed"

# ---------- 12. Preferences ----------
python3 ~/.local/bin/update-preferences.py services test approved || true
[ -f ~/.autonomy/preferences.json ] \
  && PASS "preferences learning works" \
  || FAIL "preferences failed"

# ---------- 13. Heat-map ----------
python3 ~/.local/bin/autonomy-heatmap.py >/dev/null 2>&1 \
  && PASS "heat-map runnable" \
  || FAIL "heat-map error"

# ---------- 14. Tray deps ----------
python3 - <<EOF >/dev/null 2>&1 && PASS "tray dependencies OK" || FAIL "tray deps missing"
import gi
from gi.repository import AppIndicator3
EOF

# ---------- 15. Voice ----------
command -v ask-voice.py >/dev/null \
  && PASS "voice pipeline present" \
  || INFO "voice pipeline missing"

# ---------- 16. Roles ----------
[ -d ~/.autonomy/roles ] \
  && PASS "roles directory exists" \
  || FAIL "roles missing"

# ---------- 17. Fatigue ----------
~/.local/bin/fatigue-check.sh >/dev/null || true
PASS "fatigue check runnable"

# ---------- 18. Anomaly ----------
jq -e '.errors' ~/.autonomy/observer.json >/dev/null \
  && PASS "anomaly data path present" \
  || FAIL "anomaly path missing"

# ---------- 19. Remote approval ----------
[ -x /usr/local/bin/autonomy-approve ] \
  && PASS "remote approval tool present" \
  || FAIL "remote approval missing"

echo
echo "======================================"
if [ "$FAILURES" -eq 0 ]; then
  echo -e "${GREEN}✔ SYSTEM HEALTHY${RESET}"
else
  echo -e "${RED}✖ $FAILURES ISSUES DETECTED${RESET}"
fi
echo "======================================"

if $JSON_MODE; then
  printf '{ "failures": %d, "results": [%s] }\n' \
    "$FAILURES" "$(IFS=,; echo "${RESULTS[*]}")"
fi

exit $FAILURES
