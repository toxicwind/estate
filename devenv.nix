{ config, pkgs, lib, inputs, ... }:
{
  imports = [
    ./modules/nix/packages.nix
    ./modules/nix/processes.nix
    ./modules/nix/services.nix
    ./modules/nix/scripts.nix
    ./modules/nix/tasks.nix
    ./modules/nix/enter-shell.nix
    ./modules/nix/env.nix
    ./modules/nix/git-hooks.nix
    ./modules/nix/containers.nix
    ./modules/nix/tests.nix
  ];
}
