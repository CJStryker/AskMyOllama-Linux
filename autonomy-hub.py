#!/usr/bin/env python3
import importlib.util
import pathlib
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

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


def run_with_io(cmd, input_text, output_widget, status):
    resolved = resolve_command(cmd)
    output_widget.insert(tk.END, f"$ {' '.join(cmd)}\n")
    output_widget.see(tk.END)

    def worker():
        try:
            proc = subprocess.Popen(
                resolved,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except FileNotFoundError:
            output_widget.insert(tk.END, f"Missing: {cmd[0]}\n")
            output_widget.see(tk.END)
            status.set(f"Missing: {cmd[0]}")
            return
        except Exception as exc:
            output_widget.insert(tk.END, f"Failed to launch {cmd[0]}: {exc}\n")
            output_widget.see(tk.END)
            status.set(f"Failed to launch {cmd[0]}: {exc}")
            return

        try:
            stdout, _ = proc.communicate(input=input_text or "", timeout=120)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, _ = proc.communicate()
            stdout = f"{stdout}\n[timeout]\n"

        output_widget.insert(tk.END, stdout + "\n")
        output_widget.see(tk.END)
        status.set(f"Completed: {' '.join(cmd)}")

    threading.Thread(target=worker, daemon=True).start()


def tray_available():
    return (
        importlib.util.find_spec("pystray") is not None
        and importlib.util.find_spec("PIL.Image") is not None
    )


def build_tray_icon(root, status, tray_state):
    import pystray
    from PIL import Image, ImageDraw

    size = 64
    image = Image.new("RGB", (size, size), color="#1f1f1f")
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, size - 8, size - 8), outline="#7fd1ff", width=3)
    draw.text((18, 18), "A", fill="#7fd1ff")

    def on_open(icon, _item):
        icon.stop()
        tray_state["icon"] = None
        root.after(0, root.deiconify)
        status.set("Restored from tray.")

    def on_quit(icon, _item):
        icon.stop()
        tray_state["icon"] = None
        root.after(0, root.destroy)

    menu = pystray.Menu(
        pystray.MenuItem("Open Autonomy Hub", on_open),
        pystray.MenuItem("Quit", on_quit),
    )
    return pystray.Icon("autonomy-hub", image, "Autonomy Hub", menu)


def toggle_tray(root, status, tray_state):
    if tray_state.get("icon") is None:
        if not tray_available():
            status.set("Tray support requires pystray and pillow.")
            return
        icon = build_tray_icon(root, status, tray_state)
        tray_state["icon"] = icon
        root.withdraw()
        threading.Thread(target=icon.run, daemon=True).start()
        status.set("Minimized to tray.")
        return

    icon = tray_state.get("icon")
    if icon:
        icon.stop()
    tray_state["icon"] = None
    root.deiconify()
    status.set("Restored from tray.")


def build_ui(root):
    root.title("Autonomy Hub")
    root.geometry("760x640")

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Autonomy Hub", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)
    ttk.Label(frame, text="Launch core tools", foreground="#555").pack(anchor=tk.W, pady=(0, 12))

    status = tk.StringVar(value="Ready")
    tray_state = {"icon": None}

    selector = ttk.Combobox(
        frame,
        values=[label for label, _cmd in COMMANDS],
        state="readonly",
    )
    selector.current(0)
    selector.pack(fill=tk.X, pady=(0, 6))

    input_box = scrolledtext.ScrolledText(frame, height=6, wrap=tk.WORD)
    input_box.pack(fill=tk.X, pady=(0, 6))
    input_box.insert(tk.END, "Optional stdin input for the selected tool.\n")

    buttons = ttk.Frame(frame)
    buttons.pack(fill=tk.X, pady=(0, 8))

    def selected_cmd():
        label = selector.get()
        for name, cmd in COMMANDS:
            if name == label:
                return cmd
        return COMMANDS[0][1]

    ttk.Button(
        buttons,
        text="Launch",
        command=lambda: run_command(selected_cmd(), status),
    ).pack(side=tk.LEFT, padx=(0, 6))

    ttk.Button(
        buttons,
        text="Run with Input",
        command=lambda: run_with_io(
            selected_cmd(),
            input_box.get("1.0", tk.END),
            output_box,
            status,
        ),
    ).pack(side=tk.LEFT, padx=(0, 6))

    ttk.Button(
        buttons,
        text="Clear Output",
        command=lambda: output_box.delete("1.0", tk.END),
    ).pack(side=tk.LEFT, padx=(0, 6))

    ttk.Button(
        buttons,
        text="Toggle Tray",
        command=lambda: toggle_tray(root, status, tray_state),
    ).pack(side=tk.LEFT)

    output_box = scrolledtext.ScrolledText(frame, height=14, wrap=tk.WORD)
    output_box.pack(fill=tk.BOTH, expand=True)
    output_box.insert(tk.END, "Output will appear here.\n")

    ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

    ttk.Label(frame, textvariable=status, wraplength=700).pack(anchor=tk.W)
    ttk.Button(frame, text="Close", command=root.destroy).pack(anchor=tk.E, pady=(12, 0))


def main():
    root = tk.Tk()
    build_ui(root)
    root.mainloop()


if __name__ == "__main__":
    raise SystemExit(main())
