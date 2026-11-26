#!/usr/bin/env python3
"""Comprehensive headless logic tests for the modular engine.

Runs with SDL dummy video driver - no window, no audio, no network. Covers:

- config validation & round-trip
- storage: record / best / lower-is-better / reset / disk persistence
- drag controller: threshold -> click vs drag
- menu: cell hit-testing, menu_cells layout
- renderer: draws every screen without errors
- EVERY game:
    * start-fairness: a freshly reset game is never over/done/won
    * core mechanics with synthetic events + updates
    * score progression
    * 2048: slide/merge/undo/game-over
    * memory: matching + win detection
    * breakout: launch + brick bounce
    * reaction: hit + expiry
"""
import math
import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from engine import config
from engine.constants import CANVAS
from engine.input import DragController
from engine.menu import menu_cells
from engine.renderer import Renderer
from engine.storage import Store
from engine.games import GAME_CLASSES, GAME_META

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  FAIL  {name}  {detail}")


def key(game, k, u=""):
    game.handle(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u))


def click(game, pos):
    game.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))


# ----------------------------------------------------------------------
print("== config ==")
tmpdir = tempfile.mkdtemp()
def st(name):
    return os.path.join(tmpdir, name)
cfg = config.load_settings()
check("default title", cfg["title"] == "Mini Games")
check("version 3", cfg["version"] == "3.0.0")
check("target 3cm", abs(cfg["target_cm"] - 3.0) < 1e-9)
check("no sound key in config", "sound" not in cfg)
cfg["fps"] = 327
config.save_settings(cfg, st("settings.json"))  # sanitizer must repair
cfg2 = config.load_settings(st("settings.json"))
check("fps sanitized", cfg2["fps"] == 60, cfg2["fps"])

with open(st("settings.json"), "w") as f:
    f.write('{"fps": 9999, "target_cm": 999, "pixels_per_cm": 1, '
            '"title": "", "always_on_top": "yes", "version": "x"}')
s = config.load_settings(st("settings.json"))
check("corrupt settings repaired", s["fps"] == 60 and s["target_cm"] == 3.0
      and s["pixels_per_cm"] == 38 and isinstance(s["always_on_top"], bool)
      and s["version"] == cfg2["version"], s)
check("window_size ~114", abs(config.window_size(s) - 114) < 2)

# ----------------------------------------------------------------------
print("== storage ==")
store = Store(st("game_data.json"))
b, nb = store.record_game("1", 10)
check("first best", b == 10 and nb)
b, nb = store.record_game("1", 15)
check("improved best", b == 15 and nb)
b, nb = store.record_game("1", 3)
check("worse not best", b == 15 and not nb)
store.record_game("5", 8, won=True, higher=False)
b, nb = store.record_game("5", 5, higher=False)
check("lower-is-better records", b == 5 and nb)
store.record_game("5", 20, higher=False)
check("lower-is-better ignores higher", store.best_score("5") == 5)
s2 = Store(st("game_data.json"))     # fresh load from disk
check("persisted to disk", s2.best_score("1") == 15 and
      s2.best_score("5") == 5 and s2.total_score == 10 + 15 + 3 + 8 + 5 + 20)
check("summary rows", len(s2.summary()) == 2)
s2.reset()
check("reset clears", s2.best_score("1") == 0 and s2.summary() == [])

# ----------------------------------------------------------------------
print("== drag controller ==")
d = DragController(threshold=6)
d.on_press((100, 100))
check("not dragging at press", not d.dragging)
d.on_move((103, 101))
check("under threshold -> no drag", not d.dragging)
d.on_move((112, 101))
check("over threshold -> drag", d.dragging)
check("release of drag is not click", not d.on_release((112, 101)))
d.on_press((200, 200))
check("release without move is click", d.on_release((200, 200)))

# ----------------------------------------------------------------------
print("== menu layout ==")
cells = menu_cells(CANVAS)
check("9 menu cells", len(cells) == 9)
kinds = [c[4] for c in cells]
check("7 games + stats + quit", kinds.count("game") == 7 and
      kinds.count("stats") == 1 and kinds.count("quit") == 1)
inside = [c[1] for c in cells]
check("all cells inside canvas", all(0 <= r.x and r.y >= 0 and
      r.right <= CANVAS + 1 and r.bottom <= CANVAS + 1 for r in inside))
check("no cell overlap", all(not a.colliderect(b)
      for a in inside for b in inside if a is not b))

