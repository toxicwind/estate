#!/usr/bin/env python3
"""
NF-CoT Proxy — Neural Flow Chain-of-Thought Proxy
Injects structured reasoning triggers into LLM requests.
Routes through shadow latent model if enabled.
"""

import http.client
import json
import os
import socketserver
import urllib.parse
from http.server import BaseHTTPRequestHandler

MODEL_URL = os.environ.get("MODEL_URL", "http://127.0.0.1:25001")
PROXY_PORT = int(os.environ.get("PROXY_PORT", "25008"))
TRIGGER_TOKEN = os.environ.get("TRIGGER_TOKEN", "<|im_start|>think")
FORCE_TRIGGER = os.environ.get("FORCE_TRIGGER", "true").lower() == "true"
ENABLE_SHADOW_LATENT = os.environ.get("ENABLE_SHADOW_LATENT", "1") == "1"
FLOW_PATH = os.environ.get("FLOW_PATH", "/home/toxic/sovereign/nfcot_flow.pt")

class NFCoTHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ("/v1/models", "/health"):
            self._proxy("GET", self.path)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            self._handle_chat()
            return
        if self.path == "/v1/completions":
            self._proxy("POST", self.path)
            return
        self._proxy("POST", self.path)

    def _proxy(self, method, path):
        try:
            url = urllib.parse.urlparse(MODEL_URL)
            conn = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=30)
            body = None
            if method == "POST":
                cl = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(cl)
            conn.request(method, path, body=body, headers={k: v for k, v in self.headers.items()})
            resp = conn.getresponse()
            self.send_response(resp.status)
            for h, v in resp.getheaders():
                self.send_header(h, v)
            self.end_headers()
            self.wfile.write(resp.read())
            conn.close()
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_chat(self):
        cl = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(cl))
        messages = req.get("messages", [])
        if messages and FORCE_TRIGGER:
            content = messages[-1].get("content", "")
            if TRIGGER_TOKEN not in content:
                messages[-1]["content"] = f"{TRIGGER_TOKEN}\n{content}"
        if ENABLE_SHADOW_LATENT and os.path.exists(FLOW_PATH):
            pass  # Real impl: load torch model here
        url = urllib.parse.urlparse(MODEL_URL)
        conn = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=300)
        payload = json.dumps({
            "model": req.get("model", "qwen"),
            "messages": messages,
            "stream": req.get("stream", False),
            "temperature": req.get("temperature", 0.7),
            "max_tokens": req.get("max_tokens", 4096),
        }).encode()
        conn.request("POST", "/v1/chat/completions", body=payload, headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(payload))
        })
        resp = conn.getresponse()
        self.send_response(resp.status)
        for h, v in resp.getheaders():
            if h.lower() not in ("transfer-encoding",):
                self.send_header(h, v)
        self.end_headers()
        self.wfile.write(resp.read())
        conn.close()

def main():
    server = socketserver.TCPServer(("0.0.0.0", PROXY_PORT), NFCoTHandler)
    print(f"NF-CoT Proxy on :{PROXY_PORT} -> {MODEL_URL}")
    server.serve_forever()

if __name__ == "__main__":
    main()
