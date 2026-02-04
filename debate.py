#!/usr/bin/env python3
import json
import subprocess
import pathlib
import sys
import time
import datetime

# ---------------- Paths ----------------
HOME = pathlib.Path.home()
AUTON = HOME / ".autonomy"
PROP  = AUTON / "proposal.json"
OUT   = AUTON / "debate.json"
HIST  = AUTON / "debate-history.jsonl"
LOG   = AUTON / "debate.log"

AUTON.mkdir(parents=True, exist_ok=True)

# ---------------- Logging ----------------
def log(msg):
    line = f"[{datetime.datetime.now().isoformat()}] {msg}"
    print(line)
    with LOG.open("a") as f:
        f.write(line + "\n")

# ---------------- Load proposal ----------------
if not PROP.exists():
    log("No proposal found — skipping debate.")
    sys.exit(0)

try:
    proposal = json.loads(PROP.read_text())
except Exception as e:
    log(f"Failed to parse proposal.json: {e}")
    sys.exit(0)

steps = proposal.get("steps", [])
if not steps:
    log("Proposal has no steps — skipping debate.")
    sys.exit(0)

# ---------------- Ollama helper ----------------
def ask(model, prompt):
    try:
        out = subprocess.check_output(
            ["ollama", "run", model, prompt],
            text=True,
            timeout=90
        ).strip()
        return out
    except Exception as e:
        return f"{model} unavailable ({e})"

# ---------------- Per-step debate ----------------
step_debates = []

for step in steps:
    log(f"=== DEBATING STEP: {step['id']} ===")

    # Phase 1: Interpret
    interpret = ask(
        "deepseek-r1:8b",
        "Explain the intent of this command:\n"
        + json.dumps(step, indent=2)
    )

    # Phase 2: Safety
    safety = ask(
        "qwen2.5:3b",
        "Assess the safety risks of executing this command on a Linux system:\n"
        + json.dumps(step, indent=2)
    )

    # Phase 3: Explanation
    explanation = ask(
        "gemma3:4b",
        "Explain this command clearly to a system operator:\n"
        + json.dumps(step, indent=2)
    )

    # Agreement heuristic
    agreement = 0.7
    risk = "medium"

    s = safety.lower()
    if any(x in s for x in ["danger", "high risk", "data loss", "irreversible"]):
        agreement = 0.3
        risk = "high"
    elif any(x in s for x in ["safe", "low risk", "non-destructive"]):
        agreement = 0.85
        risk = "low"

    step_debates.append({
        "step_id": step["id"],
        "command": step["command"],
        "summary": {
            "risk_level": risk,
            "agreement": agreement
        },
        "phases": [
            {
                "phase": "interpretation",
                "model": "deepseek-r1:8b",
                "output": interpret
            },
            {
                "phase": "safety",
                "model": "qwen2.5:3b",
                "output": safety
            },
            {
                "phase": "explanation",
                "model": "gemma3:4b",
                "output": explanation
            }
        ]
    })

# ---------------- Final debate object ----------------
timestamp = int(time.time())
debate = {
    "task": proposal.get("task"),
    "timestamp": timestamp,
    "time": datetime.datetime.fromtimestamp(timestamp).isoformat(),
    "steps": step_debates
}

# ---------------- Persist ----------------
OUT.write_text(json.dumps(debate, indent=2))
with HIST.open("a") as f:
    f.write(json.dumps(debate) + "\n")

log("Per-step debate completed.")
sys.exit(0)
