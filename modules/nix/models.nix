{ config, ... }:
let
  paths = import ./paths.nix { inherit config; };

  manifest = {
    primary = "${paths._module.args.MODELS}/StrangeMerges_19-7B-dare_ties.Q4_K_M.gguf";
    draft = "${paths._module.args.MODELS}/Qwen2.5-1.5B-Draft.gguf";
    flash = "${paths._module.args.MODELS}/Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf";
    heretic = "${paths._module.args.MODELS}/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf";
    gemma = "${paths._module.args.MODELS}/gemma-4-12B-it-uncensored-Q4_K_M.gguf";
    grand = "${paths._module.args.MODELS}/MN-GRAND-23.5B-Gutenberg-UNCENSORED-V2-Q4_K_M.gguf";
  };
in
{
  _module.args = {
    MODELS_MANIFEST = manifest;
    ACTIVE_MODEL = manifest.primary;
    ACTIVE_DRAFT = manifest.draft;
  };
}
