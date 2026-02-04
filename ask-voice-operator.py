#!/usr/bin/env python3
import sounddevice as sd
import whisper
import tempfile
import subprocess
import numpy as np
import scipy.io.wavfile as wav

RATE = 16000
DURATION = 6

print("🎤 Speak operator task...")

audio = sd.rec(int(DURATION * RATE), samplerate=RATE, channels=1, dtype='int16')
sd.wait()

with tempfile.NamedTemporaryFile(suffix=".wav") as f:
    wav.write(f.name, RATE, audio)
    model = whisper.load_model("base")
    result = model.transcribe(f.name)

task = result["text"].strip()

if not task:
    print("❌ No speech detected")
    exit(1)

print(f"🗣️  Task: {task}")
subprocess.run(["ask-operator.sh"], input=task, text=True)
