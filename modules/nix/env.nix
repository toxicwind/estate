{ config, pkgs, lib, inputs, ... }:
let
  shared = import ./lib.nix { inherit config pkgs lib inputs; };
  inherit (shared) pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS beellama-src hfhub-src hfxet-wheel beellama-cpp llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd;
in
{
  env = {
      # ── Paths ──
      SOVEREIGN_HOME = SOV_HOME;
      MODEL_PATH = ACTIVE_MODEL;
      DRAFT_MODEL_PATH = ACTIVE_DRAFT;
      BUN_INSTALL = "${SOV_HOME}/.bun";
      # ── CUDA ──
      CUDA_VISIBLE_DEVICES = "0";
      GGML_CUDA = "1";
      GGML_CUDA_GRAPHS = "1";
      GGML_CUDA_FA_ALL_QUANTS = "1";
      GGML_DFLASH_GPU_RING = "1";
      GGML_DFLASH_MAX_CTX = "4096";
      NIXPKGS_CONFIG = "{ cudaSupport = true; }";
      # ── Python ──
      PYTHONUNBUFFERED = "1";
      PYTHONDONTWRITEBYTECODE = "1";
      FLASK_APP = "app.py";
      FLASK_ENV = "development";
      FLASK_DEBUG = "1";
      UV_CACHE_DIR = "${SOV_HOME}/.cache/uv";
      # ── HF Hub ──
      HF_HUB_DISABLE_TELEMETRY = "1";
      HF_HUB_DISABLE_UPDATE_CHECK = "1";
      # ── Ports ──
      LLAMA_SERVER_PORT = toString PORTS.llama-server;
      OPENFANG_PORT = toString PORTS.openfang;
      NFCOT_PORT = toString PORTS.nfcot;
      RUST_WEB_PORT = toString PORTS.rust-web;
      LANDING_PAGE = toString PORTS.landing;
      HF_DOWNLOADER = toString PORTS.hf-downloader;
      LLAMA_HERDER = toString PORTS.llama-herder;
      PROMETHEUS_PORT = toString PORTS.prometheus;
      CADDY_ADMIN = "0.0.0.0:${toString PORTS.caddy-admin}";
      # ── Legacy aliases ──
      LLAMA_ARG_MODEL = ACTIVE_MODEL;
      LLAMA_ARG_CTX_SIZE = toString LLAMA_FLAGS.ctx-size;
      LLAMA_ARG_N_GPU_LAYERS = toString LLAMA_FLAGS.ngl;
      LLAMA_ARG_BATCH = toString LLAMA_FLAGS.batch;
      LLAMA_ARG_UBATCH = toString LLAMA_FLAGS.ubatch;
      LLAMA_ARG_FLASH_ATTN = "auto";
      LLAMA_ARG_THREADS = toString LLAMA_FLAGS.threads;
      LLAMA_ARG_HOST = "0.0.0.0";
      LLAMA_ARG_PORT = toString PORTS.llama-server;
      LLAMA_ARG_NO_MMAP = "1";
      LLAMA_ARG_MLOCK = "1";
      LLAMA_ARG_EMBEDDINGS = "1";
      LLAMA_ARG_POOLING = "cls";
      LLAMA_ARG_CACHE_TYPE_K = LLAMA_FLAGS.cache-type-k;
      LLAMA_ARG_CACHE_TYPE_V = LLAMA_FLAGS.cache-type-v;
      LLAMA_ARG_DRAFT = ACTIVE_DRAFT;
      LLAMA_ARG_DRAFT_N_GPU_LAYERS = toString LLAMA_FLAGS.draft-ngl;
      LLAMA_ARG_DRAFT_N_PREDICT = toString LLAMA_FLAGS.draft-n-predict;
    };
}
