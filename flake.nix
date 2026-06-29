{
  description = "Sovereign Maximal Stack";
  nixConfig = {
    extra-substituters = [
      "https://devenv.cachix.org"
      "https://nix-community.cachix.org"
      "https://nixpkgs-python.cachix.org"
      "https://cuda-maintainers.cachix.org"
    ];
    extra-trusted-public-keys = [
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      "nixpkgs-python.cachix.org-1:hxjI7pFxTyuTHn2NkvWCrAUcNZLNS3ZAvfYNuYifcEU="
      "cuda-maintainers.cachix.org-1:0dq3bujKpuEPMCX6U4WylrUDZ9JyUG0VpVZa7CNfq5E="
    ];
  };
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    nixpkgs-python.inputs.nixpkgs.follows = "nixpkgs";
    rust-overlay.url = "github:oxalica/rust-overlay";
    rust-overlay.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs =
    { nixpkgs, devenv, ... }@inputs:
    let
      systems = [ "x86_64-linux" ];
      forEachSystem =
        f:
        nixpkgs.lib.genAttrs systems (
          system:
          let
            pkgs = import nixpkgs {
              inherit system;
              config = {
                allowUnfree = true;
                cudaSupport = true;
              };
            };
          in
          f { inherit pkgs system; }
        );
    in
    {
      devShells = forEachSystem (
        { pkgs, ... }: {
          default = devenv.lib.mkShell {
            inherit inputs pkgs;
            modules = [ ./devenv.nix ];
          };
        }
      );
    };
}
