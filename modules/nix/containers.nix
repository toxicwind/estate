{
  config,
  pkgs,
  lib,
  inputs,
  ...
}:
let
  shared = import ./lib.nix {
    inherit
      config
      pkgs
      lib
      inputs
      ;
  };
  inherit (shared._module.args) configToml secretspecToml prometheusYml;
in
{
  containers = {
    shell = {
      name = "sovereign-shell";
      copyToRoot = [
        configToml
        secretspecToml
        prometheusYml
      ];
    };
    processes = {
      name = "sovereign-stack";
      copyToRoot = [
        configToml
        secretspecToml
        prometheusYml
      ];
    };
  };
}
