import type { ExtensionAPI } from "tau/extensibility/extensions/types";

// Unified Nemotron extension for tau
// Combines: 9 NVIDIA Nemotron skills + nvidia-nim router + model implementations
//
// Skills (in ./nemotron/skills/):
//   - nemotron-customize: training, fine-tuning, RL alignment pipelines
//   - nemotron-add-model, nemotron-add-pattern, nemotron-add-step: builders
//   - nemotron-nano3, nemotron-super3, nemotron-ultra: model-specific
//   - nemotron-policy-generator, nemotron-retrieval-recipes: specialized
//
// Router (in ./nemotron/router/):
//   - nvidia-router.ts: smart routing across NIM models
//   - rate-limit-retry.ts: aggressive retry handling
//
// Models (in ./nemotron/models/):
//   - nemotron.cpp, nemotron-h.cpp, nemotron-h-moe.cpp: C++ implementations

export default async function (pi: ExtensionAPI): Promise<void> {
  // Load the NVIDIA NIM router for live model routing
  const { default: nvidiaRouter } = await import("./nemotron/router/nvidia-router.ts");
  await nvidiaRouter(pi);
}
