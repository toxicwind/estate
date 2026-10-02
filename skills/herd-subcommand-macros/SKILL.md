---
name: herd-subcommand-macros
description: >
  herd.yaml macro generation. Reads llama-server --help from every llama.cpp fork on the box and writes one ARG_<FLAG> macro per flag into herd.yaml, touching nothing outside its own generated block. Triggers on: "herd macros", "subcommand macros", "llama-server flags", "herd.yaml".
---

# Herd Subcommand Macro Generation

This skill automates the process of extracting flags/subcommands from llama-server binaries (beellama vs turboquant) and updating herd.yaml with corresponding ARG_<FLAG> macros.

## When to Use
- After rebuilding llama-server binaries
- When adding new subcommands or flags to llama-server
- To ensure herd.yaml stays synchronized with available llama-server options

## Procedure

1. **Ensure the script is present and executable**:
   ```bash
   ls -l /home/toxic/estate/projects/range/ranch/stockyard/herd/scripts/generate-subcommand-macros.py
   ```

2. **Run the macro generator**:
   ```bash
   python3 /home/toxic/estate/projects/range/ranch/stockyard/herd/scripts/generate-subcommand-macros.py \
     --binary /home/toxic/estate/engines/herd/beellama.cpp/build-cuda86/bin/llama-server \
     --config /home/toxic/estate/config/herd.yaml
   ```

3. **Verify the update**:
   ```bash
   # Check that AUTO_SUBCOMMAND_MACROS block exists
   grep -n "AUTO_SUBCOMMAND_MACROS" /home/toxic/estate/config/herd.yaml

   # Count generated macros
   grep -A 1000 "AUTO_SUBCOMMAND_MACROS:" /home/toxic/estate/config/herd.yaml | grep -E "^  ARG_" | wc -l

   # Verify herd runtime
   curl -s http://127.0.0.1:25100/v1/models | jq '.data | length'
   ```

## Script Location
`/home/toxic/estate/projects/range/ranch/stockyard/herd/scripts/generate-subcommand-macros.py`

## Configuration Updated
`/home/toxic/estate/config/herd.yaml` - adds/updates `AUTO_SUBCOMMAND_MACROS` mapping

## Notes
- The script extracts all flags matching `--?[a-zA-Z0-9_-]+` pattern from `llama-server --help`
- Converts each flag to `ARG_<FLAG_NAME>` macro (e.g., `--model` → `ARG_MODEL: --model`)
- Skips empty flag names to prevent invalid macro keys
- Preserves existing macros and aliases in herd.yaml
- Can be customized with different binary/config paths via command line arguments
