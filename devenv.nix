{ config, ... }:
{
  imports = [
    ./modules/nix/lib.nix
    ./modules/nix/containers.nix
    ./modules/nix/enter-shell.nix
    ./modules/nix/env.nix
    ./modules/nix/git-hooks.nix
    ./modules/nix/languages.nix
    ./modules/nix/processes.nix
    ./modules/nix/scripts.nix
    ./modules/nix/tasks.nix
    ./modules/nix/tests.nix
  ];

  treefmt = {
    enable = true;

    config = {
      projectRootFile = "flake.nix";

      programs = {
        nixfmt.enable = true;
        statix.enable = true;
        deadnix.enable = true;
        shfmt.enable = true;
        prettier.enable = true;
      };

      settings = {
        global.excludes = [
          ".git/**"
          "result/**"
          "**/*.md"
          "LICENSE"
          "audit/**"
          ".devenv/**"
          ".direnv/**"
          "node_modules/**"
          "target/**"
          "dist/**"
          "build/**"
          "*.log"
          "tmp/**"
          "temp/**"
        ];

        formatter = {
          deadnix.priority = 1;
          statix.priority = 2;
          nixfmt.priority = 3;
        };
      };
    };
  };

  outputs = {
    sovereign-ports = config._module.args.PORTS;
    sovereign-packages = config.packages;
  };
}
