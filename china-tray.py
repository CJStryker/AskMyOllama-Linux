#!/usr/bin/env python3
import subprocess, os
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

def run(cmd):
    subprocess.Popen(cmd, shell=True)

def create_icon():
    img = Image.new("RGB", (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.text((18, 18), "问", fill="black")
    return img

menu = pystray.Menu(
    item("Ask (Floating Window)", lambda i, _: run("ask-float.py")),
    item("Ask Selection (Ctrl+Alt+S)", lambda i, _: run("ask-select")),
    item("Ask Clipboard", lambda i, _: run("ask-clip")),
    item("Explain System Errors", lambda i, _: run("ask-error")),
    pystray.Menu.SEPARATOR,
    item("Quit Tray", lambda i, _: i.stop())
)

icon = pystray.Icon("ask", create_icon(), "System Assistant", menu)
icon.run()
