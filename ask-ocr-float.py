#!/usr/bin/env python3
import subprocess
import tempfile
import os
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

def run_ocr_and_ask():
    with tempfile.TemporaryDirectory() as tmp:
        img = os.path.join(tmp, "ocr.png")
        txt = os.path.join(tmp, "ocr")

        # Screenshot selection
        subprocess.run(
            ["flameshot", "gui", "-p", img],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if not os.path.exists(img):
            return "OCR cancelled."

        # OCR Chinese + English
        subprocess.run(
            ["tesseract", img, txt, "-l", "chi_sim+eng"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        text_file = txt + ".txt"
        if not os.path.exists(text_file):
            return "No text detected."

        with open(text_file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()

        if not text:
            return "No text detected."

        # Ask Ollama via `ask`
        try:
            result = subprocess.check_output(
                ["ask", "Explain or translate the following text:", text],
                stderr=subprocess.STDOUT,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            return e.output

# -------------------------
# GUI
# -------------------------
root = tk.Tk()
root.title("Ask OCR")
root.geometry("600x400")
root.attributes("-topmost", True)

output = ScrolledText(root, font=("Sans", 11))
output.pack(expand=True, fill=tk.BOTH, padx=6, pady=6)

output.insert(tk.END, "Select a screen area for OCR...\n")
output.update()

answer = run_ocr_and_ask()
output.delete("1.0", tk.END)
output.insert(tk.END, answer)

root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()
