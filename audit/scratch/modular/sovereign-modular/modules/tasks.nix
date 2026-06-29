{ config, pkgs, lib, ... }:
{
  tasks = {
    "sovereign:setup".exec = ''
      mkdir -p "${config.env.SOVEREIGN_HOME}/.state" \
               "${config.env.SOVEREIGN_HOME}/models/hf" \
               "${config.env.SOVEREIGN_HOME}/.prometheus" \
               "${config.env.SOVEREIGN_HOME}/logs"
      echo "✓ Sovereign modular setup complete"
    '';

    "sovereign:health".exec = ''
      echo "=== Sovereign Stack Health (modular) ==="
      for svc in 25001 8080 8081 9090; do
        if curl -sf "http://localhost:$svc/health" >/dev/null 2>&1; then
          echo "  ✓ :$svc"
        else
          echo "  ✗ :$svc — DOWN"
        fi
      done
    '';
  };
}
