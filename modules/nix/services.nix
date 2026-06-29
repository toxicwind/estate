# modules/nix/services.nix
{ config, ... }:

{
  # ═══════════════════════════════════════════════════════════════════
  # ALL OTHER SERVICES DISABLED — we manage these manually in processes.nix
  # ═══════════════════════════════════════════════════════════════════
  services.postgres.enable = false;
  services.caddy.enable = false;
  services.redis.enable = false;
  services.mysql.enable = false;
  services.mongodb.enable = false;
  services.clickhouse.enable = false;
  services.elasticsearch.enable = false;
  services.opensearch.enable = false;
  services.kafka.enable = false;
  services.nats.enable = false;
  services.mosquitto.enable = false;
}
