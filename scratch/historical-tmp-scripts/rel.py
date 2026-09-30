#!/usr/bin/env python3
"""Send REL move + optional press via persistent pointer. Usage: rel.py DX DY [press_ms]"""
import sys, time
import evdev
from evdev import UInput, ecodes as E

dx, dy = int(sys.argv[1]), int(sys.argv[2])
press_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 0
caps = {
    E.EV_KEY: [E.BTN_LEFT, E.BTN_RIGHT, E.BTN_MIDDLE],
    E.EV_REL: [E.REL_X, E.REL_Y],
}
ui = UInput(caps, name="relptr", version=0x1)
time.sleep(0.4)
# Move in small steps to reduce acceleration artifacts
steps = max(1, max(abs(dx), abs(dy)) // 100)
for i in range(steps):
    ui.write(E.EV_REL, E.REL_X, dx // steps)
    ui.write(E.EV_REL, E.REL_Y, dy // steps)
    ui.syn()
    time.sleep(0.02)
ui.write(E.EV_REL, E.REL_X, dx - (dx // steps) * steps)
ui.write(E.EV_REL, E.REL_Y, dy - (dy // steps) * steps)
ui.syn()
time.sleep(0.3)
if press_ms > 0:
    ui.write(E.EV_KEY, E.BTN_LEFT, 1)
    ui.syn()
    time.sleep(press_ms / 1000.0)
    ui.write(E.EV_KEY, E.BTN_LEFT, 0)
    ui.syn()
    time.sleep(0.2)
ui.close()
print(f"moved {dx},{dy}" + (" + pressed" if press_ms else ""), flush=True)
