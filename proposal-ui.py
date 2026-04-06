#!/usr/bin/env python3
import json
import pathlib
import tkinter as tk
from tkinter import ttk

HOME = pathlib.Path.home()
AUTON = HOME / ".autonomy"
PROP = AUTON / "proposal.json"


def load_proposal():
    if not PROP.exists():
        return {"task": "(missing proposal.json)", "confidence": 0, "steps": []}
    try:
        return json.loads(PROP.read_text())
    except Exception:
        return {"task": "(invalid proposal.json)", "confidence": 0, "steps": []}


def build_ui(root, proposal):
    root.title("Proposal")
    root.geometry("720x480")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    task = proposal.get("task", "(unknown)")
    confidence = proposal.get("confidence", 0)
    steps = proposal.get("steps", [])

    header = ttk.Label(frame, text="Autonomy Proposal", font=("TkDefaultFont", 14, "bold"))
    header.pack(anchor=tk.W)

    ttk.Label(frame, text=f"Task: {task}").pack(anchor=tk.W, pady=(8, 0))
    ttk.Label(frame, text=f"Confidence: {int(confidence * 100)}%" ).pack(anchor=tk.W)
    ttk.Label(frame, text=f"Steps: {len(steps)}").pack(anchor=tk.W, pady=(0, 8))

    columns = ("id", "description", "risk", "command")
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    tree.heading("id", text="ID")
    tree.heading("description", text="Description")
    tree.heading("risk", text="Risk")
    tree.heading("command", text="Command")

    tree.column("id", width=80, anchor=tk.W)
    tree.column("description", width=220, anchor=tk.W)
    tree.column("risk", width=80, anchor=tk.W)
    tree.column("command", width=280, anchor=tk.W)

    for step in steps:
        tree.insert("", tk.END, values=(
            step.get("id", ""),
            step.get("description", ""),
            step.get("risk", ""),
            step.get("command", ""),
        ))

    tree.pack(fill=tk.BOTH, expand=True)

    ttk.Button(frame, text="Close", command=root.destroy).pack(anchor=tk.E, pady=(8, 0))


def main():
    proposal = load_proposal()
    root = tk.Tk()
    build_ui(root, proposal)
    root.mainloop()


if __name__ == "__main__":
    main()
