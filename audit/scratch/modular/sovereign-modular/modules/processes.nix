{ config, pkgs, lib, ... }:
let
  shared = import ./lib.nix { inherit pkgs lib; };
in
{
  processes = {
    llama-server = {
      exec = ''
        exec ${config.packages.beellama-cpp}/bin/llama-server \
          -m "${shared.ACTIVE_MODEL}" \
          --host 0.0.0.0 \
          --port ${toString shared.PORTS.llama-server} \
          -c ${toString shared.LLAMA_FLAGS.ctx-size} \
          --slots ${toString shared.LLAMA_FLAGS.slots} \
          -b ${toString shared.LLAMA_FLAGS.batch} \
          -ub ${toString shared.LLAMA_FLAGS.ubatch} \
          --flash-attn auto \
          -ngl ${toString shared.LLAMA_FLAGS.ngl} \
          -t ${toString shared.LLAMA_FLAGS.threads} \
          --no-mmap --mlock --embeddings --pooling cls \
          --cache-type-k ${shared.LLAMA_FLAGS.cache-type-k} \
          --cache-type-v ${shared.LLAMA_FLAGS.cache-type-v} \
          --kv-unified --no-host --ctx-checkpoints 32 --cache-ram 8192 \
          --draft "${shared.ACTIVE_DRAFT}" \
          --draft-n-ctx ${toString shared.LLAMA_FLAGS.draft-n-ctx} \
          --draft-n-predict ${toString shared.LLAMA_FLAGS.draft-n-predict} \
          --draft-n-gpu-layers ${toString shared.LLAMA_FLAGS.draft-ngl} \
          --metrics --log-format json
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${toString shared.PORTS.llama-server}/health || exit 1";
          initial_delay_seconds = 15;
          period_seconds = 5;
          timeout_seconds = 5;
          failure_threshold = 30;
        };
        availability = {
          restart = "on_failure";
          backoff_seconds = 5;
          max_restarts = 10;
        };
      };
    };

    hf-downloader = {
      exec = ''
        mkdir -p "${shared.SOV_HOME}/.state"
        cat > "${shared.SOV_HOME}/.state/hf_downloader.py" << 'PYEOF'
import http.server, socketserver, subprocess, os, json, urllib.parse, sys

PORT = int(os.environ["HF_DOWNLOADER"])
SOVEREIGN = os.environ.get("SOVEREIGN_HOME", ".")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            return
        if parsed.path.startswith("/hf/"):
            repo = parsed.path[4:].strip("/")
            local_dir = os.path.join(SOVEREIGN, "models", "hf", repo.replace("/", "_"))
            os.makedirs(local_dir, exist_ok=True)
            try:
                subprocess.run(
                    ["python3", "-m", "huggingface_hub.cli", "download", repo,
                     "--local-dir", local_dir, "--local-dir-use-symlinks", "False"],
                    check=True, capture_output=True
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "downloaded", "repo": repo, "path": local_dir
                }).encode())
            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": str(e), "stderr": e.stderr.decode()
                }).encode())
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("HF Downloader listening on :" + str(PORT))
    httpd.serve_forever()
PYEOF
        exec ${pkgs.python3}/bin/python3 "${shared.SOV_HOME}/.state/hf_downloader.py"
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${toString shared.PORTS.hf-downloader}/health || exit 1";
          initial_delay_seconds = 1;
          period_seconds = 3;
          failure_threshold = 5;
        };
      };
    };

    llama-herder = {
      exec = "${config.packages.llama-herder-pkg}/bin/llama-herder";
      process-compose = {
        depends_on.llama-server.condition = "process_healthy";
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${toString shared.PORTS.llama-herder}/health || exit 1";
          initial_delay_seconds = 2;
          period_seconds = 5;
          failure_threshold = 10;
        };
      };
    };

    # Add the other processes (openfang, watchdog, prometheus, rust-web, etc.) here later
    # They can be copied from the original monolith when you are ready to split further.
  };
}
