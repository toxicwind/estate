import os

vars_str = "pkgs' SOV SOV_HOME MODELS STATE LOGS PROMETHEUS_DATA MODELS_MANIFEST ACTIVE_MODEL ACTIVE_DRAFT PORTS LLAMA_FLAGS beellama-src hfhub-src hfxet-wheel beellama-cpp llama-herder-pkg sovereign-watchdog-pkg telethon-overlord-pkg configToml secretspecToml prometheusYml caddyConfig llamaServerCmd"

def make_module(filename, content):
    with open(f"modules/{filename}", 'w') as f:
        f.write("{ config, pkgs, lib, inputs, ... }:\nlet\n")
        f.write("  shared = import ./lib.nix { inherit config pkgs lib inputs; };\n")
        f.write(f"  inherit (shared) {vars_str};\n")
        f.write("in\n{\n")
        f.write("  " + content.replace('\n', '\n  ').strip() + "\n")
        f.write("}\n")

# processes.nix with the hf-downloader fix
with open('scratch/modular/extracted/processes.nix', 'r') as f:
    proc_content = f.read()
proc_content = proc_content.replace('passwith socketserver', 'pass\n\nwith socketserver')
make_module('processes.nix', proc_content)

# other files
for name in ['services', 'tasks', 'scripts', 'env', 'git-hooks', 'containers', 'languages', 'packages']:
    if os.path.exists(f'scratch/modular/extracted/{name}.nix'):
        with open(f'scratch/modular/extracted/{name}.nix', 'r') as f:
            make_module(f'{name}.nix', f.read())

# enter-shell needs to combine enterShell and enterTest
enter_content = ""
for name in ['enterShell', 'enterTest']:
    if os.path.exists(f'scratch/modular/extracted/{name}.nix'):
        with open(f'scratch/modular/extracted/{name}.nix', 'r') as f:
            enter_content += f.read() + "\n"
make_module('enter-shell.nix', enter_content)

print("Modules assembled.")
