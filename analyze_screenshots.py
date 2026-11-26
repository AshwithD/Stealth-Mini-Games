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
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stealth_game as g

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "win")
os.makedirs(OUT, exist_ok=True)

pygame.init()
pygame.display.set_mode((g.WIN, g.WIN), g.NOFRAME)
canvas = pygame.Surface((g.CANVAS, g.CANVAS))
F = {"title": g.font(48, True), "body": g.font(30), "small": g.font(24)}
BG = g.BG


def capture(name, draw_fn):
    canvas.fill(BG)
    draw_fn()
    small = pygame.transform.smoothscale(canvas, (g.WIN, g.WIN))
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
screens["menu"] = capture("menu.png", lambda: g.draw_menu(canvas, F, None))

snake = g.SnakeGame()
screens["snake"] = capture("snake.png", lambda: snake.draw(canvas, F))
snake.over = True
screens["snake_over"] = capture("snake_over.png", lambda: snake.draw(canvas, F))

tr = g.TypeRushGame()
tr.progress = 2
screens["type"] = capture("type.png", lambda: tr.draw(canvas, F))
tr.over = True
screens["type_over"] = capture("type_over.png", lambda: tr.draw(canvas, F))

g2048 = g.Game2048()
screens["2048"] = capture("2048.png", lambda: g2048.draw(canvas, F))
g2048.over = True
screens["2048_over"] = capture("2048_over.png", lambda: g2048.draw(canvas, F))

fl = g.FlapGame()
pipe = fl._new_pipe()
pipe["x"] = 200
fl.pipes.append(pipe)
screens["flap"] = capture("flap.png", lambda: fl.draw(canvas, F))
fl.over = True
screens["flap_over"] = capture("flap_over.png", lambda: fl.draw(canvas, F))

print(f"\nwindow = {g.WIN}px (~3 cm), canvas = {g.CANVAS}px, scale = {g.CANVAS / g.WIN:.2f}x")
ok = True
for name, img in screens.items():
    ok = analyze(name, img) and ok
print("ANALYZER:", "ALL SCREENS OK" if ok else "ISSUES FOUND (see above)")
sys.exit(0 if ok else 1)
