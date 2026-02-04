#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys
import datetime

HOME = pathlib.Path.home()
AUTON = HOME / ".autonomy"
PROP = AUTON / "proposal.json"
LOG = AUTON / "planner.log"

DEFAULT_CONFIDENCE = 0.4


def log(msg: str) -> None:
    AUTON.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.datetime.now().isoformat()}] {msg}"
    with LOG.open("a") as f:
        f.write(line + "\n")


def read_task(args) -> str:
    if args.task:
        return " ".join(args.task).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def build_proposal(task: str) -> dict:
    return {
        "task": task,
        "confidence": DEFAULT_CONFIDENCE,
        "steps": [
            {
                "id": "step-1",
                "description": task,
                "command": f"echo {json.dumps(task)}",
                "risk": "low",
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a basic proposal.json")
    parser.add_argument("task", nargs="*", help="Task to plan")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout output")
    args = parser.parse_args()

    task = read_task(args)
    if not task:
        if not args.quiet:
            print("NO_ACTION")
        log("No task provided; NO_ACTION")
        return 0

    proposal = build_proposal(task)
    AUTON.mkdir(parents=True, exist_ok=True)
    PROP.write_text(json.dumps(proposal, indent=2))
    log(f"Wrote proposal.json with {len(proposal['steps'])} step(s)")

    if not args.quiet:
        print(json.dumps(proposal, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
