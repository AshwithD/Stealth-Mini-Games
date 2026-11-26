#!/usr/bin/env python3
"""Stealth Mini Games -- a tiny (~3 cm) menu-driven game collection.

Starts with a 4-option menu:  1 SNAKE  2 TYPE RUSH  3 2048  4 FLAP
Choose with number keys or mouse click. The window is borderless (no title
bar / buttons) and automatically positions itself at the bottom-left corner.

All games render at a high internal resolution (CANVAS) and are scaled down
smoothly to the small window size, so graphics stay crisp at 3 cm.

Windows 11: run build_exe.bat to produce dist/StealthGame.exe.
Quit the app with Esc or Q (there is no window chrome to close it).
"""
import os
import sys
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
    "always_on_top": False,     # True = keep above other windows
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

_FONT_CACHE = {}


def font(size, bold=False):
    """Font helper (pygame Font has no .copy(); cache by size)."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        f = pygame.font.Font(None, size)
        f.set_bold(bold)
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]


def move_to_bottom_left():
    """Move the window to the bottom-left corner of the (virtual) screen."""
    try:
        if sys.platform.startswith("win"):
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = pygame.display.get_window_handle()
            sy = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            topmost = -1 if CONFIG["always_on_top"] else 0
            user32.SetWindowPos(hwnd, topmost, 0, max(0, sy - WIN), 0, 0, 0)
        else:
            try:
                pygame.display.set_window_position(0, 0)  # best effort
            except Exception:
                pass
    except Exception:
        pass


def draw_over(canvas, F, label):
    """Semi-transparent game-over overlay."""
    overlay = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    canvas.blit(overlay, (0, 0))
    t = font(64, True)
    s1 = t.render("OVER", True, RED)
    canvas.blit(s1, ((CANVAS - s1.get_width()) // 2, CANVAS // 3))
    s2 = font(34, True).render(label, True, FG)
    canvas.blit(s2, ((CANVAS - s2.get_width()) // 2, CANVAS // 3 + s1.get_height() + 10))
    s3 = font(26).render("press any key", True, DIM)
    canvas.blit(s3, ((CANVAS - s3.get_width()) // 2, CANVAS - 54))


# ----------------------------------------------------------------------
# Game 1: Snake
# ----------------------------------------------------------------------
class SnakeGame:
    KEY = "1"
    NAME = "SNAKE"

    def __init__(self):
        self.cells = 10
        self.cell = 33
        self.ox = 15
        self.oy = 15
        self.reset()

    def reset(self):
        mid = self.cells // 2
        self.body = [(mid, mid), (mid - 1, mid), (mid - 2, mid)]
        self.dir = (1, 0)
        self.pending = 0
        self.food = self._food()
        self.score = 0
        self.over = False
        self.done = False

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
        pygame.draw.rect(canvas, (52, 56, 66), (8, 8, CANVAS - 16, CANVAS - 16), border_radius=16)
        for i, (x, y) in enumerate(self.body):
            if i == 0:
                pygame.draw.circle(canvas, (120, 240, 160),
                                   (self.ox + (x + 0.5) * self.cell,
                                    self.oy + (y + 0.5) * self.cell), 12)
            else:
                pygame.draw.circle(canvas, (46, 168, 88),
                                   (self.ox + (x + 0.5) * self.cell,
                                    self.oy + (y + 0.5) * self.cell), 10)
        fx, fy = self.food
        pygame.draw.circle(canvas, RED,
                           (self.ox + (fx + 0.5) * self.cell,
                            self.oy + (fy + 0.5) * self.cell), 12)
        s = font(30).render(f"S {self.score}", True, DIM)
        canvas.blit(s, (14, 10))
        if self.over:
            draw_over(canvas, F, f"{self.NAME}  {self.score}")


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
        # timer bar
        bar_w = CANVAS - 48
        x0, y0, h = 24, CANVAS - 42, 12
        ratio = max(0.0, min(1.0, self.time_left))
        color = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
        pygame.draw.rect(canvas, (60, 64, 74), (x0, y0, bar_w, h), border_radius=6)
        pygame.draw.rect(canvas, color, (x0, y0, int(bar_w * ratio), h), border_radius=6)
        # score
        s = font(30).render(f"P {self.score}", True, DIM)
        canvas.blit(s, (14, 10))
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
        y = CANVAS // 2 - f.size("A")[1] // 2 - 10
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
            draw_over(canvas, F, f"{self.NAME}  {self.score}")


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
        s = font(30).render(f"P {self.score}", True, DIM)
        canvas.blit(s, (16, 10))
        if self.over:
            draw_over(canvas, F, f"{self.NAME}  {self.score}")


# ----------------------------------------------------------------------
# Game 4: Flap -- tap to keep the dot flying between the pipes
# ----------------------------------------------------------------------
class FlapGame:
    KEY = "4"
    NAME = "FLAP"

    def __init__(self):
        self.bird_w, self.bird_h = 38, 30
        self.gx = 92
        self.gravity = 1.1
        self.jump = -15.5
        self.speed = 4.0
        self.pipe_w = 46
        self.gap = 130
        self.spawn_every = 110
        self.reset()

    def reset(self):
        self.y = CANVAS * 0.4
        self.vy = 0.0
        self.pipes = []
        self.frame = 0
        self.score = 0
        self.over = False
        self.done = False
        self.spawn_timer = 40

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
        ground = CANVAS - self.bird_h - 12
        if self.y < 0 or self.y > ground:
            self.over = True
            return
        bird = pygame.Rect(self.gx, self.y, self.bird_w, self.bird_h)
        for p in self.pipes:
            p["x"] -= self.speed
            if not p["passed"] and p["x"] + self.pipe_w < self.gx:
                p["passed"] = True
                self.score += 1
            top = pygame.Rect(p["x"], 0, self.pipe_w, p["gap_y"] - self.gap / 2)
            bottom = pygame.Rect(p["x"], p["gap_y"] + self.gap / 2,
                                 self.pipe_w, CANVAS - (p["gap_y"] + self.gap / 2))
            if top.colliderect(bird) or bottom.colliderect(bird):
                self.over = True
                return
        self.pipes = [p for p in self.pipes if p["x"] + self.pipe_w > 0]

    def draw(self, canvas, F):
        canvas.fill(BG)
        ground = CANVAS - 12
        pygame.draw.rect(canvas, (44, 48, 58), (0, ground, CANVAS, 12))
        pygame.draw.line(canvas, DIM, (0, ground), (CANVAS, ground), 3)
        for p in self.pipes:
            top_h = p["gap_y"] - self.gap / 2
            bot_y = p["gap_y"] + self.gap / 2
            pygame.draw.rect(canvas, GREEN, (p["x"], 0, self.pipe_w, top_h), border_radius=6)
            pygame.draw.rect(canvas, GREEN, (p["x"], bot_y, self.pipe_w, CANVAS - bot_y), border_radius=6)
        pygame.draw.ellipse(canvas, YELLOW, (self.gx, self.y, self.bird_w, self.bird_h))
        pygame.draw.ellipse(canvas, (255, 240, 200), (self.gx + 8, self.y + 6, 8, 8))
        s = font(30).render(f"F {self.score}", True, DIM)
        canvas.blit(s, (14, 10))
        if self.over:
            draw_over(canvas, F, f"{self.NAME}  {self.score}")


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
def menu_buttons():
    m = 24
    g = 20
    bw = (CANVAS - 2 * m - g) // 2
    bh = 108
    labels = [("1", "SNAKE"), ("2", "TYPE"), ("3", "2048"), ("4", "FLAP")]
    out = []
    top = 86
    for i, (k, lab) in enumerate(labels):
        col, row = i % 2, i // 2
        x = m + col * (bw + g)
        y = top + row * (bh + g)
        out.append((k, pygame.Rect(x, y, bw, bh), lab))
    return out


def draw_menu(canvas, F, hover):
    canvas.fill(BG)
    t = font(48, True)
    s = t.render("MINI GAMES", True, FG)
    canvas.blit(s, ((CANVAS - s.get_width()) // 2, 20))
    for k, rect, lab in menu_buttons():
        sel = hover is not None and rect.collidepoint(hover)
        pygame.draw.rect(canvas, ACCENT if sel else PANEL, rect, border_radius=16)
        pygame.draw.rect(canvas, FG if sel else DIM, rect, width=2, border_radius=16)
        # number badge
        cx = rect.x + 34
        cy = rect.y + 30
        pygame.draw.circle(canvas, ACCENT if sel else (60, 66, 78), (cx, cy), 20)
        b = font(26, True).render(k, True, BG if sel else FG)
        canvas.blit(b, (cx - b.get_width() // 2, cy - b.get_height() // 2 - 2))
        # label
        l = font(34, True).render(lab, True, BG if sel else FG)
        canvas.blit(l, (rect.x + 20, rect.y + 64))
    h = font(24).render("1-4 / CLICK    ESC = QUIT", True, DIM)
    canvas.blit(h, ((CANVAS - h.get_width()) // 2, CANVAS - 34))


# ----------------------------------------------------------------------
# Self-test (headless): plays each game briefly with synthetic input
# ----------------------------------------------------------------------
def _start_selftest():
    def runner():
        time.sleep(0.6)
        def key(k, u=""):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u))
        # 1 Snake
        key(pygame.K_1, "1"); time.sleep(0.5)
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
    F = {"title": font(48, True), "body": font(30), "small": font(24)}
    clock = pygame.time.Clock()

    if os.environ.get("STEALTH_SELFTEST"):
        _start_selftest()

    GAME_CLASSES = {"1": SnakeGame, "2": TypeRushGame, "3": Game2048, "4": FlapGame}
    state, game, hover = "menu", None, None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if state == "menu":
                if event.type == pygame.KEYDOWN:
                    if event.unicode in GAME_CLASSES:
                        game = GAME_CLASSES[event.unicode]()
                        state = event.unicode
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return
                elif event.type == pygame.MOUSEMOTION:
                    hover = event.pos
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for k, rect, _ in menu_buttons():
                        if rect.collidepoint(event.pos):
                            game = GAME_CLASSES[k]()
                            state = k
                            break
            else:
                game.handle(event)

        if state != "menu":
            game.update(1.0 / CONFIG["fps"])
            if game.done:
                game, state = None, "menu"

        if state == "menu":
            draw_menu(canvas, F, hover)
        else:
            game.draw(canvas, F)

        scaled = pygame.transform.smoothscale(canvas, (WIN, WIN))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()
    if os.environ.get("STEALTH_SELFTEST"):
        print("SELFTEST OK", flush=True)