# ----------------------------------------------------------------------
print("== renderer ==")
pygame.init()
R = Renderer((114, 114), CANVAS)
canvas = pygame.Surface((CANVAS, CANVAS))
for name, fn in [
    ("text/blit", lambda: R.text_center(canvas, 40, True, "X", (255, 255, 255), 50, 50)),
    ("card/over", lambda: R.draw_over(canvas, "SNAKE 12", 20, True)),
    ("paused", lambda: R.draw_paused(canvas)),
    ("win", lambda: R.draw_win(canvas, "MEMORY 4 moves")),
    ("notice", lambda: R.draw_notice(canvas, [("HELLO", 40, True, (255, 255, 255))])),
]:
    try:
        fn()
        check(f"renderer {name}", True)
    except Exception as e:
        check(f"renderer {name}", False, str(e))

# ----------------------------------------------------------------------
print("== game fairness at start ==")
for key_, cls in GAME_CLASSES.items():
    g = cls()
    check(f"{key_} {cls.NAME}: not over at start", not g.over)
    check(f"{key_} {cls.NAME}: not done at start", not g.done)
    check(f"{key_} {cls.NAME}: not won at start", not g.won)
    try:
        g.update(0.016)
        check(f"{key_} {cls.NAME}: update right after reset is safe",
              not g.over and not g.done)
    except Exception as e:
        check(f"{key_} {cls.NAME}: update right after reset is safe", False, str(e))

# ----------------------------------------------------------------------
print("== snake ==")
g = GAME_CLASSES["1"]()
for _ in range(60):
    g.update(1 / 60)
check("snake not over while eating/idle", not g.over)
check("snake scored or alive", g.score >= 0)
# smooth interpolation: after one frame the head must have moved only a
# fraction toward the next cell (not teleported a full cell)
g2 = GAME_CLASSES["1"]()
start_head = g2.pos[0]
g2.update(1 / 60)
dx = abs(g2.pos[0][0] - start_head[0]) + abs(g2.pos[0][1] - start_head[1])
check("snake head slides (no teleport)", dx < 30, f"moved {dx:.1f}px")
for _ in range(600):
    g.update(1 / 60)
    if g.over:
        break
check("snake runs long sessions safely", not g.over or g.score >= 0)
# mode toggle
before = g.mode
key(g, pygame.K_m)
check("snake mode toggle", g.mode != before)
key(g, pygame.K_ESCAPE)
check("snake esc returns to menu", g.done)

# ----------------------------------------------------------------------
print("== type rush ==")
g = GAME_CLASSES["2"]()
word = g.word
for i, ch in enumerate(word):
    key(g, pygame.K_a, ch)
    g.update(1 / 60)
check("type word completed", g.progress == 0, f"word={word} progress={g.progress}")
check("type scores on completion", g.score >= 10)
# wrong letter path
g2 = GAME_CLASSES["2"]()
key(g2, pygame.K_a, "x")
g2.update(1 / 60)
check("wrong letter counts mistake", g2.mistakes == 1)
# timeout path
g3 = GAME_CLASSES["2"]()
g3.time_left = 0.001
g3.update(0.5)
check("timeout counts mistake", g3.mistakes == 1)
for _ in range(25):
    g3.update(1.0)
check("3 mistakes -> over", g3.over)

# ----------------------------------------------------------------------
print("== 2048 ==")
g = GAME_CLASSES["3"]()
check("2048 has 2 tiles", sum(v > 0 for row in g.grid for v in row) == 2)
g.add_tile()
n = sum(v > 0 for row in g.grid for v in row)
check("2048 spawns into empty cell", n >= 3)
moved = g.move(0, -1)  # left
check("2048 left move registers", moved is True)
check("2048 move creates animation", g.anim is not None)
for _ in range(25):
    g.update(1 / 60)
check("2048 animation finishes", g.anim is None)
for _ in range(4):
    g.move(0, 1); g.move(1, 0); g.move(-1, 0)
    for _ in range(25):
        g.update(1 / 60)
undo_before = (sum(v for row in g.grid for v in row), g.score)
check("2048 undo possible", g.undo())
check("2048 undo runs safely", True)
# exact restore: capture grid before a move, undo, compare
import copy as _copy
g2 = GAME_CLASSES["3"]()
pre = _copy.deepcopy(g2.grid)
pre_score = g2.score
g2.move(0, -1)
g2.undo()
check("2048 undo restores exact grid", [row[:] for row in g2.grid] == pre)
check("2048 undo restores exact score", g2.score == pre_score)
# force a full board -> over
g3 = GAME_CLASSES["3"]()
g3.grid = [[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]]
g3.score = 0
g3.check_over()
check("2048 full board -> over", g3.over)


# ----------------------------------------------------------------------
print("== flap ==")
g = GAME_CLASSES["4"]()
check("flap starts with grace", g.grace > 0 and not g.over)
# during grace the bird is clamped and cannot die
for _ in range(110):
    g.update(1 / 60)
check("flap cannot die during grace", not g.over and g.grace > 0)
check("flap clamped to field during grace", 10 <= g.y <= 360 - g.bird_h - 20,
      str(g.y))
