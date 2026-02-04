#!/usr/bin/env python3
import subprocess
from ask_gui_helper import show

try:
    text = subprocess.check_output(
        ["xclip", "-selection", "clipboard", "-o"],
        text=True
    ).strip()
except:
    show("Ask Clipboard", "Clipboard empty.")
    exit()

answer = subprocess.check_output(["ask", text], text=True)
show("Ask Clipboard", answer)
