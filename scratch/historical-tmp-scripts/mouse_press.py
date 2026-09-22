#!/usr/bin/env python3
"""Clean mouse press-only (no move). Usage: mouse_press.py [press_ms]"""
import sys, time
import evdev
from evdev import UInput, ecodes as E

PRESS_MS = int(sys.argv[1]) if len(sys.argv) > 1 else 90
caps = {
    E.EV_KEY: [E.BTN_LEFT, E.BTN_RIGHT, E.BTN_MIDDLE],
    E.EV_REL: [E.REL_X, E.REL_Y],
}
ui = UInput(caps, name="testmouse2", version=0x1)
time.sleep(0.4)
ui.write(E.EV_KEY, E.BTN_LEFT, 1)
ui.syn()
time.sleep(PRESS_MS / 1000.0)
ui.write(E.EV_KEY, E.BTN_LEFT, 0)
ui.syn()
time.sleep(0.2)
ui.close()
print("pressed", flush=True)
