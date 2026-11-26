#!/usr/bin/env python3
"""Deep logic tests for the game internals (headless)."""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stealth_game as g

pygame.init()
pygame.display.set_mode((g.WIN, g.WIN), g.NOFRAME)

# --- 2048 merge logic (direct line merges) ---
t = g.Game2048()
for line, want in [([2, 2, 4, 4], [4, 8, 0, 0]), ([4, 4, 2, 2], [8, 4, 0, 0]),
                   ([2, 2, 2, 2], [4, 4, 0, 0]), ([0, 2, 2, 0], [4, 0, 0, 0]),
                   ([8, 8, 8, 8], [16, 16, 0, 0])]:
    l = line[:]
    t._merge_into(l)
    assert l == want, (line, l, want)
print("2048 merge: OK")

# --- 2048 full-board moves (tile spawn disabled for determinism) ---
t.add_tile = lambda: None
t.grid = [[2, 2, 4, 4], [4, 4, 2, 2], [2, 2, 4, 4], [4, 4, 2, 2]]
t.move(0, -1)
assert t.grid[0] == [4, 8, 0, 0] and t.grid[1] == [8, 4, 0, 0], t.grid
t.grid = [[2, 2, 4, 4], [4, 4, 2, 2], [2, 2, 4, 4], [4, 4, 2, 2]]
t.move(0, 1)
assert t.grid[0] == [0, 0, 4, 8], t.grid
t.grid = [[2, 0, 0, 0], [2, 0, 0, 0], [4, 0, 0, 0], [4, 0, 0, 0]]
t.move(-1, 0)
assert [t.grid[r][0] for r in range(4)] == [4, 8, 0, 0], t.grid
t.grid = [[2, 0, 0, 0], [2, 0, 0, 0], [4, 0, 0, 0], [4, 0, 0, 0]]
t.move(1, 0)
assert [t.grid[r][0] for r in range(4)] == [0, 0, 4, 8], t.grid
print("2048 directions: OK")

# --- Snake movement, wrap, eating ---
s = g.SnakeGame()
assert s.body == [(4, 4), (3, 4), (2, 4)] and s.dir == (1, 0)
s.update(1 / 60)
assert s.body == [(5, 4), (4, 4), (3, 4)], s.body
s.food = (6, 4)
for _ in range(7):
    s.update(1 / 60)
assert len(s.body) == 4, s.body  # ate the food
s.dir = (1, 0)
s.body = [(7, 4), (6, 4)]
s.food = (0, 4)
s.pending = 0
s.update(1 / 60)
assert s.body[0] == (0, 4), s.body  # wraps around the right edge
print("snake: OK")

# --- Type Rush typing engine ---
tr = g.TypeRushGame()
score_before = tr.score
for ch in tr.word:
    tr.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode=ch))
assert tr.score > score_before and tr.progress == 0  # word completed -> new word
tr2 = g.TypeRushGame()
m0 = tr2.mistakes
tr2.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode="z"))
assert tr2.mistakes == m0 + 1
print("type rush: OK")

# --- Flap: starts with a flap, never dies instantly ---
fl = g.FlapGame()
assert fl.vy == fl.jump * 0.8    # initial flap
for _ in range(20):
    fl.update(1 / 60)
assert not fl.over, "flap died during grace period without input"  # grace covers start
fl.update(1 / 60)
assert fl.vy > fl.jump           # gravity applied
fl.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" "))
assert fl.vy == fl.jump          # space re-jumps
print("flap: OK")

# --- Best scores roundtrip ---
g.save_bests({"1": 7, "4": 12})
bests = g.load_bests()
assert bests.get("1") == 7 and bests.get("4") == 12
print("best scores: OK")
try:
    os.remove(g._best_path())
except OSError:
    pass

# --- All games can render without errors (including new overlay paths) ---
F = {"title": g.font(46, True), "body": g.font(32), "small": g.font(24)}
canvas = pygame.Surface((g.CANVAS, g.CANVAS))
g.draw_menu(canvas, F, None)
pygame.transform.smoothscale(canvas, (g.WIN, g.WIN))
for cls in (g.SnakeGame, g.TypeRushGame, g.Game2048, g.FlapGame):
    gc = cls()
    gc.draw(canvas, F)
    pygame.transform.smoothscale(canvas, (g.WIN, g.WIN))
    gc.over = True
    gc.best = 9
    gc.new_best = True
    gc.draw(canvas, F)  # game-over render path with best score
    pygame.transform.smoothscale(canvas, (g.WIN, g.WIN))
g.draw_paused(canvas, F)  # pause overlay
pygame.transform.smoothscale(canvas, (g.WIN, g.WIN))
print("rendering: OK")
print("ALL LOGIC TESTS PASSED")
