#!/usr/bin/env python3
"""Render each game screen to PNG (headless) and print pixel-color stats so
the tiny rendering can be verified programmatically. Saves screenshots into
screenshots/ so the user can view them too."""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stealth_game as g

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(OUT, exist_ok=True)

pygame.init()
pygame.display.set_mode((g.WIN, g.WIN), g.NOFRAME)
F = {"title": g.font(48, True), "body": g.font(30), "small": g.font(24)}
canvas = pygame.Surface((g.CANVAS, g.CANVAS))


def save(name, draw_fn):
    canvas.fill(g.BG)
    draw_fn()
    path = os.path.join(OUT, name)
    pygame.image.save(canvas, path)
    return path


def count_near(img, color, tol=45):
    w, h = img.get_size()
    n = 0
    cr, cg, cb = color
    for x in range(0, w, 2):
        for y in range(0, h, 2):
            p = img.get_at((x, y))
            if abs(p.r - cr) <= tol and abs(p.g - cg) <= tol and abs(p.b - cb) <= tol:
                n += 1
    return n * 4  # sampled every 2px -> x4 estimate


shots = {}

shots["01_menu.png"] = save("01_menu.png", lambda: g.draw_menu(canvas, F, None))

snake = g.SnakeGame()
shots["02_snake.png"] = save("02_snake.png", lambda: snake.draw(canvas, F))
snake.over = True
shots["03_snake_over.png"] = save("03_snake_over.png", lambda: snake.draw(canvas, F))

tr = g.TypeRushGame()
tr.progress = 2  # partially typed for a more representative shot
shots["04_type.png"] = save("04_type.png", lambda: tr.draw(canvas, F))
tr.over = True
shots["05_type_over.png"] = save("05_type_over.png", lambda: tr.draw(canvas, F))

g2048 = g.Game2048()
shots["06_2048.png"] = save("06_2048.png", lambda: g2048.draw(canvas, F))
g2048.over = True
shots["07_2048_over.png"] = save("07_2048_over.png", lambda: g2048.draw(canvas, F))

fl = g.FlapGame()
pipe = fl._new_pipe()
pipe["x"] = 200  # on-screen position for the screenshot
fl.pipes.append(pipe)
shots["08_flap.png"] = save("08_flap.png", lambda: fl.draw(canvas, F))
fl.over = True
shots["09_flap_over.png"] = save("09_flap_over.png", lambda: fl.draw(canvas, F))

# --- verify each screenshot has the expected content ---
checks = [
    ("01_menu.png", [("white text", g.FG, 150), ("panel buttons", g.PANEL, 2000)]),
    ("02_snake.png", [("snake body", (46, 168, 88), 400),
                       ("snake head", (120, 240, 160), 250),
                       ("food red", g.RED, 100)]),
    ("04_type.png", [("letters", g.FG, 200), ("timer green", g.GREEN, 100)]),
    ("06_2048.png", [("tiles", (230, 232, 238), 500)]),
    ("08_flap.png", [("bird yellow", g.YELLOW, 200), ("pipes green", g.GREEN, 2000)]),
    ("03_snake_over.png", [("OVER red", g.RED, 800)]),
]
print(f"window = {g.WIN}px   canvas = {g.CANVAS}px\n")
ok = True
for name in sorted(shots):
    img = pygame.image.load(os.path.join(OUT, name)).convert()
    print(f"{name}: {img.get_size()}")
for name, expected in checks:
    img = pygame.image.load(os.path.join(OUT, name)).convert()
    for label, color, min_pixels in expected:
        n = count_near(img, color)
        status = "OK " if n >= min_pixels else "LOW"
        if n < min_pixels:
            ok = False
        print(f"  {name} [{label}] ~{n}px  (need >= {min_pixels})  {status}")
print("\nSCREENSHOT CHECKS:", "PASSED" if ok else "FAILED")
sys.exit(0 if ok else 1)
