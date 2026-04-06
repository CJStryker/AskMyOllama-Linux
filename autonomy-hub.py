#!/usr/bin/env python3
import importlib.util
import pathlib
import os
import queue
import subprocess
import threading
import time
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

BASE_DIR = pathlib.Path(__file__).resolve().parent
LOG_DIR = pathlib.Path.home() / ".autonomy"
HUB_LOG = LOG_DIR / "autonomy-hub.log"

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


def tray_available():
    return (
        importlib.util.find_spec("pystray") is not None
        and importlib.util.find_spec("PIL.Image") is not None
    )


def shutil_which(binary):
    return shutil.which(binary)


class HubApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autonomy Hub")
        self.root.geometry("900x700")

        LOG_DIR.mkdir(parents=True, exist_ok=True)

        self.status = tk.StringVar(value="Ready")
        self.filter_var = tk.StringVar(value="")
        self.timeout_var = tk.StringVar(value="120")
        self.args_var = tk.StringVar(value="")
        self.command_map = {label: cmd for label, cmd in COMMANDS}
        self.output_queue = queue.Queue()
        self.tray_icon = None
        self.run_history = []

        self.build_ui()
        self.populate_commands()
        self.poll_output_queue()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Autonomy Hub", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(frame, text="Unified launcher and runner for autonomy tools", foreground="#555").pack(anchor=tk.W, pady=(0, 10))

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(top, text="Filter:").pack(side=tk.LEFT)
        filter_entry = ttk.Entry(top, textvariable=self.filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 8))
        filter_entry.bind("<KeyRelease>", lambda _evt: self.populate_commands())

        ttk.Label(top, text="Timeout (s):").pack(side=tk.LEFT)
        ttk.Entry(top, width=8, textvariable=self.timeout_var).pack(side=tk.LEFT, padx=(6, 0))

        args_row = ttk.Frame(frame)
        args_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(args_row, text="Args:").pack(side=tk.LEFT)
        ttk.Entry(args_row, textvariable=self.args_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        self.selector = ttk.Combobox(frame, state="readonly")
        self.selector.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(frame, text="Input (stdin):").pack(anchor=tk.W)
        self.input_box = scrolledtext.ScrolledText(frame, height=7, wrap=tk.WORD)
        self.input_box.pack(fill=tk.X, pady=(0, 8))

        button_row = ttk.Frame(frame)
        button_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(button_row, text="Launch Detached", command=self.launch_detached).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_row, text="Run with Input/Output", command=self.run_with_io).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_row, text="System Check", command=self.run_system_check).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_row, text="Open Proposal", command=self.open_proposal).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_row, text="Save Output", command=self.save_output).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_row, text="Copy Output", command=self.copy_output).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_row, text="Toggle Tray", command=self.toggle_tray).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_row, text="Clear", command=lambda: self.output_box.delete("1.0", tk.END)).pack(side=tk.LEFT)

        ttk.Label(frame, text="Output:").pack(anchor=tk.W)
        self.output_box = scrolledtext.ScrolledText(frame, height=18, wrap=tk.WORD)
        self.output_box.pack(fill=tk.BOTH, expand=True)
        self.output_box.insert(tk.END, "Output will appear here.\n")

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(frame, textvariable=self.status, wraplength=850).pack(anchor=tk.W)

    def populate_commands(self):
        needle = self.filter_var.get().strip().lower()
        labels = [label for label, _ in COMMANDS if needle in label.lower()]
        if not labels:
            labels = [label for label, _ in COMMANDS]

        previous = self.selector.get()
        self.selector["values"] = labels
        if previous in labels:
            self.selector.set(previous)
        elif labels:
            self.selector.set(labels[0])

    def selected_cmd(self):
        label = self.selector.get()
        cmd = list(self.command_map.get(label, COMMANDS[0][1]))
        extra = self.args_var.get().strip()
        if extra:
            cmd.extend(extra.split())
        return cmd

    def append_output(self, text):
        self.output_box.insert(tk.END, text)
        self.output_box.see(tk.END)
        with HUB_LOG.open("a") as f:
            f.write(text)

    def set_status(self, text):
        self.status.set(text)

    def launch_detached(self):
        cmd = self.selected_cmd()
        resolved = resolve_command(cmd)
        try:
            subprocess.Popen(resolved)
            self.set_status(f"Launched detached: {' '.join(cmd)}")
            self.append_output(f"$ {' '.join(cmd)} [detached]\n")
            self.record_history(cmd, mode="detached")
        except FileNotFoundError:
            self.set_status(f"Missing: {cmd[0]}")
        except Exception as exc:
            self.set_status(f"Failed to launch {cmd[0]}: {exc}")

    def run_with_io(self):
        cmd = self.selected_cmd()
        resolved = resolve_command(cmd)
        input_text = self.input_box.get("1.0", tk.END)
        timeout_s = self.parse_timeout()

        self.append_output(f"\n$ {' '.join(cmd)}\n")
        self.set_status(f"Running: {' '.join(cmd)}")
        self.record_history(cmd, mode="io")

        def worker():
            started = time.time()
            try:
                proc = subprocess.Popen(
                    resolved,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
            except FileNotFoundError:
                self.output_queue.put(("output", f"Missing: {cmd[0]}\n"))
                self.output_queue.put(("status", f"Missing: {cmd[0]}"))
                return
            except Exception as exc:
                self.output_queue.put(("output", f"Failed to launch {cmd[0]}: {exc}\n"))
                self.output_queue.put(("status", f"Failed to launch {cmd[0]}: {exc}"))
                return

            try:
                if proc.stdin:
                    proc.stdin.write(input_text)
                    proc.stdin.close()

                while True:
                    line = proc.stdout.readline() if proc.stdout else ""
                    if not line and proc.poll() is not None:
                        break
                    if line:
                        self.output_queue.put(("output", line))

                proc.wait(timeout=max(timeout_s, 1))
                elapsed = time.time() - started
                self.output_queue.put(("status", f"Completed: {' '.join(cmd)} in {elapsed:.1f}s (rc={proc.returncode})"))
            except subprocess.TimeoutExpired:
                proc.kill()
                self.output_queue.put(("output", "[timeout reached]\n"))
                self.output_queue.put(("status", f"Timed out: {' '.join(cmd)}"))

        threading.Thread(target=worker, daemon=True).start()

    def parse_timeout(self):
        try:
            value = int(self.timeout_var.get().strip())
            return max(value, 1)
        except ValueError:
            self.timeout_var.set("120")
            return 120

    def poll_output_queue(self):
        while True:
            try:
                typ, payload = self.output_queue.get_nowait()
            except queue.Empty:
                break

            if typ == "output":
                self.append_output(payload)
            elif typ == "status":
                self.set_status(payload)

        self.root.after(100, self.poll_output_queue)

    def open_proposal(self):
        try:
            subprocess.Popen(resolve_command(["proposal-ui.py"]))
            self.set_status("Opened proposal-ui.py")
        except Exception as exc:
            self.set_status(f"Unable to open proposal-ui.py: {exc}")

    def save_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Autonomy Hub Output",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            pathlib.Path(path).write_text(self.output_box.get("1.0", tk.END))
            self.set_status(f"Saved output: {path}")
        except Exception as exc:
            self.set_status(f"Failed to save output: {exc}")

    def copy_output(self):
        text = self.output_box.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("Copied output to clipboard.")

    def record_history(self, cmd, mode):
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{stamp} [{mode}] {' '.join(cmd)}"
        self.run_history.append(entry)
        self.append_output(f"[history] {entry}\n")

    def run_system_check(self):
        checks = []
        checks.append(("python", shutil_which("python3") or shutil_which("python")))
        checks.append(("jq", shutil_which("jq")))
        checks.append(("curl", shutil_which("curl")))
        checks.append(("ask", os.path.exists(str(BASE_DIR / "ask"))))
        checks.append(("planner.py", os.path.exists(str(BASE_DIR / "planner.py"))))
        checks.append(("proposal-ui.py", os.path.exists(str(BASE_DIR / "proposal-ui.py"))))

        lines = ["System check results:"]
        for name, ok in checks:
            state = "OK" if ok else "MISSING"
            lines.append(f"- {name}: {state}")
        report = "\n".join(lines)
        self.append_output(report + "\n")
        self.set_status("System check completed.")
        messagebox.showinfo("Autonomy Hub Check", report)

    def build_tray_icon(self):
        import pystray
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (64, 64), color="#1f1f1f")
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 56, 56), outline="#7fd1ff", width=3)
        draw.text((22, 20), "A", fill="#7fd1ff")

        def on_open(icon, _item):
            icon.stop()
            self.tray_icon = None
            self.root.after(0, self.root.deiconify)
            self.root.after(0, lambda: self.set_status("Restored from tray."))

        def on_quit(icon, _item):
            icon.stop()
            self.tray_icon = None
            self.root.after(0, self.root.destroy)

        menu = pystray.Menu(
            pystray.MenuItem("Open Autonomy Hub", on_open),
            pystray.MenuItem("Quit", on_quit),
        )
        return pystray.Icon("autonomy-hub", image, "Autonomy Hub", menu)

    def toggle_tray(self):
        if self.tray_icon is None:
            if not tray_available():
                self.set_status("Tray support requires pystray and pillow.")
                return
            self.tray_icon = self.build_tray_icon()
            self.root.withdraw()
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            self.set_status("Minimized to tray.")
            return

        self.tray_icon.stop()
        self.tray_icon = None
        self.root.deiconify()
        self.set_status("Restored from tray.")


def main():
    root = tk.Tk()
    HubApp(root)
    root.mainloop()


if __name__ == "__main__":
    raise SystemExit(main())
