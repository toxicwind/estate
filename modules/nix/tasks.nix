{
  config,
  pkgs,
  lib,
  inputs,
  ...
}:
let
  shared = import ./lib.nix {
    inherit
      config
      pkgs
      lib
      inputs
      ;
  };
  inherit (shared._module.args)
    SOV_HOME
    PORTS
    configToml
    secretspecToml
    prometheusYml
    ;
in
{
  tasks = {
    "sovereign:setup".exec = ''
            mkdir -p "${SOV_HOME}/.state" "${SOV_HOME}/models/hf" "${SOV_HOME}/.prometheus" "${SOV_HOME}/logs" "${SOV_HOME}/data" "${SOV_HOME}/backups"

            cat > "${SOV_HOME}/config.toml" <<'EOF'
      ${configToml}
      EOF

            cat > "${SOV_HOME}/secretspec.toml" <<'EOF'
      ${secretspecToml}
      EOF

            cat > "${SOV_HOME}/prometheus.yml" <<'EOF'
      ${prometheusYml}
      EOF

            echo "✓ Setup complete → ${SOV_HOME}"
    '';

    "sovereign:clean-logs".exec = ''
      find "${SOV_HOME}/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
      find "${SOV_HOME}/ctx_bruteforce_logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
      echo "✓ Old logs cleaned"
    '';

    "sovereign:clean-models".exec = ''
      find "${SOV_HOME}/models/hf" -type d -empty -delete 2>/dev/null || true
      echo "✓ Empty model dirs cleaned"
    '';

    "sovereign:clean-all".exec = ''
      rm -rf "${SOV_HOME}/logs"/* "${SOV_HOME}/.state"/*
      echo "✓ Logs and state wiped"
    '';

    "sovereign:health".exec = ''
      echo "=== Sovereign Stack Health ==="
      for svc in ${
        toString (lib.attrValues (lib.filterAttrs (n: _v: n != "caddy-admin" && n != "prometheus") PORTS))
      }; do
        if ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/health" >/dev/null 2>&1 || \
           ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/-/healthy" >/dev/null 2>&1 || \
           ${pkgs.curl}/bin/curl -sf "http://localhost:$svc/v1/models" >/dev/null 2>&1; then
          echo " ✓ :$svc"
        else
          echo " ✗ :$svc — DOWN"
        fi
      done
    '';

    "sovereign:ports".exec = ''
      echo "=== Sovereign Ports ==="
      ${lib.concatStringsSep "\n" (
        lib.mapAttrsToList (name: port: "echo ' ${name}: ${toString port}'") PORTS
      )}
    '';

    "sovereign:status".exec = ''
      echo "SOV_HOME: ${SOV_HOME}"
      echo "--- disk usage ---"
      du -sh "${SOV_HOME}"/* 2>/dev/null | sort -h || true
    '';

    "sovereign:logs".exec = ''
      echo "Tailing logs (Ctrl-C to exit)..."
      tail -n 50 -f "${SOV_HOME}/logs"/*.log 2>/dev/null || echo "No logs found in ${SOV_HOME}/logs"
    '';

    "sovereign:backup".exec = ''
      TIMESTAMP=$(date +%Y%m%d_%H%M%S)
      BACKUP_DIR="${SOV_HOME}/backups/$TIMESTAMP"
      mkdir -p "$BACKUP_DIR"
      cp "${SOV_HOME}/config.toml" "${SOV_HOME}/secretspec.toml" "${SOV_HOME}/prometheus.yml" "$BACKUP_DIR/" 2>/dev/null
      echo "✓ Backup created → $BACKUP_DIR"
    '';

    "sovereign:reset".exec = ''
      read -p "Wipe state and logs? [y/N] " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "${SOV_HOME}/.state" "${SOV_HOME}/logs"
        mkdir -p "${SOV_HOME}/.state" "${SOV_HOME}/logs"
        echo "✓ Sovereign reset complete"
      else
        echo "Cancelled"
      fi
    '';

    "sovereign:test".exec = ''
      bun run "$DEVENV_ROOT/tests/test_stack.ts"
    '';

    "sovereign:graph" = {
      description = "Compile system topology (d2) + process graph (Mermaid) and update docs";
      exec = ''
            mkdir -p "${SOV_HOME}/docs"

            # --- System topology (d2) ---
            cat > "${SOV_HOME}/architecture.d2" <<'D2EOF'
        direction: down
        vars: {
          dcolor: "#1e1e2e"
          stroke: "#cba6f7"
          font: "#cdd6f4"
        }
        style: {
          fill: "#11111b"
          font-color: "$.vars.font"
          stroke: "#45475a"
          border-radius: 6
        }
        devenv: devenv.nix {
          style.fill: "#313244"
          style.stroke: "$.vars.stroke"
        }
        nix_modules: Nix Orchestration Layer {
          style.fill: "#181825"
          lib: "lib.nix"
          packages: "packages.nix"
          processes: "processes.nix"
          services: "services.nix"
          scripts: "scripts.nix"
          tasks: "tasks.nix"
          tests: "tests.nix"
          shell: "enter-shell.nix"
        }
        runtime_core: TypeScript Core Runtime {
          style.fill: "#181825"
          watchdog: "src/watchdog.ts"
          yote: "src/yote.ts"
          proxy: "modules/nfcot_proxy.py"
          bench: "src/prompt_cache_benchmark.ts"
        }
        devenv -> nix_modules.lib
        devenv -> nix_modules.packages
        devenv -> nix_modules.processes
        devenv -> nix_modules.services
        devenv -> nix_modules.scripts
        devenv -> nix_modules.tasks
        devenv -> nix_modules.tests
        devenv -> nix_modules.shell
        nix_modules.processes -> runtime_core.watchdog: Spawns
        nix_modules.processes -> runtime_core.yote: Spawns
        nix_modules.processes -> runtime_core.proxy: Spawns
        nix_modules.processes -> nix_modules.lib: References Matrix
        nix_modules.services -> nix_modules.lib: References Matrix
        D2EOF

            ${pkgs.d2}/bin/d2 --theme=200 --layout=elk --pad=30 \
              "${SOV_HOME}/architecture.d2" "${SOV_HOME}/architecture.svg" || true

            # --- Process graph (Mermaid) with stolen styling ---
            cat > "${SOV_HOME}/architecture.mmd" <<'MMDEOF'
        graph TD
          Caddy["Caddy<br/>gateway"] --> landing
          Caddy --> llama-server
          Caddy --> openfang
          Caddy --> nfcot
          Caddy --> rust-web
          Caddy --> hf-downloader
          Caddy --> llama-herder
          Caddy --> watchdog
          Caddy --> overlord

          llama-herder --> llama-server
          overlord --> watchdog
          watchdog --> llama-server
          watchdog --> openfang
          watchdog --> nfcot
          watchdog --> rust-web
          watchdog --> hf-downloader
          watchdog --> llama-herder
          watchdog --> overlord

          prometheus --> llama-server
          prometheus --> watchdog

          classDef gateway fill:#7c3aed,stroke:#c4b5fd,stroke-width:3px,color:#fff,rx:12,ry:12;
          classDef ai fill:#ec4899,stroke:#f9a8d4,stroke-width:2px,color:#fff,rx:10;
          classDef infra fill:#0ea5e9,stroke:#7dd3fc,stroke-width:2px,color:#fff,rx:10;
          classDef app fill:#10b981,stroke:#6ee7b7,stroke-width:2px,color:#fff,rx:10;

          class Caddy gateway;
          class llama-server,llama-herder,openfang,nfcot,hf-downloader ai;
          class watchdog,overlord,prometheus infra;
          class landing,rust-web,postgres,redis,mysql,mongodb,kafka,nats,mosquitto,clickhouse,elasticsearch,opensearch,trafficserver,blackfire,node-exporter app;
        MMDEOF

            echo "✓ Generated architecture.svg + architecture.mmd"

            # Copy interactive studio if it exists in repo root/docs
            if [ -f "${SOV_HOME}/docs/devenv-graph.html" ]; then
              echo "✓ Interactive studio present at docs/devenv-graph.html"
            fi
      '';
    };

    "devenv:enterShell".after = [ "sovereign:setup" ];
  };
}
