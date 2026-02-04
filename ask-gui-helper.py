import subprocess, tkinter as tk
from tkinter.scrolledtext import ScrolledText

def show(title, text):
    root = tk.Tk()
    root.title(title)
    root.geometry("600x400")
    root.attributes("-topmost", True)

    box = ScrolledText(root, font=("Sans", 11))
    box.pack(expand=True, fill=tk.BOTH, padx=6, pady=6)
    box.insert(tk.END, text)
    box.config(state=tk.DISABLED)

    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()
