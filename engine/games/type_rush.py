"""Game 2: Type Rush.

Deepened mechanics:
- Word pool with a difficulty ramp: the per-word timer shrinks as the score
  grows (never below a fair minimum).
- Combo multiplier: consecutive completed words award bonus points and are
  shown on screen.
- Three mistakes (wrong letter or timeout) end the game.
"""
import random

import pygame

from ..constants import BG, FG, DIM, GREEN, RED, YELLOW, PANEL
from .base import GameBase

WORDS = [
    "code", "run", "file", "data", "word", "text", "mail", "list",
    "team", "plan", "draft", "note", "web", "app", "test", "play",
    "game", "grid", "map", "chat", "boss", "fish", "book", "page",
    "key", "tag", "link", "sync", "home", "back", "make", "build",
    "work", "task", "report", "chart", "graph", "logic", "loop", "byte",
]


class TypeRushGame(GameBase):
    KEY = "2"
    NAME = "TYPE"
    LABEL = "TYPE"
    ICON = "type"
    DESC = "Type the words fast - looks like real work"

    MIN_TIME = 1.8
    START_TIME = 3.0

    def __init__(self):
        super().__init__()
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
        self.won = False
        self.new_word()

    def new_word(self):
        if not self.pool:
            self.pool = WORDS[:]
            random.shuffle(self.pool)
        self.word = self.pool.pop()
        self.progress = 0
        # difficulty ramp: faster required as score grows, with a fair floor
        self.time_left = max(self.MIN_TIME, self.START_TIME - self.score * 0.005)
        self.time_total = self.time_left

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
            self.time_left = self.time_total
            self.mistakes += 1
            self.combo = 0
            self.flash = 0.4
            if self.mistakes >= 3:
                self.over = True

    def draw(self, canvas, R):
        R.clear(canvas)
        # panel behind the word (structure at tiny sizes)
        R.rr(canvas, (28, 128, R.canvas_size - 56, 128), PANEL, radius=20)
        # timer bar
        bar_w = R.canvas_size - 48
        x0, y0, h = 24, R.canvas_size - 42, 12
        ratio = max(0.0, min(1.0, self.time_left / self.time_total))
        color = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
        R.rr(canvas, (x0, y0, bar_w, h), (60, 64, 74), radius=6)
        R.rr(canvas, (x0, y0, int(bar_w * ratio), h), color, radius=6)
        # score + combo
        s = R.text(32, False, f"P {self.score}", DIM)
        R.blit(canvas, s, (14, 10))
        if self.combo >= 2:
            c = R.text(28, True, f"x{self.combo}", YELLOW)
            R.blit(canvas, c, (R.canvas_size - 14 - c.get_width(), 12))
        # mistake dots
        R.dot_row(canvas, 3, self.mistakes, 92, 26, 11, 16)
        # word, centered, one char per colored tile
        f = R.text(52, True, "A", FG)
        letters = list(self.word)
        widths = [R.text(52, True, ch, FG).get_width() for ch in letters]
        total = sum(widths) + 10 * (len(letters) - 1)
        x = (R.canvas_size - total) // 2
        y = R.canvas_size // 2 - f.get_height() // 2 - 6
        for i, ch in enumerate(letters):
            if i < self.progress:
                color = GREEN
            elif self.flash > 0 and i == self.progress:
                color = RED
            else:
                color = FG
            txt = R.text(52, True, ch, color)
            R.blit(canvas, txt, (x, y))
            x += txt.get_width() + 10
        if self.over:
            self.finish(canvas, R)
        else:
            R.finish(canvas)
