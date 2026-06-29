{ pkgs, prebuilts, ... }:
{
  _module.args = {
    beellama-cpp = pkgs.symlinkJoin {
      name = "beellama-cpp";
      paths = [
        (pkgs.writeShellScriptBin "llama-server" ''exec ${prebuilts._module.args.BEELLAMA_BIN} "$@"'')
        (pkgs.writeShellScriptBin "llama-cli" ''exec ${prebuilts._module.args.BEELLAMA_BIN} "$@"'')
      ];
    };

    sovereign-watchdog-pkg = pkgs.writers.writePython3Bin "sovereign-watchdog" {
      libraries = with pkgs.python3Packages; [
        requests
        psutil
      ];
    } ''print("watchdog stub")'';

    telethon-overlord-pkg = pkgs.writers.writePython3Bin "telethon-overlord" {
      libraries = with pkgs.python3Packages; [
        telethon
        requests
        pydantic
      ];
    } ''print("overlord stub")'';
  };
}
