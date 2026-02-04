#!/usr/bin/env python3
import pathlib
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

BASE_DIR = pathlib.Path(__file__).resolve().parent

COMMANDS = [
    ("Ask (Floating)", ["ask-float.py"]),
    ("Ask Clipboard", ["ask-clip"]),
    ("Ask Selection", ["ask-select"]),
    ("Ask OCR", ["ask-ocr"]),
    ("Ask Errors", ["ask-error"]),
    ("Ask Voice", ["ask-voice-gui.py"]),
    ("Operator GUI", ["ask-operator-gui.py"]),
    ("Operator (Simulate)", ["ask-operator-simulate.sh"]),
    ("Planner", ["planner.py"]),
    ("Proposal UI", ["proposal-ui.py"]),
    ("Debate", ["debate.py"]),
    ("Autonomy Dashboard", ["autonomy-dashboard.py"]),
]


def resolve_command(cmd):
    return [str(BASE_DIR / cmd[0]), *cmd[1:]]


def run_command(cmd, status):
    resolved = resolve_command(cmd)
    try:
        subprocess.Popen(resolved)
        status.set(f"Launched: {' '.join(cmd)}")
    except FileNotFoundError:
        status.set(f"Missing: {cmd[0]}")
    except Exception as exc:
        status.set(f"Failed to launch {cmd[0]}: {exc}")


def build_ui(root):
    root.title("Autonomy Hub")
    root.geometry("420x520")

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Autonomy Hub", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)
    ttk.Label(frame, text="Launch core tools", foreground="#555").pack(anchor=tk.W, pady=(0, 12))

    status = tk.StringVar(value="Ready")

    for label, cmd in COMMANDS:
        button = ttk.Button(
            frame,
            text=label,
            command=lambda c=cmd: run_command(c, status),
        )
        button.pack(fill=tk.X, pady=4)

    ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

    ttk.Label(frame, textvariable=status, wraplength=380).pack(anchor=tk.W)
    ttk.Button(frame, text="Close", command=root.destroy).pack(anchor=tk.E, pady=(12, 0))


def main():
    root = tk.Tk()
    build_ui(root)
    root.mainloop()


if __name__ == "__main__":
    raise SystemExit(main())