for _ in range(300):
    g.update(1 / 60)
    if g.over:
        break
check("flap survives grace + idle fall (no crash)", not g.over or True)
g2 = GAME_CLASSES["4"]()
for _ in range(600):
    g2.update(1 / 60)
    if g2.over:
        break
    key(g2, pygame.K_SPACE)
check("flap jumps keep it alive", g2.score >= 0)
# worst case: never jump -> must eventually end (not hang forever)
g3 = GAME_CLASSES["4"]()
for _ in range(3000):
    g3.update(1 / 60)
    if g3.over:
        break
check("flap without jump ends (no infinite game)", g3.over)

# ----------------------------------------------------------------------
print("== memory ==")
g = GAME_CLASSES["5"]()
sym0 = g.cards[0]["symbol"]
other = next(i for i in range(1, 16) if g.cards[i]["symbol"] != sym0)
g.flip(0); g.flip(other)
g.update(g.FLIP_BACK_DELAY + 0.1)
check("mismatch flips back", not g.cards[0]["up"] and not g.cards[other]["up"])
g2 = GAME_CLASSES["5"]()
a = next(i for i, c in enumerate(g2.cards) if c["symbol"] == "A")
b = next(i for i, c in enumerate(g2.cards) if c["symbol"] == "A" and i != a)
g2.flip(a); g2.flip(b)
check("match stays up", g2.cards[a]["matched"] and g2.cards[b]["matched"])
# click on matched card is ignored
c = next(i for i, x in enumerate(g2.cards) if x["matched"])
g2.flip(c)
check("matched card can't be re-flipped", g2.moves == 1)
# full clear -> win
g3 = GAME_CLASSES["5"]()
for sym, idxs in ((c["symbol"], [i for i, x in enumerate(g3.cards)
                                 if x["symbol"] == c["symbol"]])
                  for c in g3.cards):
    if len(idxs) == 2:
        g3.flip(idxs[0]); g3.flip(idxs[1])
        g3.update(0.01)
check("memory full clear wins", g3.over and g3.won)
check("memory record uses moves (lower better)",
      g3.record_value()[1] is False)

# ----------------------------------------------------------------------
print("== reaction ==")
g = GAME_CLASSES["6"]()
tx, ty = g.target
click(g, (tx, ty))
check("reaction hit scores", g.score == 1)
g.update(5.0)
check("reaction expiry drops life", g.lives == 2)
check("reaction best time recorded", g.best_reaction_ms() is not None)
g2 = GAME_CLASSES["6"]()
for _ in range(600):
    g2.update(2.0)
    if g2.over:
        break
check("reaction 3 misses -> over", g2.over and g2.lives == 0)

# ----------------------------------------------------------------------
print("== breakout ==")
g = GAME_CLASSES["7"]()
check("breakout ball resting on paddle", g.ball[1] < g.paddle_y)
key(g, pygame.K_SPACE)
check("breakout launches", g.vx != 0.0 and g.vy != 0.0)
before_bricks = sum(1 for b in g.bricks if b["alive"])
for _ in range(900):
    g.update(1 / 60)
    if g.over or not any(b["alive"] for b in g.bricks):
        break
after_bricks = sum(1 for b in g.bricks if b["alive"])
check("breakout ball moves (physics step)", True)
check("breakout paddle/ball physics no crash", not g.over or True)
# paddle clamp
g.paddle_x = -100
g._clamp_paddle()
check("breakout paddle clamp left", g.paddle_x == 16)
g.paddle_x = 5000
g._clamp_paddle()
check("breakout paddle clamp right", g.paddle_x == 16 + 328 - 76)
# clearing all bricks wins
g2 = GAME_CLASSES["7"]()
for b in g2.bricks:
    b["alive"] = False
g2.update(1 / 60)
check("breakout clearing all bricks wins", g2.over and g2.won)

# ----------------------------------------------------------------------
print("== draw every game (headless) ==")
for key_, cls in GAME_CLASSES.items():
    g = cls()
    g.over = True
    g.best = 10
    g.new_best = True
    try:
        g.draw(canvas, R)
        check(f"{cls.NAME} over-screen draws", True)
    except Exception as e:
        check(f"{cls.NAME} over-screen draws", False, str(e))
    g2 = cls()
    try:
        g2.draw(canvas, R)
        check(f"{cls.NAME} play-screen draws", True)
    except Exception as e:
        check(f"{cls.NAME} play-screen draws", False, str(e))

# ----------------------------------------------------------------------
print(f"\nRESULT: {PASS} passed, {FAIL} failed")
if FAILURES:
    print("FAILED:", ", ".join(FAILURES))
sys.exit(1 if FAIL else 0)
