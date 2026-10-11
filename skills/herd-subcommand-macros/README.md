# herd-subcommand-macros

[![for-the-badge](https://img.shields.io/badge/llama-server-Parser-FF6F61?style=for-the-badge)](https://github.com/ggml-org/llama.cpp) [![for-the-badge](https://img.shields.io/badge/herd.yaml-Macros-88D4FD?style=for-the-badge)](https://github.com/toxic/config) [![for-the-badge](https://img.shields.io/python-3.9-3776AB?style=for-the-badge)](https://python.org)

## herd-subcommand-macros

Automates the process of extracting flags/subcommands from llama-server binaries (beellama vs turboquant) and updating herd.yaml with corresponding ARG_<FLAG> macros.

### When to Use

- After rebuilding llama-server binaries
- When adding new subcommands or flags to llama-server
- To ensure herd.yaml stays synchronized with available llama-server options

### Procedure

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

### Script Location

`/home/toxic/estate/projects/range/ranch/stockyard/herd/scripts/generate-subcommand-macros.py`

### Configuration Updated

`/home/toxic/estate/config/herd.yaml` - adds/updates `AUTO_SUBCOMMAND_MACROS` mapping

### Notes

- The script extracts all flags matching `--?[a-zA-Z0-9_-]+` pattern from `llama-server --help`
- Converts each flag to `ARG_<FLAG_NAME>` macro (e.g., `--model` → `ARG_MODEL: --model`)
- Skips empty flag names to prevent invalid macro keys
- Preserves existing macros and aliases in herd.yaml
- Can be customized with different binary/config paths via command line arguments

### Quick start (3 commands max)

```bash
# Generate subcommand macros from llama-server
python3 /home/toxic/estate/projects/range/ranch/stockyard/herd/scripts/generate-subcommand-macros.py \
  --binary /home/toxic/estate/engines/herd/beellama.cpp/build-cuda86/bin/llama-server \
  --config /home/toxic/estate/config/herd.yaml

# Verify the macros were generated
grep -n "AUTO_SUBCOMMAND_MACROS" /home/toxic/estate/config/herd.yaml

# Count the generated macros
grep -A 1000 "AUTO_SUBCOMMAND_MACROS:" /home/toxic/estate/config/herd.yaml | grep -E "^  ARG_" | wc -l
```

### Architecture

The script parses `llama-server --help` output, extracting all `--flag` patterns, and generates corresponding `ARG_<FLAG>` entries in herd.yaml. Each flag name is validated to be non-empty before macro creation. Existing macros are preserved and not overwritten unless they match newly extracted flags.

### Config / optional services

- `--binary <path>` — path to llama-server binary (default: `/home/toxic/estate/engines/herd/beellama.cpp/build-cuda86/bin/llama-server`)
- `--config <path>` — path to herd.yaml config (default: `/home/toxic/estate/config/herd.yaml`)
- Flag pattern: `--?[a-zA-Z0-9_-]+` from `llama-server --help`
- Macro format: `ARG_<FLAG_NAME>` (e.g., `--model` → `ARG_MODEL: --model`)

### Dev / contributing

- Ensure the llama-server binary is built before running the script
- Test with both beellama and turboquant binaries after rebuilding
- Verify that existing herd.yaml macros are preserved when running the script
- Can customize binary/config paths via command line arguments
- Add new flag patterns to the regex if llama-server adds new flag conventions

### License

Open Claw — see `skill.toml` for details.

### Security

- Preserves existing macros and aliases in herd.yaml — no unintended overwrites
- Can be customized with different binary/config paths via command line arguments
- Script location is fixed; do not move without updating all references