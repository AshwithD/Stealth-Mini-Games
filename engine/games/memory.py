"""Game 5: Memory (concentration).

Deepened mechanics:
- 4x4 grid of 8 symbol pairs. Flip two cards; matches stay up (green),
  mismatches flip back after a short delay (during which clicks are locked).
- Move counter + elapsed timer; clearing the board is a win and records the
  best number of moves.
"""
import random
import time

import pygame

from ..constants import BG, FG, DIM, GREEN, ACCENT, PANEL, MUTED
from .base import GameBase

SYMBOLS = ["A", "B", "C", "D", "E", "F", "G", "H"]

CARD_W, CARD_H, CARD_GAP = 72, 58, 10
GRID_COLS, GRID_ROWS = 4, 4


class MemoryGame(GameBase):
    KEY = "5"
    NAME = "MEMORY"
    LABEL = "MEMORY"
    ICON = "memory"
    DESC = "Flip cards, match all pairs in fewest moves"

    FLIP_BACK_DELAY = 1.1

    def __init__(self):
        super().__init__()
        self.ox = (360 - (GRID_COLS * CARD_W + (GRID_COLS - 1) * CARD_GAP)) // 2
        self.oy = 70
        self.reset()

    def reset(self):
        deck = SYMBOLS[:] * 2
        random.shuffle(deck)
        self.cards = [{"symbol": s, "up": False, "matched": False}
                      for s in deck]
        self.flipped = []            # indices currently face up (max 2)
        self.locked = False          # waiting for mismatch flip-back
        self.flip_back_t = 0.0
        self.moves = 0
        self.elapsed = 0.0
        self.score = 0
        self.over = False
        self.done = False
        self.won = False

    # ------------------------------------------------------------------
    def _card_rect(self, i):
        r, c = divmod(i, GRID_COLS)
        return pygame.Rect(self.ox + c * (CARD_W + CARD_GAP),
                           self.oy + r * (CARD_H + CARD_GAP),
                           CARD_W, CARD_H)

    def _hit(self, pos):
        for i, card in enumerate(self.cards):
            if card["matched"] or card["up"]:
                continue
            if self._card_rect(i).collidepoint(pos):
                return i
        return None

    def flip(self, i):
        card = self.cards[i]
        if card["up"] or card["matched"] or self.locked or self.over:
            return
        card["up"] = True
        self.flipped.append(i)
        if len(self.flipped) == 2:
            self.moves += 1
            a, b = self.flipped
            if self.cards[a]["symbol"] == self.cards[b]["symbol"]:
                self.cards[a]["matched"] = True
                self.cards[b]["matched"] = True
                self.score += 10
                self.flipped = []
                if all(c["matched"] for c in self.cards):
                    self.over = True
                    self.won = True
            else:
                self.locked = True
                self.flip_back_t = self.FLIP_BACK_DELAY

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or self.over:
                self.done = True
                return
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.over:
                self.done = True
                return
            i = self._hit(event.pos)
            if i is not None:
                self.flip(i)

    def record_value(self):
        # fewer moves is better
        return self.moves, False

    def update(self, dt):
        if self.over:
            return
        self.elapsed += dt
        if self.locked:
            self.flip_back_t -= dt
            if self.flip_back_t <= 0:
                self.locked = False
                for i in self.flipped:
                    self.cards[i]["up"] = False
                self.flipped = []

    # ------------------------------------------------------------------
    def draw(self, canvas, R):
        R.clear(canvas)
        for i, card in enumerate(self.cards):
            rect = self._card_rect(i)
            if card["matched"]:
                R.rr(canvas, rect, MUTED, radius=10)
                R.rr(canvas, rect, GREEN, radius=10, width=3)
                s = R.text(34, True, card["symbol"], DIM)
                R.blit_center(canvas, s, rect.centerx, rect.centery)
            elif card["up"]:
                R.rr(canvas, rect, PANEL, radius=10)
                R.rr(canvas, rect, ACCENT, radius=10, width=2)
                s = R.text(34, True, card["symbol"], FG)
                R.blit_center(canvas, s, rect.centerx, rect.centery)
            else:
                R.rr(canvas, rect, PANEL, radius=10)
                R.rr(canvas, rect, (60, 66, 78), radius=10, width=2)
                # subtle "back" mark
                cx, cy = rect.centerx, rect.centery
                R.circle(canvas, (cx, cy - 8), 6, (60, 66, 78))
                R.circle(canvas, (cx, cy + 8), 6, (60, 66, 78))
        m = R.text(30, False, f"M {self.moves}", DIM)
        R.blit(canvas, m, (14, 10))
        t = R.text(30, False, f"T {int(self.elapsed)}", DIM)
        R.blit(canvas, t, (360 - 14 - t.get_width(), 10))
        if self.over:
            self.finish(canvas, R, f"MEMORY {self.moves} moves")
        else:
            R.finish(canvas)
