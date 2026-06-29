{ pkgs, lib, ... }:
let
  SOV = ".";
  SOV_HOME = SOV;
  MODELS = "${SOV_HOME}/models";

  MODELS_MANIFEST = {
    primary = "${MODELS}/StrangeMerges_19-7B-dare_ties.Q4_K_M.gguf";
    draft   = "${MODELS}/Qwen2.5-1.5B-Draft.gguf";
    flash   = "${MODELS}/Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf";
    heretic = "${MODELS}/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf";
    gemma   = "${MODELS}/gemma-4-12B-it-uncensored-Q4_K_M.gguf";
    grand   = "${MODELS}/MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q4_K_M.gguf";
  };

  ACTIVE_MODEL = MODELS_MANIFEST.primary;
  ACTIVE_DRAFT = MODELS_MANIFEST.draft;

  PORTS = {
    llama-server = 25001;
    openfang     = 25004;
    nfcot        = 25008;
    rust-web     = 25010;
    landing      = 25000;
    hf-downloader = 8080;
    llama-herder  = 8081;
    prometheus   = 9090;
    caddy-admin  = 2019;
    redis        = 6379;
    postgres     = 5432;
    clickhouse   = 19000;
    clickhouse-http = 18123;
    nats         = 4222;
    mosquitto    = 1883;
    trafficserver = 8082;
  };

  LLAMA_FLAGS = {
    ctx-size        = 32768;
    slots           = 1;
    batch           = 4096;
    ubatch          = 1024;
    ngl             = 99;
    threads         = 4;
    cache-type-k    = "q4_0";
    cache-type-v    = "q4_0";
    draft-n-ctx     = 4096;
    draft-n-predict = 16;
    draft-ngl       = 99;
  };

  beellama-src = builtins.fetchGit {
    url = "https://github.com/Anbeeld/beellama.cpp.git";
    ref = "main";
    shallow = true;
  };
in
{
  inherit SOV_HOME MODELS MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT
          PORTS LLAMA_FLAGS beellama-src;
}
