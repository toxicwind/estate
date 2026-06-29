#!/usr/bin/env python3
"""Sovereign Stack — end-to-end health tests"""
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
BASE = "http://127.0.0.1"
# your actual ports from lib.nix
SERVICES = {
    "llama-server": (25001, ["/health", "/v1/models"]),
    "nfcot": (25003, ["/health", "/v1/models"]),
    "openfang": (25004, ["/health"]),
    "rust-web": (25005, ["/health"]),
    "hf-downloader": (25020, ["/health"]),
    "llama-herder": (25021, ["/health"]),
    "watchdog": (25022, ["/health"]),
    "overlord": (25023, ["/health"]),
    "landing": (25000, ["/", "/health"]),
    "prometheus": (25030, ["/-/healthy", "/-/ready"]),
    "caddy-admin": (25031, ["/config/"]),
}
# services that are infrastructure (different checks)
INFRA = {
    "postgres": 5432,
    "redis": 6379,
    "nats": 4222,
}
GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def check_http(name, port, paths, timeout=2, retries=3):
  for path in paths:
    url = f"{BASE}:{port}{path}"
    for i in range(retries):
      try:
        r = requests.get(url, timeout=timeout)
        if r.status_code < 500:
          return True, f"{r.status_code} {path}"
      except:
        requests.RequestException
  return False, f"no response on {paths}"


def check_tcp(name, port, timeout=1):
  import socket
  try:
    with socket.create_connection((BASE[7:], port), timeout):
            return True, "open"
  except:
    OSError as e


def test_one(name, spec):
  if isinstance(spec, tuple):
    port, paths = spec
    ok, msg = check_http(name, port, paths)
  else:
    ok, msg = check_tcp(name, spec)
  status = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
  print(f"{status} {name:<15} :{spec if isinstance(spec,int) else spec[0]:<5} → {msg}")
  return ok


def main():
  print("🚀 Sovereign Stack Test —", time.strftime("%H:%M:%S"))
  print("-" * 55)
  all_services = {**SERVICES, **INFRA}
  results = {}
  with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(test_one, n, s): n for n, s in all_services.items()}
        for f in as_completed(futures):
            results[futures[f]] = f.result()
  print("-" * 55)
  passed = sum(results.values())
  total = len(results)
  if passed == total:
    print(f"{GREEN}All {total} services healthy{RESET}")
    return 0
  else:
    print(f"{YELLOW}{passed}/{total} up — {total-passed} down{RESET}")
    print("\nTip: run `devenv up --detach` then `sovereign:logs`")
    return 1
if __name__ == "__main__":
  sys.exit(main())
