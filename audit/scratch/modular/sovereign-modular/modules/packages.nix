{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit pkgs lib; };
in
{
  # BeeLlama with CUDA + native
  beellama-cpp = (pkgs.llama-cpp.override {
    cudaSupport = true;
    rocmSupport = false;
    metalSupport = false;
    blasSupport = true;
  }).overrideAttrs (oldAttrs: rec {
    pname = "beellama-cpp";
    version = "main";
    src = shared.beellama-src;
    cmakeFlags = (oldAttrs.cmakeFlags or []) ++ [
      "-DGGML_NATIVE=ON"
      "-DGGML_CUDA_FA_ALL_QUANTS=ON"
    ];
    preConfigure = ''
      export NIX_ENFORCE_NO_NATIVE=0
      ${oldAttrs.preConfigure or ""}
    '';
  });

  # Custom Python packages
  llama-herder-pkg = pkgs.writeScriptBin "llama-herder" ''
    #!${pkgs.python3}/bin/python3
    from flask import Flask
    app = Flask(__name__)
    @app.route("/health")
    def health(): return "OK"
    if __name__ == "__main__": app.run(host="0.0.0.0", port=${toString shared.PORTS.llama-herder})
  '';

  sovereign-watchdog-pkg = pkgs.python3Packages.buildPythonApplication {
    pname = "sovereign-watchdog";
    version = "0.1.0";
    src = pkgs.writeTextDir "watchdog.py" "print('watchdog stub')";
    format = "pyproject";
    propagatedBuildInputs = with pkgs.python3Packages; [ requests psutil ];
    doCheck = false;
  };

  telethon-overlord-pkg = pkgs.python3Packages.buildPythonApplication {
    pname = "telethon-overlord";
    version = "0.1.0";
    src = pkgs.writeTextDir "overlord.py" "print('overlord stub')";
    format = "pyproject";
    propagatedBuildInputs = with pkgs.python3Packages; [ telethon requests pydantic ];
    doCheck = false;
  };
}
