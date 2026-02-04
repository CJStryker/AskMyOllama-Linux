chris#!/usr/bin/env python3
import tkinter as tk, pathlib, json, time

BASE = pathlib.Path.home() / ".autonomy"
root = tk.Tk()
root.title("Autonomy Dashboard")
root.geometry("600x400")

txt = tk.Text(root, font=("Sans",11))
txt.pack(expand=True, fill=tk.BOTH)

def refresh():
    txt.delete("1.0", tk.END)
    txt.insert(tk.END, f"Autonomy: {'ON' if (BASE/'enabled').exists() else 'OFF'}\n")
    txt.insert(tk.END, f"Role: {(BASE/'current_role').read_text() if (BASE/'current_role').exists() else 'none'}\n\n")
    if (BASE/'proposal.json').exists():
        txt.insert(tk.END, (BASE/'proposal.json').read_text())
    root.after(5000, refresh)

refresh()
root.mainloop()
