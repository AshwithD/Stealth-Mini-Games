# Stealth Mini Games

A tiny (~3 cm) game collection that starts with a **4-option menu** and tucks
itself into the **bottom-left corner** of your screen. Built for playing
unnoticed at the office.

The window is **borderless** — no title bar, no minimize/close buttons. Games
render at a high internal resolution (360×360) and are scaled smoothly to the
small window, so they stay crisp at tiny physical sizes.

**To close the app: press Esc or Q** (there is no window chrome to click).

## The 4 games (menu at startup)

| Key | Game | Controls |
|-----|------|----------|
| 1 | **Snake** | Arrow keys / WASD |
| 2 | **Type Rush** | Type the word, press letters A-Z (great office camo — looks like typing work) |
| 3 | **2048** | Arrow keys / WASD |
| 4 | **Flap** | Space / Up / W / click |

- **Esc** inside a game → back to the menu.
- **Esc / Q** on the menu → quit.
- Game over → press any key → menu.

## Size: making the window exactly 3 cm

The window size is: `window_px = target_cm × pixels_per_cm`

The default `pixels_per_cm = 38` is a good guess for a 24" 1080p monitor.
Tune it to **your** screen with a ruler (measure the screen width in cm, then
`pixels_per_cm = screen_width_px ÷ screen_width_cm`):

| Screen | Approx. pixels/cm | Set this to |
|--------|-------------------|-------------|
| 13–14" laptop (1366 px wide) | ~44 | 44 |
| 15.6" laptop (1920 px wide) | ~56 | 56 |
| 24" monitor (1920 px wide) | ~36 | 36 |
| 27" monitor (2560 px wide) | ~43 | 43 |

Just edit `pixels_per_cm` at the top of `stealth_game.py` and rebuild — or
run the `.py` directly to test instantly. (Windows display scaling can shift
physical size slightly; adjust until a ruler confirms ~3 cm.)

## Building the .exe on Windows 11

1. Install Python from https://www.python.org/downloads/
   → during setup, **check "Add python.exe to PATH"**.
2. Put `stealth_game.py` and `build_exe.bat` in one folder.
3. **Double-click `build_exe.bat`** (it installs pygame + pyinstaller, then builds).
4. The finished app is at **`dist\StealthGame.exe`** — a single file, no console.

Manual command, if you prefer the terminal:

```
pip install pygame pyinstaller
pyinstaller --noconfirm --onefile --windowed --name StealthGame stealth_game.py
```

## Run without building (development)

```
pip install pygame
python stealth_game.py
```

The window appears at the bottom-left automatically.

## Preview

Rendered previews of every screen (menu, all 4 games, game-over states) are in
the `screenshots/` folder — open any PNG to see how the tiny window looks.

## Notes / troubleshooting

- **No close button on the window:** the window is borderless on purpose.
  Press **Esc** or **Q** to quit (on the menu, or in a game it returns to
  the menu first).
- **Antivirus:** unsigned PyInstaller executables are occasionally flagged on
  first run. If Windows Defender blocks it, click "Allow" or add the file as an
  exclusion.
- **Window hidden behind other windows:** that's expected with a plain (not
  always-on-top) window. If you want it to stay above everything, set
  `"always_on_top": True` in `CONFIG` and rebuild.
- **Tired of the title?** It's plain ("Mini Games") by design. Change
  `CONFIG["title"]` if you want something else.
- **"Failed to build 'pygame' ... ModuleNotFoundError: distutils" /
  building from source errors:** pygame 2.6.x only ships prebuilt binaries
  up to **Python 3.13**. If you have Python 3.14+ (e.g. the Store/pythoncore
  3.14 install), pip tries to compile pygame from source and fails.
  Fix: install **Python 3.12** from python.org (check "Add python.exe to
  PATH"). The updated `build_exe.bat` auto-selects Python 3.12/3.13 and will
  tell you if your version is unsupported.
- **`python` opens the Microsoft Store** instead of running Python: the
  `build_exe.bat` script uses the `py` launcher, which avoids this. You can
  also disable the app execution alias in Windows Settings → Apps → Advanced
  app settings → App execution aliases.
- **"X was unexpected at this time" when running `build_exe.bat`:** cmd.exe
  breaks if the **folder path contains parentheses** (e.g. `... (1)\stealth_game`)
  while a script uses `if (...)` blocks. The current `build_exe.bat` avoids
  `if`-blocks entirely (goto-based flow), has no parentheses in its code, and
  uses proper Windows (CRLF) line endings — so just use the latest file. If
  anything ever goes sideways, copy the folder to a simple path like
  `C:\stealthgame` and run from there.
