  tasks = {
    "sovereign:setup".exec = ''
      mkdir -p "${SOV_HOME}/.state" "${SOV_HOME}/models/hf" "${SOV_HOME}/.prometheus" "${SOV_HOME}/logs" "${SOV_HOME}/data"
      cp -f ${configToml} "${SOV_HOME}/config.toml"
      cp -f ${secretspecToml} "${SOV_HOME}/secretspec.toml"
      cp -f ${prometheusYml} "${SOV_HOME}/prometheus.yml"
      echo "✓ Setup complete"
    '';
    "sovereign:clean-logs".exec = ''
      find "${SOV_HOME}/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
      find "${SOV_HOME}/ctx_bruteforce_logs" -name "*.log" -mtime +7 -delete 2>/dev/null ||
true
      echo "✓ Old logs cleaned"
    '';
    "sovereign:health".exec = ''
      echo "=== Sovereign Stack Health ==="
      for svc in ${toString PORTS.llama-server} ${toString PORTS.hf-downloader} ${toString PORTS.llama-herder} ${toString PORTS.prometheus} ${toString PORTS.rust-web} ${toString PORTS.nfcot}; do
        if ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/health" >/dev/null 2>&1 || ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/-/healthy" >/dev/null 2>&1 || ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/v1/models" >/dev/null 2>&1; then
          echo "  ✓ :$svc"
        else
          echo "  ✗ :$svc — DOWN"
        fi
      done
    '';
    "devenv:enterShell".after = [ "sovereign:setup" ];
  };