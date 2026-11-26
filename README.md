# 🎮 Stealth Mini Games

![Python](https://img.shields.io/badge/Python-3.12%2F3.13-3776AB)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-2b579a)
![License](https://img.shields.io/badge/License-MIT-green)

A tiny **~3 cm × 3 cm** game collection that starts with a 4-option menu and
tucks itself into the **bottom-left corner** of your screen — built to be
played **unnoticed at the office**. Borderless window, **zero sound**,
automatic positioning, and crisp high-resolution graphics scaled down to a
distraction-sized box.

```
┌─────────────────────────────┐
│       MINI GAMES            │   ← 4-option menu, ~3 cm
│  ┌─────────┐  ┌─────────┐   │
│  │ 1 SNAKE │  │ 2 TYPE  │   │   1 Snake   ·  2 Type Rush
│  └─────────┘  └─────────┘   │   3 2048    ·  4 Flappy
│  ┌─────────┐  ┌─────────┐   │
│  │ 3 2048  │  │ 4 FLAP  │   │
│  └─────────┘  └─────────┘   │
└─────────────────────────────┘
```

## ✨ Features

- **Tiny & stealthy** — borderless window, no title bar or buttons, starts at
  the bottom-left corner, and makes **no sound whatsoever** (by design).
- **4 games in one menu** — Snake, Type Rush, 2048 and Flappy. Pick with the
  keyboard or a click.
- **Crisp at 3 cm** — everything renders at a 360×360 internal resolution and
  is scaled smoothly to the tiny window, so graphics stay clean.
- **Drag to move** — pick up the window with the mouse and place it anywhere.
- **Best scores** — each game remembers your best score (saved next to the
  executable, no setup).
- **Pause & always-on-top** — in-game pause plus a one-key toggle to keep the
  window above everything.
- **Office-safe by construction** — no audio code exists in the project, so
  there is nothing that can ever make a sound.

## 🎯 The games

| Key | Game | Controls |
|:---:|------|----------|
| `1` | **Snake** | Arrow keys / WASD |
| `2` | **Type Rush** | Type the falling word (looks like real typing work — best camo) |
| `3` | **2048** | Arrow keys / WASD |
| `4` | **Flap** | `Space` / `↑` / `W` / click |

## ⌨️ Controls

| Action | Input |
|--------|-------|
| Start a game | `1`–`4` or click a menu button |
| Back to menu | `Esc` (in a game) |
| Quit | `Esc` / `Q` on menu, or **right-click** anywhere |
| Move the window | Hold left mouse on the menu and drag |
| Pause / unpause | `P` (in a game) |
| Always-on-top toggle | `T` |

## 🚀 Quick Start (Windows 11)

### Prerequisites

- **Python 3.12 or 3.13** from [python.org](https://www.python.org/downloads/)
  — during setup, **check "Add python.exe to PATH"**.
  > ⚠️ pygame 2.6.x ships prebuilt binaries only up to **Python 3.13**.
  > Python 3.14+ will fail to install pygame — use 3.12/3.13.

### Build the .exe

1. Download this repository / copy the folder.
2. **Double-click `build_exe.bat`** — it installs `pygame` + `pyinstaller`
   and builds the executable automatically.
3. Your game is ready at **`dist\StealthGame.exe`** — a single file, no
   console window. Double-click to play.

Prefer the terminal?

```bat
pip install pygame pyinstaller
pyinstaller --noconfirm --onefile --windowed --name StealthGame stealth_game.py
```

## 📐 Getting the exact 3 cm size

The window size is computed as:

```
window_pixels = target_cm × pixels_per_cm
```

The default `pixels_per_cm = 38` suits a 24" 1080p monitor. Calibrate for
**your** screen with a ruler (`pixels_per_cm = screen_width_px ÷ screen_width_cm`),
then edit the single setting at the top of `stealth_game.py` and rebuild:

| Screen | Approx. pixels/cm | Set this to |
|--------|:---:|:---:|
| 13–14" laptop (1366 px wide) | ~44 | `44` |
| 15.6" laptop (1920 px wide) | ~56 | `56` |
| 24" monitor (1920 px wide) | ~36 | `36` |
| 27" monitor (2560 px wide) | ~43 | `43` |

> Windows display scaling can shift the physical size slightly — adjust until
> a ruler confirms ~3 cm.

## 💻 Development

Run straight from source (no build needed):

```bash
pip install pygame
python stealth_game.py
```

### Tests

The project ships with a headless test suite (uses a dummy video driver, no
display required):

```bash
python test_smoke.py        # boots the app and auto-plays all 4 games
python test_logic.py        # deep logic tests for every game
python make_screenshots.py  # renders every screen + pixel-content checks
python analyze_screenshots.py  # critiques rendering at the real window size
```

Screenshots rendered by the tools live in `screenshots/` (canvas-size
previews) and `screenshots/win/` (actual window-size previews).

## 🗂️ Project Structure

```
stealth_game/
├── stealth_game.py        # the entire game (single file, no assets)
├── build_exe.bat          # one-click Windows .exe builder
├── best_scores.json       # created at runtime - per-game best scores
├── test_smoke.py          # headless runtime self-test
├── test_logic.py          # game-logic unit tests
├── make_screenshots.py    # renders screens + verifies content
├── analyze_screenshots.py # renders at window size + visual critique
└── screenshots/           # rendered previews (canvas + window size)
```

## 🛠️ Troubleshooting

- **`Failed to build 'pygame'` / `distutils` errors** — you're on Python
  3.14+. Install **Python 3.12** (see Prerequisites) and re-run.
- **`"X" was unexpected at this time` when running `build_exe.bat`** — cmd.exe
  breaks when the **folder path contains parentheses** (e.g. `... (1)\...`).
  The build script avoids `if`-blocks entirely, so just use the latest file;
  if it still happens, copy the folder to a simple path like `C:\stealthgame`.
- **`python` opens the Microsoft Store** — the script uses the `py` launcher
  which bypasses this. You can also disable the app execution alias in
  Windows Settings → Apps → Advanced app settings → App execution aliases.
- **Antivirus warning on first run** — unsigned PyInstaller executables are
  occasionally flagged. Click "Allow" or add the file as an exclusion.
- **No close button** — the window is borderless on purpose. Quit with
  `Esc`/`Q` or right-click; move it by dragging on the menu.

## 📄 License

MIT — do whatever you like. Play responsibly (and quietly) at work. 🤫
