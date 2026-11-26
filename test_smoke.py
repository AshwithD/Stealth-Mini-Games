#!/usr/bin/env python3
"""Smoke test: boot the App headless, click through menu/stats/every game,
simulate a drag, and check nothing crashes or hangs.

Uses the SDL dummy driver. Exits 0 on success, 1 on failure.
"""
import os
import sys
import threading
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.setdefault("SDL_VIDEO_WINDOW_POS", "0,0")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from engine.app import App

TIMEOUT = 60.0


def key(k, u=""):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u))


def click(pos):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))


def drag(start, end):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=1))
    for i in range(1, 7):
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(start[0] + (end[0] - start[0]) * i // 6,
                 start[1] + (end[1] - start[1]) * i // 6)))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=end, button=1))


def main():
    app = App()
    app.cfg["fps"] = 120

    # seed stats so the stats screen has content
    for k, v in [("1", 12), ("2", 30), ("5", 4)]:
        app.store.record_game(k, v, won=(k == "5"),
                              higher=(k != "5"))

    # run the loop in a background thread
    t = threading.Thread(target=app.run, daemon=True)
    t.start()
    start = time.time()
    try:
        time.sleep(0.8)
        assert app.state == "menu", f"expected menu, got {app.state}"

        # stats screen
        key(pygame.K_8, "8")
        time.sleep(0.4)
        assert app.state == "menu" and app.stats_view
        key(pygame.K_ESCAPE)
        time.sleep(0.4)
        assert not app.stats_view

        # a click on the menu must start a game (cell 1 is top-left area).
        # Mouse events arrive in screen space (114 px window); the App
        # scales them to canvas space (360 px). Cell 1's canvas center is
        # ~(68, 96) -> screen ~(22, 30).
        click((22, 30))
        time.sleep(0.3)
        assert app.state == "game" and app.game is not None, \
            f"click did not start a game (state={app.state})"
        # back to menu
        key(pygame.K_ESCAPE)
        time.sleep(0.3)
        assert app.state == "menu"

        # drag must NOT start a game or quit
        before_state = app.state
        drag((150, 150), (180, 175))
        time.sleep(0.4)
        assert app.state == before_state, "drag changed state unexpectedly"

        # play each game briefly (synthetic input)
        plan = [
            (pygame.K_1, "1", 0.4, [(pygame.K_RIGHT, 0.15), (pygame.K_DOWN, 0.2),
                                    (pygame.K_m, 0.1), (pygame.K_p, 0.1),
                                    (pygame.K_p, 0.1)]),
            (pygame.K_2, "2", 0.4, [(pygame.K_a, 0.1) for _ in "word"],
            ),
            (pygame.K_3, "3", 0.4,
             [(pygame.K_LEFT, 0.15), (pygame.K_UP, 0.15), (pygame.K_u, 0.1)]),
            (pygame.K_4, "4", 0.4, [(pygame.K_SPACE, 0.2) for _ in range(6)]),
            (pygame.K_5, "5", 0.4, []),
            (pygame.K_6, "6", 0.4, [("click", 0.2)]),
            (pygame.K_7, "7", 0.4, [(pygame.K_SPACE, 0.15)]),
        ]
        for start_key, unicode, settle, actions in plan:
            key(start_key, unicode)
            time.sleep(settle)
            assert app.state == "game" and app.game is not None, \
                f"key {start_key} did not start {unicode}"
            for act in actions:
                # a game may end early (e.g. Type Rush timeout): stop
                # feeding it once it has returned to the menu
                if app.state != "game":
                    break
                if act == "click":
                    click((180, 180))
                else:
                    key(act[0])
                time.sleep(act[1])
            # only send ESCAPE if the game is still running; an ESCAPE in
            # menu state would quit the app
            if app.state == "game":
                key(pygame.K_ESCAPE)
                time.sleep(0.3)
            assert app.state == "menu", "game did not return to menu"

        # stats should now contain the played games
        summary = app.store.summary()
        assert len(summary) >= 3, summary

        print(f"SMOKE TEST PASSED in {time.time() - start:.1f}s "
              f"({len(summary)} game entries in stats)")
        return 0
    except AssertionError:
        import traceback; traceback.print_exc()
        print("SMOKE TEST FAILED (assertion)")
        return 1
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"SMOKE TEST FAILED: {type(e).__name__}: {e}")
        return 1
    finally:
        try:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        except Exception:
            pass
        time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
