"""Apply the ws_lane_claim probe-derivation fix to yote's connector.py."""
import sys

p = "/home/toxic/sovereign/projects/bridge/hatch/connector.py"
s = open(p).read()

old1 = '''            # Lane flags below are claims, not truth: a connectable socket
            # does not prove authenticated execution (caught 2026-09-20:
            # both lanes "true" while every real command 401'd). The
            # authoritative bit is exec_probe: a real no-op command executed
            # end-to-end through auth. ok=True requires it.
            ws_ok = False
            try:
                s = bridge._ws_try_once()
                if s is not None:
                    ws_ok = True
                    s.close()
            except Exception:
                pass
            https_down, https_why = bridge._https_known_down()'''
new1 = '''            # The authoritative bit is exec_probe: a real no-op command
            # executed end-to-end through auth. ok=True requires it.
            # The lane flags are DERIVED from that probe, never from a
            # separate claim: a claim that contradicts a successful
            # authenticated probe is a lie (caught 2026-09-21: raw-socket
            # claim probe called a nonexistent bridge helper, so
            # ws_lane_claim sat False while exec_probe ran fine over WS).
            https_down, https_why = bridge._https_known_down()'''
assert s.count(old1) == 1, "anchor old1 not unique/found"
s = s.replace(old1, new1)

old2 = '''            ok = probe["ok"]
            self._json(200 if ok else 503,
                       {"ok": ok, "exec_probe": probe,
                        "ws_lane_claim": ws_ok,'''
new2 = '''            ok = probe["ok"]
            # Lane claims derived from the probe just run: if an
            # authenticated command succeeded over WS, the WS lane works --
            # no separate claim may contradict that.
            ws_ok = bool(ok and probe.get("transport") == "ws")
            self._json(200 if ok else 503,
                       {"ok": ok, "exec_probe": probe,
                        "ws_lane_claim": ws_ok,'''
assert s.count(old2) == 1, "anchor old2 not unique/found"
s = s.replace(old2, new2)

old3 = '''                         (ok=True requires a real authenticated exec probe;
                         *_claim flags are claims, not truth -- see lines below)'''
# the em-dash variant may be present instead
if s.count(old3) != 1:
    old3 = old3.replace(" -- ", " \u2014 ")
new3 = '''                         (ok=True requires a real authenticated exec probe;
                         *_claim flags are derived from that probe -- a claim
                         never contradicts a successful authenticated run)'''
assert s.count(old3) == 1, "anchor old3 not unique/found: %d" % s.count(old3)
s = s.replace(old3, new3)

open(p, "w").write(s)
print("patched OK")