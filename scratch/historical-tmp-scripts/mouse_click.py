#!/usr/bin/env python3
"""Clean mouse click via uinput: proper pointer device (no tablet bits).
Usage: mouse_click.py X Y [press_ms]"""
import sys, time
import evdev
from evdev import UInput, ecodes as E

X, Y = int(sys.argv[1]), int(sys.argv[2])
PRESS_MS = int(sys.argv[3]) if len(sys.argv) > 3 else 90

caps = {
    E.EV_KEY: [E.BTN_LEFT, E.BTN_RIGHT, E.BTN_MIDDLE],
    E.EV_REL: [E.REL_X, E.REL_Y],
    E.EV_ABS: [
        (E.ABS_X, evdev.AbsInfo(value=0, min=0, max=2559, fuzz=0, flat=0, resolution=0)),
        (E.ABS_Y, evdev.AbsInfo(value=0, min=0, max=1439, fuzz=0, flat=0, resolution=0)),
    ],
}
ui = UInput(caps, name="testmouse", version=0x1)
time.sleep(0.4)
ui.write(E.EV_ABS, E.ABS_X, X)
ui.write(E.EV_ABS, E.ABS_Y, Y)
ui.syn()
time.sleep(0.3)
ui.write(E.EV_KEY, E.BTN_LEFT, 1)
ui.syn()
time.sleep(PRESS_MS / 1000.0)
ui.write(E.EV_KEY, E.BTN_LEFT, 0)
ui.syn()
time.sleep(0.2)
ui.close()
print(f"mouse clicked {X},{Y}", flush=True)
