{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) PORTS;
in
{
  # devenv test expects a package (script), not a raw attrset
  test = pkgs.writeShellScript "sovereign-test" ''
    set -e
    echo "Waiting for services to start..."
    sleep 5

    echo "Pinging PostgreSQL..."
    ${pkgs.postgresql}/bin/pg_isready -h localhost -p ${toString PORTS.postgres}

    echo "Pinging Redis..."
    ${pkgs.redis}/bin/redis-cli -h localhost -p ${toString PORTS.redis} ping

    echo "Checking llama-swap..."
    ${pkgs.curl}/bin/curl -f -s http://localhost:${toString PORTS.llama-herder}/health || exit 1

    echo "All services verified!"
  '';
}
