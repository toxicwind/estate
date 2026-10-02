import re

P = "/home/toxic/squawk-ws/squawk_ws_server.py"
src = open(P).read()

old = '''    for w in SUBSCRIBERS[channel]:
        try:
            w.write(frame_text(json.dumps(msg).encode()))
            await w.drain()
        except Exception:
            pass
    log(f"broadcast seq={seq} ch={channel} from={sender} sealed={sealed}")'''

new = '''    dead = []
    for w in list(SUBSCRIBERS[channel]):
        try:
            w.write(frame_text(json.dumps(msg).encode()))
            await w.drain()
        except Exception:
            dead.append(w)
    for w in dead:
        SUBSCRIBERS[channel].discard(w)
    log(f"broadcast seq={seq} ch={channel} from={sender} sealed={sealed}")'''

assert old in src, "pattern not found"
src = src.replace(old, new)
open(P, "w").write(src)
print("patched ok")
