#!/usr/bin/env python3
"""End-to-end stack tests"""
import requests
import sys

BASE_URL = "http://127.0.0.1"

def test_llm():
    r = requests.get(f"{BASE_URL}:25001/health", timeout=5)
    assert r.status_code == 200, "LLM health failed"
    print("✓ llama-server")

def test_nfcot():
    r = requests.get(f"{BASE_URL}:25008/v1/models", timeout=5)
    assert r.status_code == 200, "NF-CoT proxy failed"
    print("✓ nfcot-proxy")

def test_caddy():
    r = requests.get(f"{BASE_URL}:80/health", timeout=5)
    assert r.status_code == 200, "Caddy failed"
    print("✓ caddy")

if __name__ == "__main__":
    test_llm()
    test_nfcot()
    test_caddy()
    print("All tests passed")
