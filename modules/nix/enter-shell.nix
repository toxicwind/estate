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
  inherit (shared._module.args) PORTS;

  # build a printf line for each port, sorted alphabetically
  portLines = lib.concatStringsSep "\n" (
    map (name: ''printf "  %-16s :%s\n" "${name}" "${toString PORTS.${name}}"'') (
      lib.sort (a: b: a < b) (lib.attrNames PORTS)
    )
  );
in
{
  enterShell = ''
    echo "🚀 Sovereign Stack — Maximal Modular (Clean Ports)"
    ${portLines}
  '';
}
