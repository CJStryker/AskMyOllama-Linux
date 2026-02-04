#!/usr/bin/env python3
import subprocess
from ask_gui_helper import show

res = subprocess.check_output(["ask-voice.py"], text=True)
show("Voice Ask", res)
