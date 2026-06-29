{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS beellama-src hfhub-src hfxet-wheel beellama-cpp llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
  services = {
    # Web server
    caddy = {
      enable = true;
      config = caddyConfig;
    };
    # Databases
    postgres = {
      enable = true;
      listen_addresses = "127.0.0.1,::1";
      port = PORTS.postgres;
      initialDatabases = [{ name = "sovereign"; }];
      initialScript = ''
        CREATE USER sovereign WITH PASSWORD 'sovereign' SUPERUSER;
        GRANT ALL PRIVILEGES ON DATABASE sovereign TO sovereign;
      '';
    };
    redis = {
      enable = true;
      bind = "127.0.0.1";
      port = PORTS.redis;
    };
    mysql = {
      enable = true;
      initialDatabases = [{ name = "sovereign"; }];
    };
    mongodb = {
      enable = true;
      additionalArgs = ["--noauth"];
    };
    clickhouse = {
      enable = true;
      httpPort = PORTS.clickhouse-http;
      # Note: devenv has native tcpPort option but clickhouse requires some configs
    };
    elasticsearch = {
      enable = true;
      port = PORTS.elasticsearch;
      single_node = true;
    };
    opensearch = {
      enable = true;
    };
    # Message queues
    kafka = {
      enable = true;
      defaultMode = "kraft";
    };
    nats = {
      enable = true;
      port = PORTS.nats;
      host = "127.0.0.1";
      monitoring = {
        enable = true;
        port = PORTS.nats-monitoring;
      };
      jetstream = {
        enable = true;
        maxMemory = "1G";
        maxFileStore = "10G";
      };
    };
    mosquitto = {
      enable = true;
      port = PORTS.mosquitto;
    };
    # Object storage
    #minio = {
    #  enable = true;
    #  accessKey = "minioadmin";
    #  secretKey = "minioadmin";
    #};
    # CDN — REMOVED from services, moved to processes (devenv has no native trafficserver service)
    # trafficserver = { enable = true; };  # DOES NOT EXIST in devenv
    # Profiling — REMOVED (devenv has no native blackfire service)
    # blackfire = { enable = true; socket = "tcp://127.0.0.1:${toString PORTS.blackfire}"; };
  };
}
