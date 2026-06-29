{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) PORTS;
in
{
  test = {
    exec = ''
      echo "Waiting for services to start..."
      sleep 5
      
      # Test postgres
      echo "Pinging PostgreSQL..."
      ${pkgs.postgresql}/bin/pg_isready -h localhost -p ${toString PORTS.postgres}
      
      # Test redis
      echo "Pinging Redis..."
      ${pkgs.redis}/bin/redis-cli -h localhost -p ${toString PORTS.redis} ping
      
      # Test llamaherd
      echo "Checking LlamaHerd..."
      ${pkgs.curl}/bin/curl -f -s http://localhost:${toString PORTS.llama-herder}/healthz || exit 1
      
      echo "All services successfully verified!"
    '';
  };
}
