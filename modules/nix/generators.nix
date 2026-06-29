{
  pkgs,
  ports,
  lib,
  ...
}:
let
  p = ports;

  # === Single source of truth for what to scrape ===
  scrapeJobs = {
    prometheus = {
      port = p.prometheus;
      path = "/metrics";
      interval = "10s";
    };
    "llama-server" = {
      port = p."llama-server";
      path = "/metrics";
      interval = "5s";
    };
    nfcot = {
      port = p.nfcot;
      path = "/metrics";
    };
    openfang = {
      port = p.openfang;
      path = "/metrics";
    };
    "rust-web" = {
      port = p."rust-web";
      path = "/metrics";
    };
    "hf-downloader" = {
      port = p."hf-downloader";
      path = "/metrics";
    };
    "llama-herder" = {
      port = p."llama-herder";
      path = "/metrics";
    };

    # Databases / exporters (use default exporter ports)
    postgres = {
      port = 9187;
    };
    redis = {
      port = 9121;
    };
    mysql = {
      port = 9104;
    };
    mongodb = {
      port = 9216;
    };
    node = {
      port = 9100;
    };
    kafka = {
      port = 9308;
    };
  };

  # Generate scrape_configs automatically
  scrapeConfigs = lib.mapAttrsToList (
    name: job:
    {
      job_name = name;
      static_configs = [ { targets = [ "localhost:${toString job.port}" ]; } ];
    }
    // (lib.optionalAttrs (job ? path) { metrics_path = job.path; })
    // (lib.optionalAttrs (job ? interval) { scrape_interval = job.interval; })
  ) scrapeJobs;

in
{
  _module.args = {
    prometheusYml = pkgs.writeText "prometheus.yml" (
      builtins.toJSON {
        global = {
          scrape_interval = "15s";
          evaluation_interval = "15s";
          external_labels = {
            cluster = "sovereign";
            environment = "local";
          };
        };

        scrape_configs = scrapeConfigs;
      }
    );

    # Still pull these from real files if you want
    configToml = builtins.readFile ../../config.toml;
    caddyConfig = builtins.readFile ../../Caddyfile;
    secretspecToml = builtins.readFile ../../secretspec.toml;
  };
}
