---
name: model-switch
description: >
  Switches the active inference model on the beellama server.
  Triggers on: "switch model", "load model", "use [model name]",
  "swap to", "change model". Knows about all GGUFs in ~/models/.
---

# Model Switch Skill

## Available models

Scan /home/toxic/sovereign/models/ and ~/models/ for .gguf files.

## Procedure

1. List available GGUFs
2. Match user request to closest filename
3. Restart llama-server with new -m path (via systemd or pitchfork)
4. Confirm new model is loaded via /health endpoint

## Constraints

- Preserve --ctx, -ngl 99, TurboQuant flags
- Draft model stays unless user explicitly requests change
