#!/usr/bin/env python3
import subprocess
from ask_gui_helper import show

try:
    text = subprocess.check_output(
        ["xclip", "-selection", "primary", "-o"],
        text=True
    ).strip()
except:
    show("Ask Selection", "No text selected.")
    exit()

if not text:
    show("Ask Selection", "No text selected.")
    exit()

answer = subprocess.check_output(["ask", text], text=True)
show("Ask Selection", answer)
