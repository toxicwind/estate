#!/usr/bin/env python3
"""Yote Agent — Autonomous task execution"""
import os
import requests

class YoteAgent:
    def __init__(self, model_url=None):
        self.model_url = model_url or os.environ.get("MODEL_URL", "http://127.0.0.1:25001")
        self.session = requests.Session()

    def chat(self, prompt, max_tokens=4096):
        resp = self.session.post(
            f"{self.model_url}/v1/chat/completions",
            json={"model": "qwen", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
        )
        return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    agent = YoteAgent()
    print(agent.chat("Hello, what is your purpose?"))
