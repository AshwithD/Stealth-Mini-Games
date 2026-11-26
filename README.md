# 🎮 Stealth Mini Games

![Python](https://img.shields.io/badge/Python-3.12%2F3.13-3776AB)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-2b579a)
![License](https://img.shields.io/badge/License-MIT-green)
![Stars](https://img.shields.io/badge/Stars-welcome-yellow)

> A tiny **~3 cm × 3 cm** game collection that tucks itself into the
> **bottom-left corner** of your screen — built to be played **unnoticed at
> the office**. Borderless window, **zero sound**, automatic positioning, and
> crisp graphics scaled down to a distraction-sized box.

## 🎯 What is this?

Stealth Mini Games is a small, self-contained collection of 7 classic games
packaged into one **~3 cm window** that sits quietly in the corner of your
display. It's designed for moments when you want a quick, quiet break without
drawing any attention:

- **Tiny & unobtrusive** — the window is borderless, roughly the size of a
  sticky note, and parks itself in the bottom-left corner.
- **Completely silent** — there is **no audio code anywhere** in the project.
  Nothing can ever make a sound, which is exactly what you want at work.
- **7 games, one menu** — pick from Snake, Type Rush, 2048, Flappy, Memory,
  Reaction and Breakout.
- **Drag to move** — grab the window with the mouse and place it anywhere.
- **Remembers your best scores** — saved next to the executable, no setup.

```
┌─────────────────────────────┐
│       MINI GAMES            │   ← 7-game menu, ~3 cm
│  ┌─────────┐  ┌─────────┐   │
│  │ 1 SNAKE │  │ 2 TYPE  │   │   1 Snake   ·  2 Type Rush
│  └─────────┘  └─────────┘   │   3 2048    ·  4 Flappy
│  ┌─────────┐  ┌─────────┐   │   5 Memory  ·  6 Reaction
│  │ 3 2048  │  │ 4 FLAP  │   │   7 Breakout
│  └─────────┘  └─────────┘   │
│  ┌─────────┐  ┌─────────┐   │
│  │ 5 MEM   │  │ 6 REACT │   │
│  └─────────┘  └─────────┘   │
│  ┌─────────┐  ┌─────────┐   │
│  │ 7 BREAK │  │ 8 STATS │   │
│  └─────────┘  └─────────┘   │
└─────────────────────────────┘
```

## ⬇️ Download (prebuilt .exe)

Skip the build entirely — grab the ready-to-run executable:

**[📥 Download `StealthGame.exe`](https://github.com/AshwithD/Stealth-Mini-Games/blob/master/dist/StealthGame.exe)**

Drop it anywhere, double-click, and play. No Python or dependencies needed.

> Prefer to build it yourself? See **Quick Start** below.

## ✨ Features

- **Tiny & stealthy** — borderless window, no title bar or buttons, starts at
  the bottom-left corner, and makes **no sound whatsoever** (by design).
- **7 games in one menu** — Snake, Type Rush, 2048, Flappy, Memory,
  Reaction and Breakout. Pick with the keyboard or a click.
- **Crisp at 3 cm** — everything renders at a 360×360 internal resolution and
  is scaled smoothly to the tiny window, so graphics stay clean.
- **Smooth, glitch-free motion** — Snake slides fluidly between cells and
  Flappy uses tuned, forgiving physics, so nothing looks jerky at small sizes.
- **Drag to move** — press anywhere and drag to relocate the window. A
  movement threshold separates drags from clicks, so clicking a menu button
  still starts a game.
- **Fair starts, no premature game-over** — every game has start-grace
  guards; a freshly launched game can never end before you've had a chance
  to play (verified by the test suite).
- **Best scores** — each game remembers your best score (saved next to the
  executable, no setup).
- **Pause & always-on-top** — in-game pause plus a one-key toggle to keep the
  window above everything.

## 🎯 The games

| Key | Game | Controls |
|:---:|------|----------|
| `1` | **Snake** | Arrow keys / WASD; `M` toggles wrap/walls mode |
| `2` | **Type Rush** | Type the word (looks like real typing work — best camo) |
| `3` | **2048** | Arrow keys / WASD; `U` undoes the last move |
| `4` | **Flap** | `Space` / `↑` / `W` / click |
| `5` | **Memory** | Click cards; match all 8 pairs in fewest moves |
| `6` | **Reaction** | Click the dot before it disappears |
| `7` | **Breakout** | Mouse hover / `A`–`D` for the paddle; `Space`/click to launch |

## ⌨️ Controls

| Action | Input |
|--------|-------|
| Start a game | `1`–`7` or click a menu button |
| View stats | `8` or click **STATS** |
| Back to menu | `Esc` (in a game, or on the stats screen) |
| Quit | `Esc` / `Q` on menu, or **right-click** anywhere |
| Move the window | Press left mouse **anywhere** and drag |
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
then edit the `settings.json` file created next to the executable (or the
defaults in `engine/config.py`) and restart:

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
python test_logic.py          # 114 deep logic tests (config, storage,
                              # drag, menu, every game's mechanics)
python test_smoke.py          # boots the app and auto-plays all 7 games
python make_screenshots.py    # renders every screen + pixel-content checks
python analyze_screenshots.py # critiques rendering at the real window size
```

Screenshots rendered by the tools live in `screenshots/` (canvas-size
previews) and `screenshots/win/` (actual window-size previews).

## 🗂️ Project Structure

```
stealth_game/
├── stealth_game.py          # entry point: starts the App
├── engine/                  # the game engine (modular)
│   ├── __init__.py          # package docstring
│   ├── constants.py         # colors, MOVE_KEYS, CANVAS, window flags
│   ├── config.py            # settings.json load/save + validators
│   ├── storage.py           # Store: best scores / plays / wins
│   ├── input.py             # DragController: click-vs-drag + window moving
│   ├── renderer.py          # canvas scaling, fonts, overlays
│   ├── menu.py              # 3×3 menu grid + stats screen
│   ├── app.py               # state machine, event pump, main loop
│   └── games/               # the 7 games (one file each)
│       ├── base.py          # GameBase contract
│       ├── snake.py         # 1 Snake
│       ├── type_rush.py     # 2 Type Rush
│       ├── game2048.py      # 3 2048 (undo + animations)
│       ├── flap.py          # 4 Flappy
│       ├── memory.py        # 5 Memory
│       ├── reaction.py      # 6 Reaction
│       └── breakout.py      # 7 Breakout
├── build_exe.bat            # one-click Windows .exe builder
├── test_smoke.py            # headless runtime self-test
├── test_logic.py            # game-logic unit tests
├── make_screenshots.py      # renders screens + verifies content
├── analyze_screenshots.py   # renders at window size + visual critique
└── screenshots/             # rendered previews (canvas + window size)
```

### Architecture

- **engine/** is the framework: constants, config, storage, input, renderer
  and the app state machine. Games never import each other — they only
  implement the `GameBase` contract (`reset`, `handle`, `update`, `draw`).
- **Adding a game** = write a class in `engine/games/`, then add it to
  `GAME_CLASSES` and `GAME_META` in `engine/games/__init__.py`. Nothing else
  changes — the menu, stats, input routing and recording pick it up
  automatically.
- **Rendering** draws on a 360×360 canvas and smooth-scales to the window,
  keeping every element legible at ~3 cm.
- **Drag vs click** is resolved globally: a left press that moves past a
  6-pixel threshold drags the window; a press-without-move is a click.

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
  `Esc`/`Q` or right-click; move it by pressing and dragging anywhere.

## 📄 License

MIT — do whatever you like. Play responsibly (and quietly) at work. 🤫
