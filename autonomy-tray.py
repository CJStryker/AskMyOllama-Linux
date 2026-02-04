#!/usr/bin/env python3
import gi, subprocess, os, pathlib
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3

BASE = pathlib.Path.home() / ".autonomy"
STATE = BASE / "enabled"
ROLE  = BASE / "current_role"

def run(cmd):
    subprocess.Popen(cmd, shell=True)

def toggle_autonomy(_):
    if STATE.exists():
        STATE.unlink()
        run("systemctl --user stop autonomy.service")
    else:
        STATE.touch()
        run("systemctl --user start autonomy.service")

def set_role(role):
    ROLE.write_text(role)

def icon_for_state():
    try:
        state = subprocess.check_output(
            ["autonomy-health-state.sh"],
            text=True
        ).strip()
    except:
        state = "unknown"

    if state == "green":
        return "dialog-information"
    elif state == "yellow":
        return "dialog-warning"
    elif state == "red":
        return "dialog-error"
    else:
        return "dialog-question"

indicator = AppIndicator3.Indicator.new(
    "autonomy",
    icon_for_state(),
    AppIndicator3.IndicatorCategory.APPLICATION_STATUS
)

indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

def refresh_tooltip():
    try:
        tip = subprocess.check_output(
            ["autonomy-health-summary.sh"],
            text=True
        ).strip()
    except:
        tip = "Autonomy status unknown"

    indicator.set_title(tip)
    return True


menu = Gtk.Menu()

def item(label, cmd=None):
    m = Gtk.MenuItem(label=label)
    if cmd:
        m.connect("activate", lambda *_: run(cmd))
    m.show()
    menu.append(m)

item("🧠 Ask (Floating)", "ask-float.py")
item("📷 OCR", "ask-ocr-float.py")
item("🎤 Voice Ask", "ask-voice-gui.py")
menu.append(Gtk.SeparatorMenuItem())

item("🤖 Operator GUI", "ask-operator-gui.py")
item("🎤 Voice Operator", "ask-voice-operator.py")
menu.append(Gtk.SeparatorMenuItem())

item("📊 Autonomy Dashboard", "autonomy-dashboard.py")
item("✅ Check System Health", "autonomy-health.sh")

item("🛡 Policy Editor", "policy-editor-gui.py")
item("🔁 Toggle Autonomy", "autonomy-toggle.sh")
menu.append(Gtk.SeparatorMenuItem())

item("Role: Admin", None); item("→ Set Admin", "echo admin > ~/.autonomy/current_role")
item("→ Set Observer", "echo observer > ~/.autonomy/current_role")
item("→ Set Operator", "echo operator > ~/.autonomy/current_role")

menu.append(Gtk.SeparatorMenuItem())
quit_item = Gtk.MenuItem(label="Quit")
quit_item.connect("activate", lambda *_: Gtk.main_quit())
quit_item.show()
menu.append(quit_item)

indicator.set_menu(menu)
Gtk.main()

def refresh_icon():
    indicator.set_icon(icon_for_state())
    return True  # keep timer

from gi.repository import GLib
GLib.timeout_add_seconds(60, refresh_tooltip)
refresh_tooltip()
