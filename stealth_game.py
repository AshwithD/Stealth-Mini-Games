#!/usr/bin/env python3
"""Stealth Mini Games -- a tiny (~3 cm) menu-driven game collection.

Starts with a 4-option menu:  1 SNAKE  2 TYPE RUSH  3 2048  4 FLAP
Choose with number keys or mouse click. The window is borderless (no title
bar / buttons) and starts at the bottom-left corner.

Controls:
  1-4 / click   start a game       Esc      back to menu / quit
  Q             quit               P       pause / unpause (in a game)
  right-click   quit
  drag (menu)   move the window    T       toggle always-on-top

No sound by design - the game is built for quiet office use.
All games render at a high internal resolution (CANVAS) and are scaled down
smoothly to the small window size, so graphics stay crisp at 3 cm. Best
scores are saved next to the executable in best_scores.json.

Windows 11: run build_exe.bat to produce dist/StealthGame.exe.
"""
import os
import sys
import json
import math
import random
import threading
import time

import pygame

# ----------------------------------------------------------------------
# Configuration -- adjust "pixels_per_cm" so the window is really ~3 cm
# wide on YOUR screen. See README.md for the pixels-per-cm table.
# window_pixels = target_cm * pixels_per_cm
# ----------------------------------------------------------------------
CONFIG = {
    "title": "Mini Games",      # shows in taskbar / alt-tab
    "target_cm": 3.0,           # desired physical size
    "pixels_per_cm": 38,        # tune per monitor (24" 1080p ~ 36, 15.6" ~ 56)
    "always_on_top": False,     # True = keep above other windows (T toggles)
    "fps": 60,
}
WIN = int(round(CONFIG["target_cm"] * CONFIG["pixels_per_cm"]))  # ~114 px
CANVAS = 360                     # internal render resolution (~3x WIN)

# ----------------------------------------------------------------------
# Colors
# ----------------------------------------------------------------------
BG     = (23, 25, 31)
FG     = (236, 239, 246)
DIM    = (120, 128, 140)
ACCENT = (88, 198, 255)
GREEN  = (72, 222, 120)
RED    = (242, 92, 92)
YELLOW = (246, 202, 92)
PANEL  = (38, 42, 52)
FRAME  = (96, 106, 128)

MOVE_KEYS = {
    pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0),
    pygame.K_LEFT: (0, -1), pygame.K_RIGHT: (0, 1),
    pygame.K_w: (-1, 0), pygame.K_s: (1, 0),
    pygame.K_a: (0, -1), pygame.K_d: (0, 1),
}

try:
    NOFRAME = pygame.NOFRAME
except AttributeError:
    NOFRAME = 0x00000008

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002

_FONT_CACHE = {}


def font(size, bold=False):
    """Font helper (pygame Font has no .copy(); cache by size)."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        f = pygame.font.Font(None, size)
        f.set_bold(bold)
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]


# ----------------------------------------------------------------------
# Best scores (saved next to the executable)
# ----------------------------------------------------------------------
def _best_path():
    try:
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
    except Exception:
        base = os.getcwd()
    return os.path.join(base, "best_scores.json")


def load_bests():
    try:
        with open(_best_path()) as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_bests(bests):
    try:
        with open(_best_path(), "w") as fh:
            json.dump(bests, fh)
    except Exception:
        pass


# ----------------------------------------------------------------------
# Window positioning / dragging (Windows)
# ----------------------------------------------------------------------
def _win_rect():
    """Return (left, top) of the window on Windows, else None."""
    if not sys.platform.startswith("win"):
        return None
    try:
        import ctypes

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        user32 = ctypes.windll.user32
        r = RECT()
        user32.GetWindowRect(pygame.display.get_window_handle(), ctypes.byref(r))
        return r.left, r.top
    except Exception:
        return None


def _win_move_to(x, y):
    """Move the window to screen position (x, y) without resizing it."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        user32.SetWindowPos(pygame.display.get_window_handle(), 0,
                            int(x), int(y), 0, 0, SWP_NOSIZE)
    except Exception:
        pass


def set_topmost(flag):
    CONFIG["always_on_top"] = bool(flag)
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        z = -1 if CONFIG["always_on_top"] else -2  # HWND_TOPMOST / NOTOPMOST
        user32.SetWindowPos(pygame.display.get_window_handle(), z,
                            0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE)
    except Exception:
        pass


