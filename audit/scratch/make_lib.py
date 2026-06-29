import re

with open('scratch/modular/extracted/let_block.nix', 'r') as f:
    let_block = f.read()

vars = []
for line in let_block.split('\n'):
    match = re.match(r'^  ([a-zA-Z0-9_\-\']+)\s*=', line)
    if match:
        vars.append(match.group(1))

# write modules/lib.nix
with open('modules/lib.nix', 'w') as f:
    f.write("{ config, pkgs, lib, inputs, ... }:\nlet\n")
    f.write(let_block)
    f.write("\nin\n{\n  inherit " + " ".join(vars) + ";\n}\n")

print("Created lib.nix with vars:", vars)
