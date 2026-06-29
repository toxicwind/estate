#!/usr/bin/env python3
"""Health check utilities"""
import requests

def check_llm(url="http://127.0.0.1:25001"):
    try:
        return requests.get(f"{url}/health", timeout=5).status_code == 200
    except:
        return False

def check_nfcot(url="http://127.0.0.1:25008"):
    try:
        return requests.get(f"{url}/v1/models", timeout=5).status_code == 200
    except:
        return False