def move_to_bottom_left():
    """Move the window to the bottom-left corner of the (virtual) screen."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            sy = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            topmost = -1 if CONFIG["always_on_top"] else 0
            user32.SetWindowPos(pygame.display.get_window_handle(), topmost,
                                0, max(0, sy - WIN), 0, 0, SWP_NOSIZE)
            return
        except Exception:
            pass
    else:
        try:
            pygame.display.set_window_position(0, 0)  # best effort
        except Exception:
            pass


def finish(canvas):
    """Framing border drawn on every screen (helps the tiny window stand out)."""
    pygame.draw.rect(canvas, FRAME, (6, 6, CANVAS - 12, CANVAS - 12), 6, border_radius=14)


def draw_over(canvas, F, label, best=None, new_best=False):
    """Clean inset card with the game-over result."""
    card = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    pygame.draw.rect(card, (0, 0, 0, 160), (24, 24, CANVAS - 48, CANVAS - 48),
                     border_radius=24)
    pygame.draw.rect(card, DIM, (24, 24, CANVAS - 48, CANVAS - 48),
                     3, border_radius=24)
    canvas.blit(card, (0, 0))
    t = font(60, True)
    s1 = t.render("OVER", True, RED)
    canvas.blit(s1, ((CANVAS - s1.get_width()) // 2, 66))
    s2 = font(36, True).render(label, True, FG)
    canvas.blit(s2, ((CANVAS - s2.get_width()) // 2, 146))
    if new_best:
        s3 = font(30, True).render(f"NEW BEST {label.split()[-1]}!", True, YELLOW)
    elif best is not None:
        s3 = font(30).render(f"BEST {best}", True, DIM)
    else:
        s3 = None
    if s3 is not None:
        canvas.blit(s3, ((CANVAS - s3.get_width()) // 2, 198))
    s4 = font(24).render("press any key", True, DIM)
    canvas.blit(s4, ((CANVAS - s4.get_width()) // 2, 252))


def draw_paused(canvas, F):
    card = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    pygame.draw.rect(card, (0, 0, 0, 150), (24, 24, CANVAS - 48, CANVAS - 48),
                     border_radius=24)
    pygame.draw.rect(card, FRAME, (24, 24, CANVAS - 48, CANVAS - 48),
                     3, border_radius=24)
    canvas.blit(card, (0, 0))
    t = font(60, True)
    s1 = t.render("PAUSED", True, YELLOW)
    canvas.blit(s1, ((CANVAS - s1.get_width()) // 2, 150))
    s2 = font(26).render("press P to resume", True, DIM)
    canvas.blit(s2, ((CANVAS - s2.get_width()) // 2, 240))


# ----------------------------------------------------------------------
# Game 1: Snake
# ----------------------------------------------------------------------
class SnakeGame:
    KEY = "1"
    NAME = "SNAKE"

    def __init__(self):
        self.cells = 8
        self.cell = 42
        self.ox = 18
        self.oy = 18
        self.reset()

    def reset(self):
        mid = self.cells // 2
        self.body = [(mid, mid), (mid - 1, mid), (mid - 2, mid)]
        self.dir = (1, 0)
        self.pending = 0
        self.food = self._food()
        self.score = 0
        self.t = 0
        self.over = False
        self.done = False
        self.best = 0
        self.new_best = False

    def _food(self):
        free = [(x, y) for x in range(self.cells) for y in range(self.cells)
                if (x, y) not in self.body]
        return random.choice(free) if free else (0, 0)

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            if event.key in MOVE_KEYS:
                dr, dc = MOVE_KEYS[event.key]
                nd = (dc, dr)
                if nd[0] != -self.dir[0] or nd[1] != -self.dir[1]:
                    self.dir = nd
        elif event.type == pygame.MOUSEBUTTONDOWN and self.over:
            self.done = True

    def update(self, dt):
        if self.over:
            return
        self.t += 1
        self.pending -= 1
        if self.pending > 0:
            return
        self.pending = 7
        hx = (self.body[0][0] + self.dir[0]) % self.cells
        hy = (self.body[0][1] + self.dir[1]) % self.cells
        if (hx, hy) in self.body:
            self.over = True
            return
        self.body.insert(0, (hx, hy))
        if (hx, hy) == self.food:
            self.score += 1
            self.food = self._food()
        else:
            self.body.pop()

    def draw(self, canvas, F):
        canvas.fill(BG)
        pygame.draw.rect(canvas, (52, 56, 66),
                         (8, 8, CANVAS - 16, CANVAS - 16), border_radius=16)
        for i, (x, y) in enumerate(self.body):
            cx = self.ox + (x + 0.5) * self.cell
            cy = self.oy + (y + 0.5) * self.cell
            if i == 0:
                pygame.draw.circle(canvas, (120, 240, 160), (cx, cy), 19)
                # direction-aware eyes
                dx, dy = self.dir
                pygame.draw.circle(canvas, BG, (cx + dx * 9 + dy * 5, cy + dy * 9 - dx * 5), 3)
                pygame.draw.circle(canvas, BG, (cx + dx * 9 - dy * 5, cy + dy * 9 + dx * 5), 3)
            else:
                pygame.draw.circle(canvas, (46, 168, 88), (cx, cy), 16)
        fx, fy = self.food
        r = 14 + 3 * math.sin(self.t * 0.12)  # pulsing food
        pygame.draw.circle(canvas, RED,
                           (self.ox + (fx + 0.5) * self.cell,
                            self.oy + (fy + 0.5) * self.cell), r)
        s = font(32).render(f"S {self.score}", True, DIM)
        canvas.blit(s, (14, 10))
        if self.over:
            draw_over(canvas, F, f"{self.NAME} {self.score}", self.best, self.new_best)
        finish(canvas)


# ----------------------------------------------------------------------
# Game 2: Type Rush -- type the word before the timer runs out
# ----------------------------------------------------------------------
WORDS = ["code", "run", "file", "data", "word", "text", "mail", "list",
         "team", "plan", "draft", "note", "web", "app", "test", "play",
         "game", "grid", "map", "chat", "boss", "fish", "book", "page",
         "key", "tag", "link", "sync", "home", "back"]


class TypeRushGame:
    KEY = "2"
    NAME = "TYPE"

    def __init__(self):
        self.reset()

    def reset(self):
        self.pool = WORDS[:]
        random.shuffle(self.pool)
        self.score = 0
        self.combo = 0
        self.mistakes = 0
        self.flash = 0.0
        self.over = False
        self.done = False
        self.best = 0
        self.new_best = False
        self.new_word()

    def new_word(self):
        if not self.pool:
            self.pool = WORDS[:]
            random.shuffle(self.pool)
        self.word = self.pool.pop()
        self.progress = 0
        self.time_left = 1.0

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            ch = (event.unicode or "").lower()
            if len(ch) == 1 and "a" <= ch <= "z":
                if self.progress < len(self.word) and ch == self.word[self.progress]:
                    self.progress += 1
                    self.flash = 0.0
                    if self.progress == len(self.word):
                        self.score += 10 + self.combo
                        self.combo += 1
                        self.new_word()
                else:
                    self.mistakes += 1
                    self.combo = 0
                    self.flash = 0.4
                    if self.mistakes >= 3:
                        self.over = True
        elif event.type == pygame.MOUSEBUTTONDOWN and self.over:
            self.done = True

    def update(self, dt):
        self.flash = max(0.0, self.flash - dt)
        if self.over:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 1.0
            self.mistakes += 1
            self.combo = 0
            self.flash = 0.4
            if self.mistakes >= 3:
                self.over = True

    def draw(self, canvas, F):
        canvas.fill(BG)
        # panel behind the word (structure at tiny sizes)
        pygame.draw.rect(canvas, PANEL, (28, 128, CANVAS - 56, 128), border_radius=20)
        # timer bar
        bar_w = CANVAS - 48
        x0, y0, h = 24, CANVAS - 42, 12
        ratio = max(0.0, min(1.0, self.time_left))
        color = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
        pygame.draw.rect(canvas, (60, 64, 74), (x0, y0, bar_w, h), border_radius=6)
        pygame.draw.rect(canvas, color, (x0, y0, int(bar_w * ratio), h), border_radius=6)
        # score + combo
        s = font(32).render(f"P {self.score}", True, DIM)
        canvas.blit(s, (14, 10))
        if self.combo >= 2:
            c = font(28, True).render(f"x{self.combo}", True, YELLOW)
            canvas.blit(c, (CANVAS - 14 - c.get_width(), 12))
        # mistake dots
        for i in range(3):
            filled = i < self.mistakes
            pygame.draw.circle(canvas, RED if filled else (70, 74, 84),
                               (CANVAS - 24 - i * 30, 24), 11)
        # word, centered, one char per colored tile
        f = font(52, True)
        letters = list(self.word)
        widths = [f.size(ch)[0] for ch in letters]
        total = sum(widths) + 10 * (len(letters) - 1)
        x = (CANVAS - total) // 2
        y = CANVAS // 2 - f.size("A")[1] // 2 - 6
        for i, ch in enumerate(letters):
            if i < self.progress:
                color = GREEN
            elif self.flash > 0 and i == self.progress:
                color = RED
            else:
                color = FG
            txt = f.render(ch, True, color)
            canvas.blit(txt, (x, y))
            x += txt.get_width() + 10
        if self.over:
            draw_over(canvas, F, f"{self.NAME} {self.score}", self.best, self.new_best)
        finish(canvas)


# ----------------------------------------------------------------------
# Game 3: 2048
# ----------------------------------------------------------------------
TILE_COLORS = {
    2: (230, 232, 238), 4: (216, 208, 192), 8: (248, 180, 110),
    16: (246, 142, 98), 32: (240, 112, 92), 64: (234, 82, 72),
    128: (232, 210, 110), 256: (230, 190, 90), 512: (228, 170, 80),
    1024: (226, 150, 70), 2048: (224, 130, 60),
}


class Game2048:
    KEY = "3"
    NAME = "2048"

    def __init__(self):
        self.gap = 10
        self.tile = 64
        self.ox = 16
        self.oy = 48
        self.reset()

    def reset(self):
        self.grid = [[0] * 4 for _ in range(4)]
        self.add_tile()
        self.add_tile()
        self.score = 0
        self.over = False
        self.done = False
        self.best = 0
        self.new_best = False

    def add_tile(self):
        cells = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if not cells:
            return
        r, c = random.choice(cells)
        self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def _merge_into(self, line):
        vals = [v for v in line if v]
        out = []
        i = 0
        while i < len(vals):
            if i + 1 < len(vals) and vals[i] == vals[i + 1]:
                v = vals[i] * 2
                out.append(v)
                self.score += v
                i += 2
            else:
                out.append(vals[i])
                i += 1
        out += [0] * (len(line) - len(out))
        line[:] = out

    def move(self, dr, dc):
        if self.over:
            return
        prev = [row[:] for row in self.grid]
        if dr == -1:
            for c in range(4):
                col = [self.grid[r][c] for r in range(4)]
                self._merge_into(col)
                for r in range(4):
                    self.grid[r][c] = col[r]
        elif dr == 1:
            for c in range(4):
                col = [self.grid[r][c] for r in range(4)]
                col.reverse()
                self._merge_into(col)
                col.reverse()
                for r in range(4):
                    self.grid[r][c] = col[r]
        elif dc == -1:
            for r in range(4):
                self._merge_into(self.grid[r])
        else:
            for r in range(4):
                self.grid[r].reverse()
                self._merge_into(self.grid[r])
                self.grid[r].reverse()
        if self.grid != prev:
            self.add_tile()
            self.check_over()

    def check_over(self):
        if any(0 in row for row in self.grid):
            return
        for r in range(4):
            for c in range(4):
                if c + 1 < 4 and self.grid[r][c] == self.grid[r][c + 1]:
                    return
                if r + 1 < 4 and self.grid[r][c] == self.grid[r + 1][c]:
                    return
        self.over = True

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            if event.key in MOVE_KEYS:
                dr, dc = MOVE_KEYS[event.key]
                self.move(dr, dc)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.over:
            self.done = True

    def update(self, dt):
        pass

    def draw(self, canvas, F):
        canvas.fill(BG)
        for r in range(4):
            for c in range(4):
                x = self.ox + c * (self.tile + self.gap)
                y = self.oy + r * (self.tile + self.gap)
                val = self.grid[r][c]
                if val:
                    pygame.draw.rect(canvas, TILE_COLORS.get(val, (35, 30, 45)),
                                     (x, y, self.tile, self.tile), border_radius=10)
                    f = font(22 if val >= 1000 else 28 if val >= 100 else 34, True)
                    txt = f.render(str(val), True, (40, 40, 50) if val in (2, 4) else FG)
                    canvas.blit(txt, (x + (self.tile - txt.get_width()) // 2,
                                      y + (self.tile - txt.get_height()) // 2))
                else:
                    pygame.draw.rect(canvas, (44, 48, 58),
                                     (x, y, self.tile, self.tile), border_radius=10)
        s = font(32).render(f"P {self.score}", True, DIM)
        canvas.blit(s, (16, 10))
        if self.over:
            draw_over(canvas, F, f"{self.NAME} {self.score}", self.best, self.new_best)
        finish(canvas)


# ----------------------------------------------------------------------
# Game 4: Flap -- tap to keep the dot flying between the pipes
# ----------------------------------------------------------------------
class FlapGame:
    KEY = "4"
    NAME = "FLAP"

    def __init__(self):
        self.bird_w, self.bird_h = 38, 30
        self.gx = 92
        self.gravity = 0.95
        self.jump = -14.0
        self.speed = 3.6
        self.pipe_w = 46
        self.gap = 130
        self.spawn_every = 95
        # pre-render the bird once (rotated copies are cheap)
        self.bird_img = pygame.Surface((self.bird_w + 14, self.bird_h + 14),
                                       pygame.SRCALPHA)
        pygame.draw.ellipse(self.bird_img, YELLOW, self.bird_img.get_rect())
        pygame.draw.ellipse(self.bird_img, (30, 30, 30), (16, 8, 10, 10))
        self.reset()

    def reset(self):
        self.y = CANVAS * 0.42
        self.vy = self.jump * 0.8   # starts with a flap so it never dies instantly
        self.grace = 30             # brief no-collision grace at the start
        self.pipes = []
        self.frame = 0
        self.score = 0
        self.over = False
        self.done = False
        self.best = 0
        self.new_best = False
        self.spawn_timer = 70

    def _new_pipe(self):
        center = random.uniform(self.gap / 2 + 12, CANVAS - self.gap / 2 - 12)
        return {"x": CANVAS + 10, "gap_y": center, "passed": False}

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.vy = self.jump
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.over:
                self.done = True
            else:
                self.vy = self.jump

    def update(self, dt):
        if self.over:
            return
        self.frame += 1
        self.spawn_timer -= 1
        if self.spawn_timer <= 0 and not self.pipes:
            self.pipes.append(self._new_pipe())
            self.spawn_timer = self.spawn_every
        self.y += self.vy
        self.vy += self.gravity
        # pipe movement + scoring always; collisions only after the grace period
        for p in self.pipes:
            p["x"] -= self.speed
            if not p["passed"] and p["x"] + self.pipe_w < self.gx:
                p["passed"] = True
                self.score += 1
        self.pipes = [p for p in self.pipes if p["x"] + self.pipe_w > 0]
        if self.grace > 0:
            self.grace -= 1
            return
        ground = CANVAS - self.bird_h - 20
        if self.y < 8 or self.y > ground:
            self.over = True
            return
        bird = pygame.Rect(self.gx, self.y, self.bird_w, self.bird_h)
        for p in self.pipes:
            top = pygame.Rect(p["x"], 8, self.pipe_w, p["gap_y"] - self.gap / 2 - 8)
            bottom = pygame.Rect(p["x"], p["gap_y"] + self.gap / 2,
                                 self.pipe_w, CANVAS - 8 - (p["gap_y"] + self.gap / 2))
            if top.colliderect(bird) or bottom.colliderect(bird):
                self.over = True
                return

    def draw(self, canvas, F):
        canvas.fill(BG)
        # subtle background dots for texture
        for (dx, dy) in [(58, 66), (300, 88), (170, 46), (320, 180)]:
            pygame.draw.circle(canvas, (52, 56, 66), (dx, dy), 5)
        ground = CANVAS - 20
        pygame.draw.rect(canvas, (44, 48, 58), (12, ground, CANVAS - 24, 8))
        pygame.draw.line(canvas, DIM, (12, ground), (CANVAS - 12, ground), 3)
        for p in self.pipes:
            top_h = p["gap_y"] - self.gap / 2
            bot_y = p["gap_y"] + self.gap / 2
            pygame.draw.rect(canvas, GREEN, (p["x"], 8, self.pipe_w, top_h - 8), border_radius=6)
            pygame.draw.rect(canvas, GREEN, (p["x"], bot_y, self.pipe_w, CANVAS - 8 - bot_y), border_radius=6)
        # bird, tilted by velocity (classic flappy feel)
        angle = max(-25.0, min(90.0, self.vy * 2.4))
        rot = pygame.transform.rotate(self.bird_img, angle)
        canvas.blit(rot, (self.gx - 7, self.y - 7))
        s = font(32).render(f"F {self.score}", True, DIM)
        canvas.blit(s, (14, 10))
        if self.over:
            draw_over(canvas, F, f"{self.NAME} {self.score}", self.best, self.new_best)
        finish(canvas)


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
def menu_buttons():
    m = 24
    g = 20
    bw = (CANVAS - 2 * m - g) // 2
    bh = 98
    labels = [("1", "SNAKE", "snake"), ("2", "TYPE", "type"),
              ("3", "2048", "grid"), ("4", "FLAP", "flap")]
    out = []
    top = 76
    for i, (k, lab, icon) in enumerate(labels):
        col, row = i % 2, i // 2
        x = m + col * (bw + g)
        y = top + row * (bh + g)
        out.append((k, pygame.Rect(x, y, bw, bh), lab, icon))
    return out


def draw_icon(canvas, kind, cx, cy):
    if kind == "snake":
        for i, (dx, dy) in enumerate([(-12, -6), (0, 0), (12, 6)]):
            col = (120, 240, 160) if i == 0 else (46, 168, 88)
            pygame.draw.circle(canvas, col, (cx + dx, cy + dy), 6)
    elif kind == "type":
        t = font(26, True).render("Aa", True, DIM)
        canvas.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2 - 2))
    elif kind == "grid":
        for i in range(2):
            for j in range(2):
                col = [(230, 232, 238), (216, 208, 192),
                       (44, 48, 58), (248, 180, 110)][i * 2 + j]
                pygame.draw.rect(canvas, col,
                                 (cx - 12 + i * 14, cy - 12 + j * 14, 11, 11),
                                 border_radius=3)
    elif kind == "flap":
        pygame.draw.ellipse(canvas, YELLOW, (cx - 12, cy - 8, 24, 16))


def draw_menu(canvas, F, hover):
    canvas.fill(BG)
    t = font(46, True)
    s = t.render("MINI GAMES", True, FG)
    canvas.blit(s, ((CANVAS - s.get_width()) // 2, 14))
    for k, rect, lab, icon in menu_buttons():
        sel = hover is not None and rect.collidepoint(hover)
        pygame.draw.rect(canvas, ACCENT if sel else PANEL, rect, border_radius=16)
        pygame.draw.rect(canvas, FG if sel else DIM, rect, width=4, border_radius=16)
        # number hint
        n = font(22, True).render(k, True, (160, 170, 186) if not sel else BG)
        canvas.blit(n, (rect.x + 14, rect.y + 12))
        # icon + label, centered
        draw_icon(canvas, icon, rect.x + rect.w // 2, rect.y + 34)
        l = font(32, True).render(lab, True, BG if sel else FG)
        canvas.blit(l, (rect.x + (rect.w - l.get_width()) // 2, rect.y + 66))
    h1 = font(24).render("1-4 / CLICK    ESC = QUIT", True, DIM)
    canvas.blit(h1, ((CANVAS - h1.get_width()) // 2, CANVAS - 64))
    h2 = font(22).render("drag to move    right-click quits", True, DIM)
    canvas.blit(h2, ((CANVAS - h2.get_width()) // 2, CANVAS - 36))
    finish(canvas)


# ----------------------------------------------------------------------
# Self-test (headless): plays each game briefly with synthetic input
# ----------------------------------------------------------------------
def _start_selftest():
    def runner():
        time.sleep(0.6)
        def key(k, u=""):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u))
        key(pygame.K_t, "t"); time.sleep(0.2)   # toggle topmost (no-op on linux)
        # 1 Snake
        key(pygame.K_1, "1"); time.sleep(0.4)
        key(pygame.K_p, "p"); time.sleep(0.3)   # pause
        key(pygame.K_p, "p"); time.sleep(0.3)   # unpause
        key(pygame.K_RIGHT); time.sleep(0.2); key(pygame.K_DOWN); time.sleep(0.4)
        key(pygame.K_ESCAPE); time.sleep(0.4)
        # 2 Type Rush
        key(pygame.K_2, "2"); time.sleep(0.3)
        for ch in "abcdefghij":
            key(pygame.K_a, ch); time.sleep(0.15)
        time.sleep(0.4); key(pygame.K_ESCAPE); time.sleep(0.4)
        # 3 2048
        key(pygame.K_3, "3"); time.sleep(0.3)
        for k in (pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN):
            key(k); time.sleep(0.2)
        time.sleep(0.4); key(pygame.K_ESCAPE); time.sleep(0.4)
        # 4 Flap
        key(pygame.K_4, "4"); time.sleep(0.4)
        for _ in range(8):
            key(pygame.K_SPACE, " "); time.sleep(0.25)
        time.sleep(0.5)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=runner, daemon=True).start()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    pygame.init()
    pygame.display.set_caption(CONFIG["title"])
    try:
        screen = pygame.display.set_mode((WIN, WIN), NOFRAME)
    except pygame.error:
        screen = pygame.display.set_mode((WIN, WIN))
    move_to_bottom_left()

    canvas = pygame.Surface((CANVAS, CANVAS))
    F = {"title": font(46, True), "body": font(32), "small": font(24)}
    clock = pygame.time.Clock()

    if os.environ.get("STEALTH_SELFTEST"):
        _start_selftest()

    GAME_CLASSES = {"1": SnakeGame, "2": TypeRushGame, "3": Game2048, "4": FlapGame}
    state, game, hover = "menu", None, None
    paused = False
    dragging = False
    drag_start, win_start = None, None

    def start_drag(pos):
        nonlocal dragging, drag_start, win_start
        start = _win_rect()
        if start is None:
            return
        dragging = True
        drag_start = pos
        win_start = start

    def do_drag(pos):
        if not dragging or win_start is None or drag_start is None:
            return
        _win_move_to(win_start[0] + pos[0] - drag_start[0],
                     win_start[1] + pos[1] - drag_start[1])

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            # right-click quits from anywhere
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                return
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                continue
            # global hotkey
            if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                set_topmost(not CONFIG["always_on_top"])
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                if state != "menu":
                    paused = not paused
                continue

            if state == "menu":
                if event.type == pygame.KEYDOWN:
                    if event.unicode in GAME_CLASSES:
                        game = GAME_CLASSES[event.unicode]()
                        state = event.unicode
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return
                elif event.type == pygame.MOUSEMOTION:
                    hover = event.pos
                    do_drag(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    hit = None
                    for k, rect, _, _ in menu_buttons():
                        if rect.collidepoint(event.pos):
                            hit = k
                            break
                    if hit:
                        game = GAME_CLASSES[hit]()
                        state = hit
                    else:
                        start_drag(event.pos)
            else:
                game.handle(event)

        if state != "menu":
            if not paused:
                game.update(1.0 / CONFIG["fps"])
                if game.done:
                    game, state = None, "menu"
                elif game.over and not getattr(game, "_saved", False):
                    # record best score once, when the game ends
                    game._saved = True
                    bests = load_bests()
                    if game.score > bests.get(state, -1):
                        bests[state] = game.score
                        save_bests(bests)
                        game.new_best = True
                    game.best = bests.get(state, 0)

        if state == "menu":
            draw_menu(canvas, F, hover)
        else:
            game.draw(canvas, F)
            if paused:
                draw_paused(canvas, F)

        scaled = pygame.transform.smoothscale(canvas, (WIN, WIN))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()
    if os.environ.get("STEALTH_SELFTEST"):
        print("SELFTEST OK", flush=True)
