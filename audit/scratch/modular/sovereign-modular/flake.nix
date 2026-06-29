{
  description = "Sovereign Maximal Stack";
  nixConfig = {
  extra-substituters = "https://nixpkgs-python.cachix.org";
  extra-trusted-public-keys = "nixpkgs-python.cachix.org-1:hxjI7pFxTyuTHn2NkvWCrAUcNZLNS3ZAvfYNuYifcEU=";
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

outputs = { self, nixpkgs, devenv, ... } @ inputs:
  let
    systems = [ "x86_64-linux" ];
    forEachSystem = f: nixpkgs.lib.genAttrs systems (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
            permittedInsecurePackages = [
              "minio-2025-10-15T17-29-55Z"
            ];
          };
        };
      in
      f { inherit pkgs system; }
    );
  in {
    devShells = forEachSystem ({ pkgs, system, ... }: {
      default = devenv.lib.mkShell {
        inherit inputs pkgs;
        modules = [ ./devenv.nix ];
      };
    });
  };
}
