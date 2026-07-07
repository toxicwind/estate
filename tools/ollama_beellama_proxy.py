#!/usr/bin/env python3
"""
ollama_beellama_proxy.py
Ollama API-compatible proxy for beellama.cpp / llama-server
Translates Ollama API calls to llama.cpp's OpenAI-compatible interface
Required for VS Code Copilot BYOM (Bring Your Own Model) integration

Usage:
    python3 ollama_beellama_proxy.py

Then in VS Code:
    Settings -> GitHub Copilot -> Local Provider -> Ollama
    Base URL: http://localhost:11434

The proxy spoofs Ollama's /api/version, /api/tags, /api/show endpoints
while forwarding chat/completions to your local llama-server.
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import threading
import sys
from datetime import datetime

# --- Configuration ---
LLAMA_HOST = "localhost"
LLAMA_PORT = 25001  # Your beellama.cpp server port
PROXY_PORT = 11434  # Ollama's default port (required for Copilot)
MODEL_NAME = "sovereign-llama:latest"  # Ollama-style model name

# --- Ollama API Spoofing ---

class OllamaHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{datetime.now().isoformat()}] {format % args}")

    def do_GET(self):
        if self.path == "/api/version":
            # Copilot checks this first to verify Ollama compatibility
            self._send_json({"version": "0.5.7"})
            print("[+] Spoofed /api/version")
            return

        elif self.path == "/api/tags":
            # Copilot lists available models here
            models = self._fetch_llama_models()
            self._send_json({"models": models})
            print("[+] Spoofed /api/tags")
            return

        elif self.path.startswith("/api/show"):
            # Copilot queries model details
            self._send_json({
                "modelfile": f"FROM {MODEL_NAME}",
                "parameters": "",
                "template": "{{ .System }} {{ .Prompt }}",
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "9B",
                    "quantization_level": "Q4_K_M"
                },
                "model_info": {
                    "general.architecture": "qwen3_moe",
                    "general.parameter_count": 9000000000,
                    "general.quantization_version": 2
                },
                "capabilities": ["completion", "chat", "vision"]
            })
            print("[+] Spoofed /api/show")
            return

        elif self.path == "/v1/models":
            # OpenAI-compatible model listing
            models = self._fetch_llama_models()
            self._send_json({
                "object": "list",
                "data": [{"id": m["name"], "object": "model"} for m in models]
            })
            return

        self._send_error(404, "Not found")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        if self.path == "/api/chat":
            # Ollama native chat format -> OpenAI format
            self._proxy_chat(body, ollama_format=True)
            return

        elif self.path == "/v1/chat/completions":
            # Already OpenAI format, forward directly
            self._proxy_chat(body, ollama_format=False)
            return

        elif self.path == "/api/generate":
            # Ollama generate -> OpenAI completions
            self._proxy_generate(body)
            return

        elif self.path == "/api/embeddings":
            # Forward to OpenAI embeddings
            self._proxy_embeddings(body)
            return

        self._send_error(404, "Not found")

    def _fetch_llama_models(self):
        """Fetch models from llama-server /v1/models endpoint"""
        try:
            req = urllib.request.Request(
                f"http://{LLAMA_HOST}:{LLAMA_PORT}/v1/models"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = []
                for m in data.get("data", []):
                    models.append({
                        "name": m.get("id", MODEL_NAME),
                        "model": m.get("id", MODEL_NAME),
                        "modified_at": datetime.now().isoformat(),
                        "size": 0,
                        "digest": "",
                        "details": {
                            "parent_model": "",
                            "format": "gguf",
                            "family": "llama",
                            "families": ["llama"],
                            "parameter_size": "9B",
                            "quantization_level": "Q4_K_M"
                        }
                    })
                return models if models else [{"name": MODEL_NAME, "model": MODEL_NAME}]
        except Exception as e:
            print(f"[!] Failed to fetch models from llama-server: {e}")
            return [{"name": MODEL_NAME, "model": MODEL_NAME}]

    def _proxy_chat(self, body, ollama_format=False):
        """Forward chat to llama-server /v1/chat/completions"""
        try:
            data = json.loads(body)

            # Convert Ollama format to OpenAI if needed
            if ollama_format:
                messages = data.get("messages", [])
                openai_body = {
                    "model": data.get("model", MODEL_NAME),
                    "messages": messages,
                    "stream": data.get("stream", True),
                    "options": data.get("options", {})
                }
                # Extract options
                opts = data.get("options", {})
                if "temperature" in opts:
                    openai_body["temperature"] = opts["temperature"]
                if "top_p" in opts:
                    openai_body["top_p"] = opts["top_p"]
                if "num_predict" in opts:
                    openai_body["max_tokens"] = opts["num_predict"]

                body = json.dumps(openai_body)

            req = urllib.request.Request(
                f"http://{LLAMA_HOST}:{LLAMA_PORT}/v1/chat/completions",
                data=body.encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=300) as resp:
                self.send_response(resp.status)
                for header, value in resp.headers.items():
                    if header.lower() not in ("transfer-encoding", "content-length"):
                        self.send_header(header, value)
                self.end_headers()

                # Stream response back
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except Exception as e:
            print(f"[!] Proxy error: {e}")
            self._send_error(502, f"Proxy error: {str(e)}")

    def _proxy_generate(self, body):
        """Forward generate to llama-server /v1/completions"""
        try:
            data = json.loads(body)
            openai_body = {
                "model": data.get("model", MODEL_NAME),
                "prompt": data.get("prompt", ""),
                "stream": data.get("stream", False),
                "max_tokens": data.get("options", {}).get("num_predict", 256)
            }

            req = urllib.request.Request(
                f"http://{LLAMA_HOST}:{LLAMA_PORT}/v1/completions",
                data=json.dumps(openai_body).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=300) as resp:
                self.send_response(resp.status)
                for header, value in resp.headers.items():
                    if header.lower() not in ("transfer-encoding", "content-length"):
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(resp.read())

        except Exception as e:
            self._send_error(502, f"Proxy error: {str(e)}")

    def _proxy_embeddings(self, body):
        """Forward embeddings to llama-server /v1/embeddings"""
        try:
            req = urllib.request.Request(
                f"http://{LLAMA_HOST}:{LLAMA_PORT}/v1/embeddings",
                data=body.encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                self.send_response(resp.status)
                for header, value in resp.headers.items():
                    self.send_header(header, value)
                self.end_headers()
                self.wfile.write(resp.read())

        except Exception as e:
            self._send_error(502, f"Proxy error: {str(e)}")

    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())


def run_proxy():
    with socketserver.TCPServer(("0.0.0.0", PROXY_PORT), OllamaHandler) as httpd:
        print("=" * 60)
        print("Ollama <-> Beellama.cpp Proxy")
        print("=" * 60)
        print(f"  Listening (as Ollama):  http://0.0.0.0:{PROXY_PORT}")
        print(f"  Forwarding to llama.cpp: http://{LLAMA_HOST}:{LLAMA_PORT}")
        print(f"  Advertised model:        {MODEL_NAME}")
        print("")
        print("  VS Code Copilot config:")
        print("    Settings -> GitHub Copilot -> Local Provider -> Ollama")
        print(f"    Base URL: http://localhost:{PROXY_PORT}")
        print("=" * 60)
        httpd.serve_forever()


if __name__ == "__main__":
    run_proxy()
