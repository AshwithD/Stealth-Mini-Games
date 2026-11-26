#!/usr/bin/env python3
"""Headless smoke test: boots the app with a dummy video driver and
auto-plays all 4 games via synthetic events. Exits 0 if it survives."""
import os
import subprocess
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
env = dict(os.environ, STEALTH_SELFTEST="1")

res = subprocess.run([sys.executable, "stealth_game.py"],
                     env=env, capture_output=True, text=True, timeout=90)
print(res.stdout[-3000:])
print(res.stderr[-4000:])
ok = res.returncode == 0 and "SELFTEST OK" in res.stdout
print("SMOKE TEST:", "PASSED" if ok else "FAILED")
sys.exit(0 if ok else 1)
