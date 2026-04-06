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
def ask(model, prompt, timeout=120):
    started = time.time()
    try:
        out = subprocess.check_output(
            ["ollama", "run", model, prompt],
            text=True,
            timeout=timeout
        ).strip()
        duration = time.time() - started
        return out, duration, None
    except Exception as e:
        duration = time.time() - started
        return "", duration, f"{model} unavailable ({e})"

def log_phase(step_id, phase_name, model, prompt):
    log(f"[step {step_id}] phase={phase_name} model={model}")
    log(f"[step {step_id}] prompt:\n{prompt}")

def log_phase_result(step_id, phase_name, model, output, duration, error):
    if error:
        log(f"[step {step_id}] phase={phase_name} model={model} error={error} ({duration:.2f}s)")
        return
    log(f"[step {step_id}] phase={phase_name} model={model} duration={duration:.2f}s")
    log(f"[step {step_id}] output:\n{output}")

def prompt_for(phase, step):
    command_payload = json.dumps(step, indent=2)
    prompts = {
        "interpretation": "Explain the intent of this command:\n",
        "safety": "Assess the safety risks of executing this command on a Linux system:\n",
        "explanation": "Explain this command clearly to a system operator:\n",
        "uncensored_review": (
            "Be brutally honest about risks, abuse potential, and worst-case outcomes of "
            "this command. Do not hold back:\n"
        ),
        "alternate_view": "Provide an alternate perspective, edge cases, or hidden consequences:\n",
    }
    return prompts[phase] + command_payload

POPPOOB_MODELS = [
    "PopPooB-D:latest",
    "PopPooB-G:latest",
    "PopPooB-Pin-Yin:latest",
    "PopPooB:latest",
]
UNCENSORED_MODEL = "PopPooB-Uncensored:latest"
DEFAULT_TIMEOUT = 120

# ---------------- Per-step debate ----------------
step_debates = []

for step in steps:
    log(f"=== DEBATING STEP: {step['id']} ===")

    phases = [
        ("interpretation", POPPOOB_MODELS[0]),
        ("safety", POPPOOB_MODELS[1]),
        ("explanation", POPPOOB_MODELS[2]),
        ("alternate_view", POPPOOB_MODELS[3]),
        ("uncensored_review", UNCENSORED_MODEL),
    ]

    phase_outputs = []
    phase_text = {}
    for phase_name, model in phases:
        prompt = prompt_for(phase_name, step)
        log_phase(step["id"], phase_name, model, prompt)
        output, duration, error = ask(model, prompt, timeout=DEFAULT_TIMEOUT)
        log_phase_result(step["id"], phase_name, model, output, duration, error)
        if error:
            output = error
        phase_outputs.append({
            "phase": phase_name,
            "model": model,
            "prompt": prompt,
            "output": output,
            "duration_s": round(duration, 2),
            "error": error,
        })
        phase_text[phase_name] = output

    # Agreement heuristic
    agreement = 0.7
    risk = "medium"

    s = phase_text.get("safety", "").lower()
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
        "phases": phase_outputs
    })

    log(
        f"[step {step['id']}] result risk={risk} agreement={agreement} "
        f"command={step['command']}"
    )

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
