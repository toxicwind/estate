{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS BEELLAMA_BIN IK_LLAMA_BIN QUANT_BIN beellama-cpp sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
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
      def log_message(self, format, *args): pass
  
  with socketserver.TCPServer(("", PORT), Handler) as httpd:
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
      llama-swap = {
        exec = ''
          exec ${SOV_HOME}/tools/llama-swap/llama-swap \
            --config "${SOV_HOME}/tools/llama-swap/config.yaml" \
            --listen "0.0.0.0:${toString PORTS.llama-herder}"
        '';
        process-compose = {
          readiness_probe = {
            exec.command = "${pkgs.curl}/bin/curl -f -s http://localhost:${"$"}{LLAMA_HERDER}/health || exit 1";
            initial_delay_seconds = 2;
            period_seconds = 5;
            failure_threshold = 10;
          };
          availability = {
            restart = "on_failure";
            backoff_seconds = 3;
            max_restarts = 5;
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
          exec ${pkgs.bun}/bin/bun run ${SOV_HOME}/modules/src/watchdog.ts
        '';
        process-compose = {
          availability.restart = "on_failure";
          max_restarts = 5;
        };
      };
      yote = {
        exec = ''
          exec ${pkgs.bun}/bin/bun run ${SOV_HOME}/modules/src/yote.ts
        '';
        process-compose = {
          availability.restart = "on_failure";
          max_restarts = 5;
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
          exec ${pkgs.bun}/bin/bun run ${SOV_HOME}/modules/src/nfcot_proxy.ts
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
}
