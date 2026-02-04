#!/usr/bin/env python3
import subprocess
from ask_gui_helper import show

errors = subprocess.check_output(
    ["journalctl", "-p", "err", "-n", "30", "--no-pager"],
    text=True
)

if not errors.strip():
    show("System Errors", "No recent system errors.")
else:
    answer = subprocess.check_output(
        ["ask", "Explain these system errors:\n" + errors],
        text=True
    )
    show("System Errors", answer)
