{ config, pkgs, lib, inputs, ... }:
{
  imports = [
    ./modules/lib.nix
    ./modules/packages.nix
    ./modules/processes.nix
    ./modules/services.nix
    ./modules/scripts.nix
    ./modules/tasks.nix
    ./modules/enter-shell.nix
  ];

  # Minimal top-level glue only.
  # All real configuration lives in the modules above.
  packages = with pkgs; [
    git curl jq fd ripgrep nixfmt
    python3 python3Packages.uv
    bun rustc cargo go
  ];

  languages = {
    python.enable = true;
    python.uv.enable = true;
    rust.enable = true;
    go.enable = true;
    nix.enable = true;
    nix.lsp.enable = true;
  };
}
