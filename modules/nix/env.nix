{
  config,
  pkgs,
  lib,
  inputs,
  ...
}:
let
  shared = import ./lib.nix {
    inherit
      config
      pkgs
      lib
      inputs
      ;
  };
  inherit (shared._module.args) PORTS;
in
{
  env = {
    LLAMA_SERVER_PORT = toString PORTS.llama-server;
    OPENFANG_PORT = toString PORTS.openfang;
    NFCOT_PORT = toString PORTS.nfcot;
    RUST_WEB_PORT = toString PORTS.rust-web;
    LANDING_PAGE = toString PORTS.landing;
    HF_DOWNLOADER = toString PORTS.hf-downloader;
    LLAMA_HERDER = toString PORTS.llama-herder;
    PROMETHEUS_PORT = toString PORTS.prometheus;
  };
}
