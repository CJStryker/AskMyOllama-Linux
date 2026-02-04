#!/usr/bin/env python3
import sounddevice as sd
import whisper
import tempfile
import subprocess
import numpy as np
import scipy.io.wavfile as wav
import sys

RATE = 16000
DURATION = 6  # seconds

print("🎤 Speak now...")

audio = sd.rec(int(DURATION * RATE), samplerate=RATE, channels=1, dtype='int16')
sd.wait()

with tempfile.NamedTemporaryFile(suffix=".wav") as f:
    wav.write(f.name, RATE, audio)
    model = whisper.load_model("base")
    result = model.transcribe(f.name)

text = result["text"].strip()

if not text:
    print("❌ No speech detected")
    sys.exit(1)

print(f"🗣️  You said: {text}\n")
subprocess.run(["ask", text])
