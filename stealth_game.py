#!/usr/bin/env python3
"""Stealth Mini Games - entry point.

A tiny (~3 cm) borderless game collection for the bottom-left corner of the
screen: 7 games in a menu, no sound, ever. See README.md for the full
documentation, and engine/ for the architecture.

Windows 11: run build_exe.bat to produce dist/StealthGame.exe.
"""
from engine.app import App


def main():
    App().run()


if __name__ == "__main__":
    main()
