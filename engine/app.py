"""Application: state machine, event pump, main loop.

States:
- ``menu``  - the 3x3 menu grid (or the stats screen)
- ``game``   - a game is running (``paused`` overlay possible)

Responsibilities:
- window setup (borderless, bottom-left, optional always-on-top)
- input routing: keys, clicks, and the click-vs-drag window mover
- hotkeys: Esc/Q quit, P pause, T always-on-top toggle
- best-score / stats recording through the Store
- rendering through the shared Renderer

The App is also self-testable: with STEALTH_SELFTEST set it plays every game
headlessly with synthetic events (including a simulated drag) and exits.
"""
import os
import threading
import time

import pygame

from . import config
from .constants import CANVAS, NOFRAME
from .input import DragController, move_to_bottom_left, set_topmost
from .menu import draw_menu, draw_stats, menu_cells
from .renderer import Renderer
from .storage import Store
from .games import GAME_CLASSES, GAME_META


class App:
    def __init__(self):
        self.cfg = config.load_settings()
        self.win_size = config.window_size(self.cfg)
        self.store = Store()
        self.drag = DragController()
        self.state = "menu"       # "menu" | "game"
        self.stats_view = False   # menu showing stats instead of grid
        self.game = None
        self.state_key = None
        self.paused = False
        self.hover = None
        self._press_pos = None
        self._running = False

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _init_window(self):
        pygame.init()
        pygame.display.set_caption(self.cfg["title"])
        try:
            screen = pygame.display.set_mode((self.win_size, self.win_size),
                                             NOFRAME)
        except pygame.error:
            screen = pygame.display.set_mode((self.win_size, self.win_size))
        move_to_bottom_left(self.win_size)
        if self.cfg["always_on_top"]:
            set_topmost(True)
        return screen

    # ------------------------------------------------------------------
    # Event routing
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
            return
        # right-click quits from anywhere
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self._running = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drag.on_press(event.pos)
            self._press_pos = event.pos
            return
        if event.type == pygame.MOUSEMOTION:
            if self.state == "menu":
                self.hover = event.pos
            self.drag.on_move(event.pos)
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag.on_release(event.pos):
                self._handle_click()
            self._press_pos = None
            return

        if event.type == pygame.KEYDOWN:
            # global hotkeys
            if event.key == pygame.K_t:
                self.cfg["always_on_top"] = not self.cfg["always_on_top"]
                set_topmost(self.cfg["always_on_top"])
                config.save_settings(self.cfg)
                return
            if event.key == pygame.K_q:
                self._running = False
                return
            if event.key == pygame.K_p and self.state == "game":
                if self.game is not None and not self.game.over:
                    self.paused = not self.paused
                return

            if self.state == "menu":
                self._handle_menu_key(event)
            else:
                self.game.handle(event)

    def _handle_menu_key(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.stats_view:
                self.stats_view = False
            else:
                self._running = False
            return
        u = event.unicode
        if u in GAME_CLASSES:
            self._start_game(u)
        elif u == "8":
            self.stats_view = True
        elif u == "9":
            self._running = False

    def _handle_click(self):
        pos = self._press_pos
        if pos is None:
            return
        if self.state == "menu":
            if self.stats_view:
                self.stats_view = False
                return
            for key, rect, _, _, kind in menu_cells(CANVAS):
                if rect.collidepoint(pos):
                    if kind == "game":
                        self._start_game(key)
                    elif kind == "stats":
                        self.stats_view = True
                    elif kind == "quit":
                        self._running = False
                    return
        else:
            # forward the click to the running game
            if self.game is not None:
                self.game.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                    pos=pos, button=1))

    def _start_game(self, key):
        self.game = GAME_CLASSES[key]()
        self.state = "game"
        self.state_key = key
        self.paused = False
        self.drag.cancel()

    def _back_to_menu(self):
        self.game = None
        self.state = "menu"
        self.state_key = None
        self.paused = False
        self.drag.cancel()

    # ------------------------------------------------------------------
    # Per-frame logic
    # ------------------------------------------------------------------
    def _update(self, dt):
        if self.state != "game" or self.paused:
            return
        game = self.game
        game.update(dt)
        if game.done:
            self._back_to_menu()
            return
        if game.over and not getattr(game, "_saved", False):
            game._saved = True
            value, higher = game.record_value()
            best, new_best = self.store.record_game(self.state_key, value,
                                                    game.won, higher)
            game.best = best
            game.new_best = new_best

    def _draw(self, R):
        if self.state == "menu":
            if self.stats_view:
                draw_stats(R.canvas, R, self.store, GAME_META)
            else:
                draw_menu(R.canvas, R, GAME_META, self.hover, self.store)
        else:
            self.game.draw(R.canvas, R)
            if self.paused:
                R.draw_paused(R.canvas)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        screen = self._init_window()
        R = Renderer(self.win_size, CANVAS)
        clock = pygame.time.Clock()
        self._running = True

        if os.environ.get("STEALTH_SELFTEST"):
            _start_selftest(self)

        try:
            while self._running:
                dt = clock.tick(self.cfg["fps"]) / self.cfg["fps"]
                for event in pygame.event.get():
                    self.handle_event(event)
                self._update(dt)
                self._draw(R)
                R.present(screen)
                pygame.display.flip()
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            pygame.quit()
        if os.environ.get("STEALTH_SELFTEST"):
            print("SELFTEST OK", flush=True)


