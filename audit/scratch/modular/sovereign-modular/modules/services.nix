{ config, pkgs, lib, ... }:
let
  shared = import ./lib.nix { inherit pkgs lib; };
in
{
  services = {
    caddy = {
      enable = true;
      config = ''
        {
          admin 0.0.0.0:${toString shared.PORTS.caddy-admin}
          auto_https off
        }
        :80 {
          handle /health { respond "OK" 200 }
          handle_path /rank*  { reverse_proxy localhost:${toString shared.PORTS.rust-web} }
          handle_path /api/*  { reverse_proxy localhost:${toString shared.PORTS.rust-web} }
          handle_path /llm*   { reverse_proxy localhost:${toString shared.PORTS.llama-server} }
          handle_path /fang*  { reverse_proxy localhost:${toString shared.PORTS.openfang} }
          handle_path /cot*   { reverse_proxy localhost:${toString shared.PORTS.nfcot} }
          handle_path /hf/*   { reverse_proxy localhost:${toString shared.PORTS.hf-downloader} }
          handle_path /herder/* { reverse_proxy localhost:${toString shared.PORTS.llama-herder} }
          handle_path /landing/* { reverse_proxy localhost:${toString shared.PORTS.landing} }
          handle { reverse_proxy localhost:${toString shared.PORTS.rust-web} }
        }
      '';
    };

    postgres = {
      enable = true;
      listen_addresses = "127.0.0.1,::1";
      port = shared.PORTS.postgres;
      initialDatabases = [{ name = "sovereign"; }];
      initialScript = ''
        CREATE USER sovereign WITH PASSWORD 'sovereign' SUPERUSER;
        GRANT ALL PRIVILEGES ON DATABASE sovereign TO sovereign;
      '';
    };

    redis = {
      enable = true;
      bind = "127.0.0.1";
      port = shared.PORTS.redis;
    };

    clickhouse = {
      enable = true;
      port = shared.PORTS.clickhouse;
      httpPort = shared.PORTS.clickhouse-http;
    };

    nats = {
      enable = true;
      port = shared.PORTS.nats;
      host = "127.0.0.1";
      monitoring.enable = true;
      monitoring.port = 8222;
      jetstream = {
        enable = true;
        maxMemory = "1G";
        maxFileStore = "10G";
      };
    };

    mosquitto = {
      enable = true;
      port = shared.PORTS.mosquitto;
    };

    # Add mysql, mongodb, elasticsearch, kafka etc. here when needed.
    # They were in the monolith; move them as you use them.
  };
}
