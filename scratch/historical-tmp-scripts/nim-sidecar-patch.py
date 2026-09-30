import sys
p = '/home/toxic/sovereign/bin/nim-kimi-sidecar.py'
src = open(p).read()
anchor = "                return\n            except urllib.error.HTTPError as e:\n"
assert src.count(anchor) == 1, "anchor not unique: %d" % src.count(anchor)
fix = ("                return\n"
       "            except BrokenPipeError:\n"
       "                # Downstream client disconnected while we waited out the\n"
       "                # ~130s cold upstream (its own timeout fired). Upstream\n"
       "                # already answered 200 -- retrying would burn another\n"
       "                # full cold call for a client that is gone. Log and stop:\n"
       "                # no retry, no consec_fail (the provider did its job).\n"
       "                log(\"client disconnected after upstream 200; not retrying\")\n"
       "                return\n"
       "            except urllib.error.HTTPError as e:\n")
open(p, 'w').write(src.replace(anchor, fix))
import ast; ast.parse(open(p).read())
print("patched ok")
