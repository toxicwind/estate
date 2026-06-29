  languages = {
    python = {
      enable = true;
      # FIXED: removed hardcoded version = "3.12" — let devenv use nixpkgs default
      # or set via: package = pkgs.python3;
      uv.enable = true;
      venv.enable = true;
    };
    rust = {
      enable = true;
    };
    go = {
      enable = true;
    };
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