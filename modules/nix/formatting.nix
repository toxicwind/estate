{ inputs, ... }:

{
  # devenv's treefmt – this is what runs on `direnv reload`
  treefmt = {
    enable = true;

    config = {
      projectRootFile = "flake.nix";

      programs = {
        nixfmt.enable = true;
        statix.enable = true;
        deadnix.enable = true;
      };

      settings = {
        # treefmt-nix uses gitignore globs
        global.excludes = [
          ".git/**"
          "result/**"
          "**/*.md"
          "LICENSE"
          "audit/**" # <-- this finally skips your scratch files
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

  # keep `nix fmt` in sync (optional)
  _module.args.perSystem = { pkgs, ... }: {
    formatter = inputs.treefmt-nix.lib.mkWrapper pkgs {
      projectRootFile = "flake.nix";
      programs = {
        nixfmt.enable = true;
        statix.enable = true;
        deadnix.enable = true;
      };
      settings.global.excludes = [
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
    };
  };
}