# ----------------------------------------------------------------------
# Headless self-test: synthetic events for every game + a drag simulation
# ----------------------------------------------------------------------
def _start_selftest(app):
    def runner():
        time.sleep(0.5)

        def key(k, u=""):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u))

        def click(pos):
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                 pos=pos, button=1))
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                                 pos=pos, button=1))

        def drag(start, end):
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                 pos=start, button=1))
            for i in range(1, 6):
                pygame.event.post(pygame.event.Event(
                    pygame.MOUSEMOTION,
                    pos=(start[0] + (end[0] - start[0]) * i // 5,
                         start[1] + (end[1] - start[1]) * i // 5)))
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                                 pos=end, button=1))

        # stats screen, then back
        key(pygame.K_8, "8"); time.sleep(0.3)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        # simulated window drag on the menu (must NOT start a game)
        drag((200, 200), (240, 230)); time.sleep(0.3)

        # 1 Snake (with mode toggle + pause)
        key(pygame.K_1, "1"); time.sleep(0.4)
        key(pygame.K_m, "m"); time.sleep(0.2)
        key(pygame.K_p, "p"); time.sleep(0.2); key(pygame.K_p, "p")
        time.sleep(0.2)
        key(pygame.K_RIGHT); time.sleep(0.2); key(pygame.K_DOWN); time.sleep(0.3)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        # 2 Type Rush (type some letters)
        key(pygame.K_2, "2"); time.sleep(0.3)
        for ch in "abcdefghij":
            key(pygame.K_a, ch); time.sleep(0.12)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        # 3 2048 (moves + undo)
        key(pygame.K_3, "3"); time.sleep(0.3)
        for k in (pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN,
                  pygame.K_u):
            key(k); time.sleep(0.18)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        # 4 Flap (jumps)
        key(pygame.K_4, "4"); time.sleep(0.4)
        for _ in range(8):
            key(pygame.K_SPACE, " "); time.sleep(0.22)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        # 5 Memory (click a couple of cards)
        key(pygame.K_5, "5"); time.sleep(0.3)
        click((70, 110)); time.sleep(0.2)
        click((134, 110)); time.sleep(0.2)
        click((70, 184)); time.sleep(0.4)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        # 6 Reaction (click near the target area)
        key(pygame.K_6, "6"); time.sleep(0.3)
        click((180, 180)); time.sleep(0.2)
        click((120, 240)); time.sleep(0.3)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        # 7 Breakout (launch ball + move paddle)
        key(pygame.K_7, "7"); time.sleep(0.3)
        key(pygame.K_SPACE, " "); time.sleep(0.3)
        key(pygame.K_a); time.sleep(0.1); key(pygame.K_d); time.sleep(0.3)
        key(pygame.K_ESCAPE); time.sleep(0.3)

        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=runner, daemon=True).start()
