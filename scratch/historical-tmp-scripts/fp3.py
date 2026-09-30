#!/usr/bin/env python3
"""forge: final test assertion fix."""
p = "/tmp/sswap/internal/router/peer_test.go"
L = open(p).readlines()
T = "\t"
i = next(i for i, l in enumerate(L) if "expected workaround Bearer" in l)
assert L[i - 1].lstrip().startswith("if "), repr(L[i - 1])
assert L[i + 1] == T + "}\n", repr(L[i + 1])
L[i - 1:i + 2] = [
    T + 'if receivedAuth != "" {\n',
    T + T + 't.Errorf("expected stripped Authorization header, got %q", receivedAuth)\n',
    T + "}\n",
]
open(p, "w").writelines(L)
print("OK StripsClientAuth assertion updated")
