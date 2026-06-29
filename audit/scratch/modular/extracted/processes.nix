  processes = {
    landing = {
      exec = ''
        cd "${SOV_HOME}/landing" 2>/dev/null || cd "${SOV_HOME}"
        exec ${pkgs.bun}/bin/bun run server.ts --port "${"$"}{LANDING_PAGE}"
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{LANDING_PAGE}/health || exit 1";
          initial_delay_seconds = 2;
          period_seconds = 5;
          timeout_seconds = 3;
          failure_threshold = 10;
        };
      };
    };
    llama-server = {
      exec = llamaServerCmd;
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{LLAMA_SERVER_PORT}/health || exit 1";
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
        mkdir -p "${"$"}{SOVEREIGN_HOME}/.state"
        cat > "${"$"}{SOVEREIGN_HOME}/.state/hf_downloader.py" << 'PYEOF'
import http.server, socketserver, subprocess,
os, json, urllib.parse, sys
PORT = int(os.environ["HF_DOWNLOADER"])
SOVEREIGN = os.environ.get("SOVEREIGN_HOME", ".")
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK"); return
        if parsed.path.startswith("/hf/"):
            repo = parsed.path[4:].strip("/")
            local_dir = os.path.join(SOVEREIGN, "models", "hf", repo.replace("/", "_"))
            os.makedirs(local_dir, exist_ok=True)
            try:
                subprocess.run(
                    ["python3", "-m", "huggingface_hub.cli", "download", repo, "--local-dir", local_dir, "--local-dir-use-symlinks", "False"],
                    check=True, capture_output=True
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "downloaded", "repo": repo, "path": local_dir}).encode())
            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e), "stderr": e.stderr.decode()}).encode())
            return
        self.send_response(404); self.end_headers()
    def log_message(self, format, *args): passwith socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("HF Downloader listening on :" + str(PORT))
    httpd.serve_forever()
PYEOF
        exec ${pkgs.python3}/bin/python3 "${"$"}{SOVEREIGN_HOME}/.state/hf_downloader.py"
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{HF_DOWNLOADER}/health || exit 1";
          initial_delay_seconds = 1;
          period_seconds = 3;
          failure_threshold = 5;
        };
      };
    };
    llama-herder = {
      exec = ''
        cd "${SOV_HOME}/tools/llamaherder" 2>/dev/null || cd "${SOV_HOME}"
        exec ${llama-herder-pkg}/bin/llama-herder
      '';
      process-compose = {
        depends_on.llama-server.condition = "process_healthy";
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{LLAMA_HERDER}/health || exit 1";
          initial_delay_seconds = 2;
          period_seconds = 5;
          failure_threshold = 10;
        };
      };
    };
    openfang = {
      exec = ''
        while true; do
          /home/toxic/.openfang/bin/openfang start || true
          sleep 4
        done
      '';
      process-compose = {
        availability.restart = "always";
      };
    };
    sovereign_watchdog = {
      exec = ''
        exec ${sovereign-watchdog-pkg}/bin/sovereign-watchdog
      '';
      process-compose = {
        availability.restart = "on_failure";
        max_restarts = 5;
      };
    };
    telethon_overlord = {
      exec = ''
        exec ${telethon-overlord-pkg}/bin/telethon-overlord
      '';
      process-compose = {
        availability.restart = "on_failure";
        max_restarts = 3;
      };
    };
    prometheus = {
      exec = ''
        ${pkgs.prometheus}/bin/prometheus \\
          --config.file="${SOV_HOME}/prometheus.yml" \\
          --storage.tsdb.path="${PROMETHEUS_DATA}" \\
          --web.listen-address=0.0.0.0:${"$"}{PROMETHEUS_PORT}
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{PROMETHEUS_PORT}/-/healthy || exit 1";
          initial_delay_seconds = 3;
          period_seconds = 5;
        };
      };
    };
    rust-web = {
      exec = ''
        cd "${SOV_HOME}/rust_algo_web"
        exec cargo run --release
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{RUST_WEB_PORT}/health || exit 1";
          initial_delay_seconds = 5;
          period_seconds = 5;
          failure_threshold = 10;
        };
      };
    };
    nfcot-proxy = {
      exec = ''
        cd "${SOV_HOME}"
        exec ${pkgs.python3}/bin/python3 -m modules.nfcot_proxy
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{NFCOT_PORT}/v1/models || exit 1";
          initial_delay_seconds = 3;
          period_seconds = 5;
          failure_threshold = 10;
        };
      };
    };
    node-exporter = {
      exec = ''
        exec ${pkgs.prometheus-node-exporter}/bin/node_exporter \\
          --web.listen-address=:9100 \\
          --path.rootfs=/host
      '';
      process-compose = {
        readiness_probe = {
          exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:9100/metrics >/dev/null || exit 1";
          initial_delay_seconds = 1;
          period_seconds = 5;
        };
      };
    };
    # FIXED: trafficserver moved from services to processes (devenv has no native service)
    trafficserver = {
      exec = ''
        exec ${pkgs.trafficserver}/bin/traffic_server \\
          --port ${toString PORTS.trafficserver}
      '';
      process-compose = {
        availability.restart = "on_failure";
      };
    };
  };