_: {
  languages = {
    python = {
      enable = true;
      uv.enable = true;
      venv.enable = true;
    };
    rust.enable = true;
    go.enable = true;
    javascript = {
      enable = true;
      bun = {
        enable = true;
        install.enable = true;
      };
    };
    nix = {
      enable = true;
      lsp.enable = true;
    };
  };

  # this is the devenv-native treefmt (not perSystem)
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
      };
    };
  };
}
