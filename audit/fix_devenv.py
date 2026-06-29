import sys

with open('devenv.nix', 'r') as f:
    data = f.read()

# 1. Deduplicate beellama-cpp overrideAttrs
bad_bee = """    preConfigure = ''
      export NIX_ENFORCE_NO_NATIVE=0
      ${oldAttrs.preConfigure or ""}
    '';
    npmDepsHash = "sha256-1iM0LGeI9e+gZEHk46lkBe51DxIhiimfAm9o3Z3m9Ik=";
      export NIX_ENFORCE_NO_NATIVE=0
      ${oldAttrs.preConfigure or ""}
    '';
    npmDepsHash = "sha256-1iM0LGeI9e+gZEHk46lkBe51DxIhiimfAm9o3Z3m9Ik=";
  });"""

good_bee = """    preConfigure = ''
      export NIX_ENFORCE_NO_NATIVE=0
      ${oldAttrs.preConfigure or ""}
    '';
    npmDepsHash = "sha256-1iM0LGeI9e+gZEHk46lkBe51DxIhiimfAm9o3Z3m9Ik=";
  });"""

data = data.replace(bad_bee, good_bee)

# 2. Repair llama-herder-pkg and restore the deleted languages block
bad_herder = """  llama-herder-pkg = pkgs.python3Packages.buildPythonApplication {
    pname = "llama-herder";
    version = "0.1.0";
    src = pkgs.writeTextDir "app.py"
from flask import Flask
app = Flask(__name__)
@app.route("/health")
def health(): return "OK"
if __name__ == "__main__": app.run(host="0.0.0.0", port=8081)
;
    format = "pyproject";
    propagatedBuildInputs = with pkgs.python3Packages; [ flask requests pydantic uvicorn ];
    doCheck = false;
  };"""

good_herder_def = """  llama-herder-pkg = pkgs.python3Packages.buildPythonApplication {
    pname = "llama-herder";
    version = "0.1.0";
    src = if builtins.pathExists "${SOV_HOME}/tools/llamaherder/pyproject.toml"
          then "${SOV_HOME}/tools/llamaherder"
          else pkgs.writeTextDir "app.py" ''
            from flask import Flask
            app = Flask(__name__)
            @app.route("/health")
            def health(): return "OK"
            if __name__ == "__main__": app.run(host="0.0.0.0", port=8081)
          '';
    format = "pyproject";
    propagatedBuildInputs = with pkgs.python3Packages; [ flask requests pydantic uvicorn ];
    doCheck = false;
  };"""

# Replace the top-level definition
data = data.replace(bad_herder, good_herder_def, 1)

packages_tail_and_languages = """    llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg
  ];
  # ═══════════════════════════════════════════════════════════════════
  # LANGUAGES — Enable LSP and tooling
  # ═══════════════════════════════════════════════════════════════════
  languages = {
    python = {
      enable = true;
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
  };"""

# Replace the corrupted array terminator with the restored block
data = data.replace(bad_herder, packages_tail_and_languages, 1)

with open('devenv.nix', 'w') as f:
    f.write(data)
