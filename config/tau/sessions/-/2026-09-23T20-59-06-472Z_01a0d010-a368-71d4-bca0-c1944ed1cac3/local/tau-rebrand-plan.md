# Tau Rebranding Plan

## Context
The repository is a fork of an upstream project (oh-my-pi) but still carries upstream identity in the compiled binary, help output, banners, error messages, and internal package references. The goal is to rebrand the fork to present "toxicwind" identity in all user-visible strings and ensure internal dependencies no longer reference upstream names where they live inside the repo.

## Approach
1. Identify all user-visible strings that contain upstream identity (e.g., "oh-my-pi", "omp", "pi-") in source code, templates, and configuration files.
2. Replace these strings with appropriate toxicwind/tau equivalents, preserving functionality.
3. Update internal package references (imports, package.json names) for any packages that live inside the monorepo and carry upstream identity.
4. Ensure the compiled binary reports the correct version and name via --version and --help.
5. Remove any symlinks that could preserve backward compatibility.
6. Verify changes by building the binary and checking its output.

## Critical files & anchors
- /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/package.json — defines binary name and version
- /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/src/cli.ts — contains APP_NAME, VERSION imports, and help/version logic
- /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/src/cli/help-extra.ts — likely contains help text
- /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/scripts/build-binary.ts — determines binary output name
- /home/toxic/sovereign/projects/tau/.tau/agent/config.yml — may contain model roles or other references

## Verification
- Build the binary: `cd /home/toxic/sovereign/projects/tau && ./launcher/tau vendor build`
- Check binary name and version: `/home/toxic/sovereign/projects/tau/engine/packages/coding-agent/dist/tau --version` should output something like `tau/<version>-toxicwind` or similar showing toxicwind identity.
- Check help output: same binary `--help` should not contain "oh-my-pi" or "omp" as the tool name; should show "tau".
- Scan source for remaining upstream identity: `rg -i "oh-my-pi|omp" /home/toxic/sovereign/projects/tau/engine/packages --glob '!node_modules/*' --glob '!*.git/*'` should return only harmless matches (e.g., in documentation or comments) or none.
- Ensure no symlinks exist in the dist directory: `find /home/toxic/sovereign/projects/tau/engine/packages/coding-agent/dist -type l` should return empty.

## Assumptions & contingencies
- If the version string is not easily changed without breaking the build, we can embed a custom version via a build-time environment variable or by modifying the VERSION import in pi-utils/dirs.ts (if we create a fork of pi-utils).
- If internal package references are numerous, we may need to create a local pi-utils fork within the monorepo and update imports accordingly.
- If the binary name must remain "omp" for compatibility, we will instead ensure the tool reports "tau" in help and version, and update the launcher to invoke the binary as tau (already done).