#!/usr/bin/env python3
"""Render every screen at the REAL window size (114 px, ~3 cm) and critique
the rendering programmatically:

- margins / clipping risk (is content touching the window edges?)
- ink coverage (how much is actually drawn - too low = looks empty)
- 1-pixel-thin features (lines/strokes that may vanish at 3 cm)
- text contrast in the score/label area (legibility)

Prints one critique line per screen. Used to drive visual improvements.
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from engine.constants import CANVAS, BG
from engine.renderer import Renderer
from engine.menu import draw_menu, draw_stats
from engine.storage import Store
from engine.games import GAME_CLASSES, GAME_META

WIN = 114  # ~3 cm at 38 px/cm

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "win")
os.makedirs(OUT, exist_ok=True)

pygame.init()
pygame.display.set_mode((WIN, WIN), pygame.NOFRAME)
canvas = pygame.Surface((CANVAS, CANVAS))
R = Renderer((WIN, WIN), CANVAS)
store = Store(os.path.join(os.path.dirname(OUT), ".tmp_screenshots_data.json"))
for k, v in [("1", 24), ("2", 60)]:
    store.record_game(k, v)


def capture(name, draw_fn):
    canvas.fill(BG)
    draw_fn()
    small = pygame.transform.smoothscale(canvas, (WIN, WIN))
    pygame.image.save(small, os.path.join(OUT, name))
    return small


def d(px):
    return abs(px[0] - BG[0]) + abs(px[1] - BG[1]) + abs(px[2] - BG[2])


def analyze(name, img):
    w, h = img.get_size()
    minx, miny, maxx, maxy = w, h, -1, -1
    ink = 0
    for y in range(h):
        for x in range(w):
            if d(img.get_at((x, y))) > 30:
                ink += 1
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    ink_pct = 100.0 * ink / (w * h)

    # 1-pixel-wide runs (rows) - informational (continuous intentional lines)
    lines1px = 0
    for y in range(h):
        run = 0
        for x in range(w):
            if d(img.get_at((x, y))) > 30:
                run += 1
            else:
                if run == 1:
                    lines1px += 1
                run = 0
        if run == 1:
            lines1px += 1

    # isolated ink pixels (specks) - the real vanish/glitch risk at 3 cm
    specks = 0
    for y in range(h):
        for x in range(w):
            if d(img.get_at((x, y))) > 30:
                neighbors = []
                if y > 0:
                    neighbors.append(d(img.get_at((x, y - 1))) <= 30)
                if y < h - 1:
                    neighbors.append(d(img.get_at((x, y + 1))) <= 30)
                if x > 0:
                    neighbors.append(d(img.get_at((x - 1, y))) <= 30)
                if x < w - 1:
                    neighbors.append(d(img.get_at((x + 1, y))) <= 30)
                if neighbors and all(neighbors):
                    specks += 1

    # text contrast: label region for normal screens, whole image for overlays
    if name.endswith("_over"):
        x0, y0, x1, y1 = 0, 0, w, h
    else:
        x0, y0, x1, y1 = 0, 0, 70, 24
    best = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            best = max(best, d(img.get_at((x, y))))

    margins = (minx, miny, w - 1 - maxx, h - 1 - maxy)
    issues = []
    if minx <= 1 or miny <= 1 or maxx >= w - 2 or maxy >= h - 2:
        issues.append("CLIPPING RISK: content at window edge")
    if specks > 10:
        issues.append(f"isolated speck pixels: {specks} (glitch risk)")
    if lines1px > 600:
        issues.append(f"many 1px-wide lines: {lines1px} (thicken borders)")
    if ink_pct < 8:
        issues.append("low ink coverage (may look empty)")
    if best < 100:
        issues.append("weak text contrast")
    status = "OK" if not issues else "; ".join(issues)
    print(f"{name:22s} ink={ink_pct:5.1f}%  margins={margins}  "
          f"contrast={best:4d}  specks={specks:3d}  lines1px={lines1px:4d}  -> {status}")
    return not issues


screens = {}
screens["menu"] = capture("menu.png",
                          lambda: draw_menu(canvas, R, GAME_META, (90, 90), store))
screens["stats"] = capture("stats.png",
                           lambda: draw_stats(canvas, R, store, GAME_META))

for key_, name, label, icon, desc in GAME_META:
    g = GAME_CLASSES[key_]()
    for _ in range(20):
        g.update(1 / 60)
    if key_ == "4":
        p = g._new_pipe()
        p["x"] = 210
        g.pipes.append(p)
    screens[name] = capture(f"{name}.png", lambda g=g: g.draw(canvas, R))
    g.over = True
    g.best = 99
    g.new_best = True
    screens[f"{name}_over"] = capture(
        f"{name}_over.png", lambda g=g: g.draw(canvas, R))

print(f"\nwindow = {WIN}px (~3 cm), canvas = {CANVAS}px, scale = {CANVAS / WIN:.2f}x")
ok = True
for name, img in screens.items():
    ok = analyze(name, img) and ok
print("ANALYZER:", "ALL SCREENS OK" if ok else "ISSUES FOUND (see above)")
sys.exit(0 if ok else 1)
