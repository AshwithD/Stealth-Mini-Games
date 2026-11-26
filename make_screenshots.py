#!/usr/bin/env python3
"""Render each screen to PNG (headless) and verify expected pixel content.

Captures: menu, stats, all 7 games (play + game-over), drag behaviour is
not pixel-verifiable here but is covered by the logic/smoke tests.
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from engine.constants import CANVAS
from engine.renderer import Renderer
from engine.storage import Store
from engine.menu import draw_menu, draw_stats
from engine.games import GAME_CLASSES, GAME_META

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(OUT, exist_ok=True)

pygame.init()
pygame.display.set_mode((114, 114), pygame.NOFRAME)
canvas = pygame.Surface((CANVAS, CANVAS))
R = Renderer((114, 114), CANVAS)
store = Store(os.path.join(os.path.dirname(OUT), ".tmp_screenshots_data.json"))
for k, v in [("1", 24), ("2", 60), ("3", 320), ("4", 9), ("5", 6),
             ("6", 11), ("7", 180)]:
    store.record_game(k, v, won=(k in ("5", "7")), higher=(k != "5"))


def save(name, draw_fn):
    canvas.fill((14, 16, 20))
    draw_fn()
    path = os.path.join(OUT, name)
    pygame.image.save(canvas, path)
    return path


shots = {}
shots["01_menu.png"] = save("01_menu.png",
                            lambda: draw_menu(canvas, R, GAME_META,
                                              (90, 90), store))
shots["02_stats.png"] = save("02_stats.png",
                             lambda: draw_stats(canvas, R, store, GAME_META))

for idx, (key_, name, label, icon, desc) in enumerate(GAME_META):
    cls = GAME_CLASSES[key_]
    g = cls()
    # advance a few frames so screens show live state
    for _ in range(20):
        g.update(1 / 60)
    if key_ == "4":  # put a pipe on screen for a representative flap shot
        p = g._new_pipe()
        p["x"] = 210
        g.pipes.append(p)
    shots[f"{idx + 3:02d}_{name.lower()}.png"] = save(
        f"{idx + 3:02d}_{name.lower()}.png",
        lambda g=g: g.draw(canvas, R))
    g.over = True
    g.best = 99
    g.new_best = True
    shots[f"{idx + 3:02d}_{name.lower()}_over.png"] = save(
        f"{idx + 3:02d}_{name.lower()}_over.png",
        lambda g=g: g.draw(canvas, R))


def count_near(img, color, tol=45):
    w, h = img.get_size()
    n = 0
    cr, cg, cb = color
    for x in range(0, w, 2):
        for y in range(0, h, 2):
            p = img.get_at((x, y))
            if abs(p.r - cr) <= tol and abs(p.g - cg) <= tol and abs(p.b - cb) <= tol:
                n += 1
    return n * 4


checks = [
    ("01_menu.png", [((240, 242, 248), 150), ((26, 30, 38), 2000),
                     ((238, 76, 62), 80)]),
    ("02_stats.png", [((240, 242, 248), 150), ((36, 64, 82), 500)]),
    ("03_snake.png", [((46, 168, 88), 300), ((238, 76, 62), 60)]),
    ("03_snake_over.png", [((238, 76, 62), 500)]),
    # type: timer bar is GREEN at full, letters are FG on PANEL
    ("04_type.png", [((240, 242, 248), 150), ((72, 222, 120), 80)]),
    # 2048 initial tiles are 2 (light); 4 only spawns 10% of the time
    ("05_2048.png", [((230, 232, 238), 200), ((38, 42, 52), 100)]),
    # flap: green pipe + yellow bird
    ("06_flap.png", [((72, 222, 120), 300), ((246, 202, 92), 80)]),
    ("07_mem.png", [((38, 42, 52), 500), ((30, 34, 44), 200)]),
    # reaction: yellow target + white score text
    ("08_react.png", [((246, 202, 92), 80), ((240, 242, 248), 60)]),
    # breakout: orange bricks + ACCENT paddle (88,198,255)
    ("09_break.png", [((248, 180, 110), 150), ((88, 198, 255), 60)]),
]

print(f"window = 114px   canvas = {CANVAS}px\n")
ok = True
for name in sorted(shots):
    img = pygame.image.load(os.path.join(OUT, name)).convert()
    print(f"{name}: {img.get_size()}")
for name, expected in checks:
    if name not in shots:
        continue
    img = pygame.image.load(os.path.join(OUT, name)).convert()
    for color, min_pixels in expected:
        n = count_near(img, color)
        status = "OK " if n >= min_pixels else "LOW"
        if n < min_pixels:
            ok = False
        print(f"  {name} #{color} ~{n}px (need >= {min_pixels})  {status}")
print("\nSCREENSHOT CHECKS:", "PASSED" if ok else "FAILED")
sys.exit(0 if ok else 1)
