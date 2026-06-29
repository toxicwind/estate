import re

with open('devenv.nix', 'r') as f:
    content = f.read()

def extract_keys(block_name):
    match = re.search(r'^\s*'+block_name+r'\s*=\s*{(.*?)}^\s*(?:env|services|processes|tasks|scripts|enterShell|languages|packages|git-hooks|containers)', content, re.MULTILINE | re.DOTALL)
    if not match:
        match = re.search(r'^\s*'+block_name+r'\s*=\s*{(.*)', content, re.MULTILINE | re.DOTALL)
    if match:
        # crude extraction of keys at level 1 inside block
        sub = match.group(1)
        keys = re.findall(r'^\s{4}([a-zA-Z0-9_-]+)\s*=', sub, re.MULTILINE)
        return keys
    return []

print("Processes:", extract_keys("processes"))
print("Services:", extract_keys("services"))
print("Scripts:", extract_keys("scripts"))
print("Tasks:", extract_keys("tasks"))

