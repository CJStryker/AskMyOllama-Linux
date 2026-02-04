#!/usr/bin/env python3
import subprocess, tkinter as tk
from tkinter.scrolledtext import ScrolledText

def run():
    q = entry.get().strip()
    if not q:
        return
    out.delete("1.0", tk.END)
    res = subprocess.check_output(["ask", q], text=True)
    out.insert(tk.END, res)

root = tk.Tk()
root.title("Ask")
root.geometry("600x400")
root.attributes("-topmost", True)

entry = tk.Entry(root, font=("Sans", 12))
entry.pack(fill=tk.X, padx=6, pady=6)
entry.focus()

tk.Button(root, text="Ask", command=run).pack()

out = ScrolledText(root, font=("Sans", 11))
out.pack(expand=True, fill=tk.BOTH, padx=6, pady=6)

root.bind("<Return>", lambda e: run())
root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()
