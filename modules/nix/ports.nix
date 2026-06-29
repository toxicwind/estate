# modules/nix/ports.nix
# Plain attrset — NOT a module. No _module.args, no function args.
{
  landing = 25000;
  llama-server = 25001;
  nfcot = 25003;
  openfang = 25004;
  rust-web = 25005;

  hf-downloader = 25020;
  llama-herder = 25021;
  watchdog = 25022;
  overlord = 25023;

  prometheus = 25030;
  caddy-admin = 25031;

  postgres = 5432;
  redis = 6379;
  nats = 4222;
  nats-monitoring = 8222;
  mosquitto = 1883;
  clickhouse = 19000;
  clickhouse-http = 18123;
  elasticsearch = 9200;
  opensearch = 9201;
  kafka = 9092;
  mysql = 3306;
  mongodb = 27017;

  trafficserver = 8082;
  blackfire = 8307;
}
