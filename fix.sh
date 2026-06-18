#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import os
import signal
import sys
from pathlib import Path

PROXY_PATH = Path("./modules/nfcot_proxy.py")
PROXY_URL = "http://127.0.0.1:25008"

def kill_existing():
    """Kill any running nfcot_proxy processes"""
    subprocess.run(["pkill", "-f", "nfcot_proxy.py"], capture_output=True)
    time.sleep(0.8)

def start_proxy():
    """Start the proxy and wait until it's healthy"""
    print("Starting nfcot_proxy...")
    proc = subprocess.Popen(
        [sys.executable, str(PROXY_PATH)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

    for i in range(25):
        try:
            r = requests.get(f"{PROXY_URL}/health", timeout=2)
            if r.ok:
                print(f"✓ Proxy is healthy after {i+1}s")
                return proc
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

    print("✗ Proxy failed to start in time")
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    sys.exit(1)

def test_proxy():
    kill_existing()
    proc = start_proxy()

    try:
        print("\n" + "="*60)
        print("Health Check:")
        health = requests.get(f"{PROXY_URL}/health", timeout=5).json()
        print(json.dumps(health, indent=2))

        print("\n" + "="*60)
        print("Sending test request...")

        payload = {
            "messages": [{"role": "user", "content": "Hi, how are you?"}],
            "max_tokens": 50,
            "temperature": 0.7
        }

        r = requests.post(
            f"{PROXY_URL}/v1/chat/completions",
            json=payload,
            timeout=60
        )

        print(f"Status Code: {r.status_code}")

        try:
            data = r.json()
            print("\nFull Response:")
            print(json.dumps(data, indent=2))

            # Clean summary
            print("\n" + "-"*40)
            if "choices" in data and data["choices"]:
                content = data["choices"][0]["message"]["content"]
                print(f"Content: {repr(content)}")
                
                if "sovereign_receipt" in data:
                    receipt = data["sovereign_receipt"]
                    print(f"\nInjection Success: {receipt.get('injection_success')}")
                    print(f"Latent Value:     {receipt.get('latent')}")
                    print(f"Trigger Used:     {receipt.get('trigger_used')}")
            else:
                print("No choices returned in response")

        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print("Raw response:", r.text)

    finally:
        print("\n" + "="*60)
        print("Cleaning up...")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        time.sleep(0.5)

if __name__ == "__main__":
    test_proxy()