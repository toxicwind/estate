#!/usr/bin/env python3
"""forge: remove Pollinations dummy-Bearer auth workaround from sovereign-swap."""
import sys

PEER_GO = "/tmp/sswap/internal/router/peer.go"
CONFIG_PEER_GO = "/tmp/sswap/internal/config/peer.go"
POLL_GO = "/tmp/sswap/internal/freeproxy/pollinations.go"
PEER_TEST = "/tmp/sswap/internal/router/peer_test.go"

T = "\t"

def patch(path, pairs):
    with open(path) as f:
        src = f.read()
    for old, new in pairs:
        if old not in src:
            print(f"MISS in {path}: {old[:70]!r}")
            return False
        if src.count(old) != 1:
            print(f"MULTI ({src.count(old)}x) in {path}: {old[:70]!r}")
            return False
        src = src.replace(old, new)
    with open(path, "w") as f:
        f.write(src)
    print(f"OK {path} ({len(pairs)} edits)")
    return True

ok = True

# 1. router/peer.go: dummy injection -> strip
ok &= patch(PEER_GO, [(
    T + "} else {\n"
    + T + T + "// Workaround for \"not anonymous\" gate (Pollinations now requires any Bearer <redacted> avoid 401).\n"
    + T + T + "// We ignore anonymous distinction entirely: inject dummy Bearer <redacted> free tier always passes.\n"
    + T + T + "// ponytail: dummy Bearer <redacted> free backends; use real key via peer.apiKey if rate-limit matters\n"
    + T + T + "req.Header.Set(\"Authorization\", \"Bearer <redacted>\")\n"
    + T + T + "req.Header.Set(\"x-api-key\", \"pollinations-free-workaround\")\n"
    + T + "}",
    T + "} else {\n"
    + T + T + "// No apiKey configured: send NO auth headers. Pollinations' free\n"
    + T + T + "// tier accepts genuinely anonymous requests; the old dummy-Bearer\n"
    + T + T + "// workaround (\"pollinations-free-workaround\") now 401s, so strip\n"
    + T + T + "// any client-supplied auth rather than leak it upstream.\n"
    + T + T + "req.Header.Del(\"Authorization\")\n"
    + T + T + "req.Header.Del(\"x-api-key\")\n"
    + T + "}",
)])

# 2. router/peer.go: stop logging the full Authorization header value
ok &= patch(PEER_GO, [(
    T + "r.logger.Debugf(\"peer: outgoing Authorization=%s Host=%s Path=%s\", req.Header.Get(\"Authorization\"), req.Host, req.URL.Path)",
    T + "if req.Header.Get(\"Authorization\") != \"\" {\n"
    + T + T + "r.logger.Debugf(\"peer: outgoing auth=present(redacted) Host=%s Path=%s\", req.Host, req.URL.Path)\n"
    + T + "} else {\n"
    + T + T + "r.logger.Debugf(\"peer: outgoing auth=none Host=%s Path=%s\", req.Host, req.URL.Path)\n"
    + T + "}",
)])

# 3. config/peer.go: stale comment
ok &= patch(CONFIG_PEER_GO, [(
    T + "// ApiKey injected as Authorization: Bearer <key>. Empty means free-workaround mode\n"
    + T + "// (Pollinations now requires any Bearer <redacted> avoid 401 \"not anonymous\" gate).\n"
    + T + "// Router will inject dummy \"pollinations-free-workaround\" when empty.\n",
    T + "// ApiKey injected as Authorization: Bearer <key>. Empty means anonymous:\n"
    + T + "// no auth headers are sent (the old \"pollinations-free-workaround\"\n"
    + T + "// dummy Bearer <redacted> 401s on Pollinations as of 2026-09-20).\n",
)])

# 4. freeproxy/pollinations.go: dummy fallback + unconditional injection
ok &= patch(POLL_GO, [(
    T + "// Workaround: any Bearer <redacted> anonymous gate; use stable dummy that Pollinations accepts.\n"
    + T + "// We ignore anonymous distinction entirely \u2014 always inject something.\n"
    + T + "if apiKey == \"\" {\n"
    + T + T + "apiKey = \"pollinations-free-workaround\"\n"
    + T + "}\n"
    + T + "// ponytail: dummy Bearer <redacted> free backends; use real key via POLLINATIONS_API_KEY if rate-limit matters\n",
    T + "// No key configured: stay genuinely anonymous. The old dummy-Bearer\n"
    + T + "// workaround (\"pollinations-free-workaround\") now 401s on Pollinations;\n"
    + T + "// use a real key via POLLINATIONS_API_KEY if rate limits matter.\n",
), (
    T + T + T + "// Inject workaround auth \u2014 ignore anonymous gate\n"
    + T + T + T + "r.Out.Header.Set(\"Authorization\", \"Bearer \"+p.apiKey)\n"
    + T + T + T + "r.Out.Header.Set(\"x-api-key\", p.apiKey)\n",
    T + T + T + "// Real key only. Empty apiKey = anonymous request (no auth\n"
    + T + T + T + "// headers); the dummy-Bearer <redacted> 401s.\n"
    + T + T + T + "if p.apiKey != \"\" {\n"
    + T + T + T + T + "r.Out.Header.Set(\"Authorization\", \"Bearer \"+p.apiKey)\n"
    + T + T + T + T + "r.Out.Header.Set(\"x-api-key\", p.apiKey)\n"
    + T + T + T + "} else {\n"
    + T + T + T + T + "r.Out.Header.Del(\"Authorization\")\n"
    + T + T + T + T + "r.Out.Header.Del(\"x-api-key\")\n"
    + T + T + T + "}\n",
)])

# 5. peer_test.go: NoApiKey expectations
ok &= patch(PEER_TEST, [(
    T + "// Updated for free-workaround: empty apiKey now injects dummy bearer (ignore anonymous gate)\n",
    T + "// Empty apiKey = anonymous: NO auth headers are sent (dummy-Bearer <redacted> 401s on Pollinations).\n",
), (
    T + "if receivedAuthHeader != \"Bearer <redacted>\" {\n"
    + T + T + "t.Errorf(\"expected dummy workaround bearer, got %q\", receivedAuthHeader)\n"
    + T + "}\n"
    + T + "if receivedXApiKey != \"pollinations-free-workaround\" {\n"
    + T + T + "t.Errorf(\"expected x-api-key workaround, got %q\", receivedXApiKey)\n"
    + T + "}\n",
    T + "if receivedAuthHeader != \"\" {\n"
    + T + T + "t.Errorf(\"expected no Authorization header, got %q\", receivedAuthHeader)\n"
    + T + "}\n"
    + T + "if receivedXApiKey != \"\" {\n"
    + T + T + "t.Errorf(\"expected no x-api-key header, got %q\", receivedXApiKey)\n"
    + T + "}\n",
)])

# 6. peer_test.go: StripsClientAuth expectations
ok &= patch(PEER_TEST, [(
    T + "// Client sends dummy auth, peer with empty apiKey must override with workaround (not leak client key)\n",
    T + "// Client sends auth, peer with empty apiKey must strip it (never leak client key, never send dummy)\n",
), (
    T + "if receivedAuth != \"Bearer <redacted>\" {\n"
    + T + T + "t.Errorf(\"expected workaround Bearer <redacted> override client key, got %q\", receivedAuth)\n"
    + T + "}\n",
    T + "if receivedAuth != \"\" {\n"
    + T + T + "t.Errorf(\"expected stripped Authorization header, got %q\", receivedAuth)\n"
    + T + "}\n",
)])

sys.exit(0 if ok else 1)
