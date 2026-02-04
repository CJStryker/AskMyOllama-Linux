#!/usr/bin/env python3
import json, pathlib, collections, tkinter as tk

LOGS = pathlib.Path.home()/".autonomy/logs"
counts = collections.Counter()
decisions = collections.Counter()

for f in LOGS.glob("*.json"):
    try:
        d = json.loads(f.read_text())
        sub = d.get("subsystem","unknown")
        counts[sub] += 1
        decisions[(sub, d.get("decision","none"))] += 1
    except: pass

root=tk.Tk(); root.title("Autonomy Heat-Map"); root.geometry("600x400")
t=tk.Text(root,font=("Sans",11)); t.pack(expand=True,fill=tk.BOTH)

for sub,c in counts.items():
    a = decisions.get((sub,"approved"),0)
    r = decisions.get((sub,"declined"),0)
    t.insert(tk.END,f"{sub.upper():10}  proposals:{c:3}  ✔{a}  ✖{r}\n")

root.mainloop()
