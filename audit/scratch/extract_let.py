with open('devenv.nix', 'r') as f:
    lines = f.readlines()

let_lines = []
in_let = False
for i, line in enumerate(lines):
    if line.startswith('let'):
        in_let = True
        continue
    if in_let and line.startswith('in'):
        break
    if in_let:
        let_lines.append(line)

with open('scratch/modular/extracted/let_block.nix', 'w') as f:
    f.writelines(let_lines)

