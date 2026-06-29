{ config, ... }:
{
  imports = [
    ./modules/nix/lib.nix
    ./modules/nix/containers.nix
    ./modules/nix/enter-shell.nix
    ./modules/nix/env.nix
    ./modules/nix/formatting.nix
    ./modules/nix/git-hooks.nix
    ./modules/nix/languages.nix
    ./modules/nix/processes.nix
    ./modules/nix/scripts.nix
    ./modules/nix/tasks.nix
    ./modules/nix/tests.nix
  ];

  outputs = {
    sovereign-ports = config._module.args.PORTS;
    sovereign-packages = config.packages;
  };
}
