{ config, pkgs, ... }:
let
  inherit (config._module.args) PORTS;
  SOV_HOME = config.env.DEVENV_ROOT or ".";
  curl = "${pkgs.curl}/bin/curl";
in
{
  processes = {
    # CORE
    landing.exec = ''
      cd "${SOV_HOME}/src/landing" 2>/dev/null || cd "${SOV_HOME}"
      exec ${pkgs.bun}/bin/bun run "${SOV_HOME}/src/landing/server.ts"
    '';
    landing.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.landing}/health";
      initial_delay = 2;
      period = 5;
      probe_timeout = 3;
      failure_threshold = 10;
    };

    llama-server.exec = ''
      exec ${pkgs.llama-cpp}/bin/llama-server \
        -m "$MODEL_PATH" \
        --host 0.0.0.0 --port "''${LLAMA_SERVER_PORT:-${toString PORTS.llama-server}}" \
        -c 32768 --slots 1 -b 4096 --flash-attn auto -ngl 99 --metrics \
        --embeddings --pooling cls --cache-type-k q4_0 --cache-type-v q4_0 \
        --no-mmap --mlock
    '';
    llama-server.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.llama-server}/health";
      initial_delay = 15;
      period = 5;
      probe_timeout = 5;
      failure_threshold = 30;
    };
    llama-server.restart = {
      on = "on_failure";
      max = 10;
    };

    nfcot.exec = ''cd "${SOV_HOME}"; exec ${pkgs.python3}/bin/python3 -m modules.nfcot_proxy'';
    nfcot.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.nfcot}/v1/models";
      initial_delay = 3;
      period = 5;
      failure_threshold = 10;
    };

    openfang.exec = "${pkgs.bun}/bin/bun run ${SOV_HOME}/src/openfang.ts";
    openfang.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.openfang}/health";
      initial_delay = 5;
      period = 5;
      probe_timeout = 3;
      failure_threshold = 10;
    };
    openfang.restart = {
      on = "on_failure";
      max = 10;
    };

    rust-web.exec = ''cd "${SOV_HOME}/rust_algo_web"; exec cargo run --release'';
    rust-web.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.rust-web}/health";
      initial_delay = 5;
      period = 5;
      failure_threshold = 10;
    };

    # TOOLS
    hf-downloader.exec = "${pkgs.bun}/bin/bun run ${SOV_HOME}/src/hf_downloader.ts";
    hf-downloader.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.hf-downloader}/health";
      initial_delay = 1;
      period = 3;
      failure_threshold = 5;
    };

    llama-herder.exec = "${pkgs.bun}/bin/bun run ${SOV_HOME}/src/herder.ts";
    llama-herder.after = [ "devenv:processes:llama-server" ];
    llama-herder.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.llama-herder}/health";
      initial_delay = 2;
      period = 5;
      failure_threshold = 10;
    };

    watchdog.exec = "${pkgs.bun}/bin/bun run ${SOV_HOME}/src/watchdog.ts";
    watchdog.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.watchdog}/health";
      initial_delay = 2;
      period = 5;
      failure_threshold = 10;
    };

    overlord.exec = "${pkgs.bun}/bin/bun run ${SOV_HOME}/src/overlord.ts";
    overlord.after = [ "devenv:processes:watchdog" ];
    overlord.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.overlord}/health";
      initial_delay = 2;
      period = 5;
      failure_threshold = 10;
    };

    # OBSERVABILITY
    prometheus.exec = ''
      ${pkgs.prometheus}/bin/prometheus \
        --config.file="${SOV_HOME}/prometheus.yml" \
        --storage.tsdb.path="${SOV_HOME}/.prometheus" \
        --web.listen-address=0.0.0.0:${toString PORTS.prometheus}
    '';
    prometheus.ready = {
      exec = "${curl} -f -s http://localhost:${toString PORTS.prometheus}/-/healthy";
      initial_delay = 3;
      period = 5;
    };

    node-exporter.exec = "${pkgs.prometheus-node-exporter}/bin/node_exporter --web.listen-address=:9100 --path.rootfs=/host";
    node-exporter.ready = {
      exec = "${curl} -f -s http://localhost:9100/metrics";
      initial_delay = 1;
      period = 5;
    };

    # DATABASES
    postgres.exec = ''
      mkdir -p "${SOV_HOME}/.postgres"
      exec ${pkgs.postgresql}/bin/postgres -D "${SOV_HOME}/.postgres" -p ${toString PORTS.postgres} -k "${SOV_HOME}/.postgres"
    '';
    postgres.ready = {
      exec = "${pkgs.postgresql}/bin/pg_isready -p ${toString PORTS.postgres} -h localhost";
      initial_delay = 3;
      period = 5;
      failure_threshold = 10;
    };

    redis.exec = ''exec ${pkgs.redis}/bin/redis-server --port ${toString PORTS.redis} --bind 127.0.0.1 --dir "${SOV_HOME}/.redis" --daemonize no'';
    redis.ready = {
      exec = "${pkgs.redis}/bin/redis-cli -p ${toString PORTS.redis} ping | grep -q PONG";
      initial_delay = 1;
      period = 3;
      failure_threshold = 5;
    };

    mysql.exec = "...your existing mysql block...";
    mysql.ready = {
      exec = "${pkgs.mysql84}/bin/mysqladmin -P ${toString PORTS.mysql} -h 127.0.0.1 ping 2>/dev/null | grep -q alive";
      initial_delay = 5;
      period = 5;
      failure_threshold = 10;
    };

    #... keep the same pattern for mongodb, clickhouse, elasticsearch, opensearch, nats, mosquitto, kafka, trafficserver, blackfire — just move the exec.command into ready.exec and timing fields

    caddy.exec = "...your Caddyfile generation...";
    caddy.ready = {
      exec = "${curl} -f -s http://localhost:80/health";
      initial_delay = 2;
      period = 5;
      failure_threshold = 5;
    };

    "infra-graph-monitor".exec =
      ''exec ${pkgs.watchexec}/bin/watchexec --watch "${SOV_HOME}/modules/nix" --exts nix --postpone "devenv tasks run sovereign:graph"'';
  };
}
