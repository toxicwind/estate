#!/usr/bin/env python3
"""Apply NIM-proxy rewiring to herd.sh and router.ts on awrawr-pc."""
import pathlib
import sys

def patch_herd_sh():
    p = pathlib.Path("/home/toxic/sovereign/stack/services/herd.sh")
    t = p.read_text()
    if "Canonical secrets for provider keyEnvs" in t:
        print("herd.sh: already patched")
        return
    marker = "require_env HERD_PORT\n"
    assert marker in t, "herd.sh marker not found"
    insert = (
        "# Canonical secrets for provider keyEnvs. Sourced, never copied.\n"
        "if [[ -f /home/toxic/.secrets ]]; then\n"
        "  set -a; set +u\n"
        "  source /home/toxic/.secrets\n"
        "  set -u; set +a\n"
        "fi\n"
    )
    t = t.replace(marker, marker + insert, 1)
    p.write_text(t)
    print("herd.sh: patched")

def patch_router_ts():
    p = pathlib.Path("/home/toxic/sovereign/tools/sovereign-router/sovereign-router-ts/router.ts")
    t = p.read_text()
    if 'base: "http://127.0.0.1:8000/v1"' in t:
        print("router.ts: already patched")
        return
    old = 'base: "https://integrate.api.nvidia.com/v1",\n    key_env: "NVIDIA_API_KEY",\n    key_env_alt: "NVIDIA_NIM_API_KEY",'
    new = 'base: "http://127.0.0.1:8000/v1",\n    key_env: "NIM_PROXY_API_KEY",\n    key_env_alt: "NVIDIA_API_KEY",'
    assert old in t, "router.ts pattern not found"
    t = t.replace(old, new, 1)
    p.write_text(t)
    print("router.ts: patched")

if __name__ == "__main__":
    patch_herd_sh()
    patch_router_ts()
