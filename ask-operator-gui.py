#!/usr/bin/env python3
import subprocess
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

proc = None

def start():
    global proc
    task = entry.get().strip()
    if not task:
        return

    output.delete("1.0", tk.END)
    proc = subprocess.Popen(
        ["ask-operator.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    proc.stdin.write(task + "\n")
    proc.stdin.flush()
    root.after(100, read_output)

def read_output():
    if proc:
        line = proc.stdout.readline()
        if line:
            output.insert(tk.END, line)
            output.see(tk.END)
            root.after(100, read_output)

root = tk.Tk()
root.title("AI System Operator")
root.geometry("700x500")
root.attributes("-topmost", True)

entry = tk.Entry(root, font=("Sans", 12))
entry.pack(fill=tk.X, padx=6, pady=6)
entry.focus()

btn = tk.Button(root, text="Start Operator", command=start)
btn.pack(pady=4)

output = ScrolledText(root, font=("Sans", 11))
output.pack(expand=True, fill=tk.BOTH, padx=6, pady=6)

root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()
