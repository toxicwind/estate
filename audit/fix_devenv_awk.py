import re

with open('devenv.nix', 'r') as f:
    data = f.read()

# 1. Deduplicate beellama-cpp overrideAttrs (Using regex to handle arbitrary whitespace)
data = re.sub(
    r'(npmDepsHash\s*=\s*"[^"]+";\s*)\n\s*export NIX_ENFORCE_NO_NATIVE=0\n\s*\$\{oldAttrs\.preConfigure or ""\}\n\s*\'\';\n\s*npmDepsHash\s*=\s*"[^"]+";',
    r'\1',
    data,
    flags=re.MULTILINE
)

# 2. Extract everything BEFORE the bad llama-herder-pkg definition
match_before = re.search(r'# CUSTOM PACKAGES\n\s*# ═══════════════════════════════════════════════════════════════════\n', data)
idx_start = match_before.end()

# 3. Extract everything AFTER the bad llama-herder-pkg definition, starting at sovereign-watchdog-pkg
match_after = re.search(r'  sovereign-watchdog-pkg = pkgs\.python3Packages\.buildPythonApplication', data)
idx_end = match_after.start()

prefix = data[:idx_start]
suffix = data[idx_end:]

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
  };

"""

# 4. Splice it together
data = prefix + good_herder_def + suffix

# 5. Fix the end of the packages array and restore languages block (which got eaten by the sed command)
bad_packages_end = """    # Custom
  llama-herder-pkg = pkgs.python3Packages.buildPythonApplication {"""

packages_tail_and_languages = """    # Custom
    llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg
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
  };

  # ═══════════════════════════════════════════════════════════════════
  # ENVIRONMENT"""

# Locate where the packages list was truncated and replace the broken tail
idx_custom = data.rfind("    # Custom")
if idx_custom != -1:
    idx_env = data.find("  # ENVIRONMENT", idx_custom)
    if idx_env != -1:
        data = data[:idx_custom] + packages_tail_and_languages + data[idx_env+15:]
    else:
        print("Could not find environment block after custom packages.")

with open('devenv.nix', 'w') as f:
    f.write(data)
