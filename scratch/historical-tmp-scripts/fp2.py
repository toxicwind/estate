#!/usr/bin/env python3
"""forge v2: remove Pollinations dummy-Bearer workaround via line-span edits.

All anchors are secret-free; spans are replaced wholesale so the old
dummy literal never needs to be reproduced exactly.
"""
import sys

T = "\t"
fails = []

def lines_of(path):
    with open(path) as f:
        return f.readlines()

def write(path, lines):
    with open(path, "w") as f:
        f.writelines(lines)

def find(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i
    return -1

def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond

# ---------- 1. internal/router/peer.go: dummy injection -> strip ----------
p = "/tmp/sswap/internal/router/peer.go"
L = lines_of(p)
w = find(L, '// Workaround for "not anonymous" gate')
if check(w > 0, "peer.go: workaround comment not found"):
    si = w - 1
    if check(L[si] == T + "} else {\n", f"peer.go: expected '}} else {{' at {si}, got {L[si]!r}"):
        ei = find(L, T + "}\n", w)
        if check(ei > w, "peer.go: closing brace not found"):
            new = [
                T + "} else {\n",
                T + T + "// No apiKey configured: send NO auth headers. Pollinations' free\n",
                T + T + "// tier accepts genuinely anonymous requests; the old dummy-Bearer\n",
                T + T + '// workaround ("pollinations-free-workaround") now 401s, so strip\n',
                T + T + "// any client-supplied auth rather than leak it upstream.\n",
                T + T + 'req.Header.Del("Authorization")\n',
                T + T + 'req.Header.Del("x-api-key")\n',
                T + "}\n",
            ]
            L[si:ei + 1] = new
            write(p, L)
            print("OK peer.go injection block")

# ---------- 2. internal/router/peer.go: Debugf already patched? ----------
L = lines_of(p)
if find(L, "peer: outgoing auth=") >= 0:
    print("OK peer.go Debugf already redacted")
else:
    fails.append("peer.go: Debugf redaction missing")

# ---------- 3. internal/config/peer.go: stale comment ----------
p = "/tmp/sswap/internal/config/peer.go"
L = lines_of(p)
i = find(L, "// Router will inject dummy")
if check(i >= 2, "config/peer.go: dummy comment not found"):
    if check("ApiKey injected as Authorization" in L[i - 2], "config/peer.go: comment block head mismatch"):
        L[i - 2:i + 1] = [
            T + "// ApiKey injected as Authorization: Bearer <key>. Empty means anonymous:\n",
            T + '// no auth headers are sent (the old "pollinations-free-workaround"\n',
            T + "// dummy Bearer <redacted> 401s on Pollinations as of 2026-09-20).\n",
        ]
        write(p, L)
        print("OK config/peer.go comment")

# ---------- 4. internal/freeproxy/pollinations.go ----------
p = "/tmp/sswap/internal/freeproxy/pollinations.go"
L = lines_of(p)
a = find(L, "// Workaround: any Bearer")
b = find(L, "// ponytail:", a)
if check(a >= 0 and b > a, "pollinations.go: workaround block anchors not found"):
    L[a:b + 1] = [
        T + "// No key configured: stay genuinely anonymous. The old dummy-Bearer\n",
        T + '// workaround ("pollinations-free-workaround") now 401s on Pollinations;\n',
        T + "// use a real key via POLLINATIONS_API_KEY if rate limits matter.\n",
    ]
    write(p, L)
    print("OK pollinations.go dummy fallback")

L = lines_of(p)
c = find(L, "// Inject workaround auth")
if check(c >= 0, "pollinations.go: rewrite anchor not found"):
    # c, c+1, c+2 = comment + two Set lines
    if check("r.Out.Header.Set" in L[c + 1] and "r.Out.Header.Set" in L[c + 2],
             "pollinations.go: expected two Set lines after rewrite comment"):
        L[c:c + 3] = [
            T + T + T + "// Real key only. Empty apiKey = anonymous request (no auth\n",
            T + T + T + "// headers); the dummy-Bearer <redacted> 401s.\n",
            T + T + T + 'if p.apiKey != "" {\n',
            T + T + T + T + 'r.Out.Header.Set("Authorization", "Bearer "+p.apiKey)\n',
            T + T + T + T + 'r.Out.Header.Set("x-api-key", p.apiKey)\n',
            T + T + T + "} else {\n",
            T + T + T + T + 'r.Out.Header.Del("Authorization")\n',
            T + T + T + T + 'r.Out.Header.Del("x-api-key")\n',
            T + T + T + "}\n",
        ]
        write(p, L)
        print("OK pollinations.go rewrite block")

# ---------- 5. internal/router/peer_test.go ----------
p = "/tmp/sswap/internal/router/peer_test.go"
L = lines_of(p)

def replace_if_block(anchor, new_block):
    global L
    i = find(L, anchor)
    if not check(i > 0, f"peer_test.go: anchor {anchor!r} not found"):
        return
    # block = lines[i-1] (if ...) .. lines[i+1] (})
    if not check(L[i - 1].lstrip().startswith("if ") and L[i + 1] == T + "}\n",
                 f"peer_test.go: block shape mismatch at {i}"):
        return
    L[i - 1:i + 2] = new_block
    print(f"OK peer_test.go: {anchor[:40]}")

replace_if_block("expected dummy workaround bearer", [
    T + 'if receivedAuthHeader != "" {\n',
    T + T + 't.Errorf("expected no Authorization header, got %q", receivedAuthHeader)\n',
    T + "}\n",
])
replace_if_block("expected x-api-key workaround", [
    T + 'if receivedXApiKey != "" {\n',
    T + T + 't.Errorf("expected no x-api-key header, got %q", receivedXApiKey)\n',
    T + "}\n",
])
replace_if_block("expected workaround Bearer", [
    T + 'if receivedAuth != "" {\n',
    T + T + 't.Errorf("expected stripped Authorization header, got %q", receivedAuth)\n',
    T + "}\n",
])

i = find(L, "// Updated for free-workaround:")
if check(i >= 0, "peer_test.go: NoApiKey comment not found"):
    L[i] = T + "// Empty apiKey = anonymous: NO auth headers are sent (dummy-Bearer <redacted> 401s on Pollinations).\n"
    print("OK peer_test.go NoApiKey comment")

i = find(L, "// Client sends dummy auth, peer with empty apiKey must override")
if check(i >= 0, "peer_test.go: StripsClientAuth comment not found"):
    L[i] = T + "// Client sends auth, peer with empty apiKey must strip it (never leak client key, never send dummy)\n"
    print("OK peer_test.go StripsClientAuth comment")

write(p, L)

if fails:
    print("FAILURES:")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("ALL PATCHES APPLIED")
