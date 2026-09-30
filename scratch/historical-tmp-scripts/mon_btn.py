#!/usr/bin/env python3
"""Monitor an input device for BTN_LEFT. Usage: mon_btn.py /dev/input/eventX [seconds]"""
import sys, time, select
import evdev
from evdev import ecodes as E

dev = evdev.InputDevice(sys.argv[1])
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 6
print(f"monitoring {dev.name} for {secs}s", flush=True)
end = time.time() + secs
while time.time() < end:
    r, _, _ = select.select([dev.fd], [], [], 0.5)
    if r:
        for ev in dev.read():
            if ev.type == E.EV_KEY and ev.code == E.BTN_LEFT:
                print(f"BTN_LEFT {'PRESS' if ev.value==1 else 'RELEASE' if ev.value==0 else ev.value} t={ev.timestamp():.3f}", flush=True)
print("done", flush=True)
