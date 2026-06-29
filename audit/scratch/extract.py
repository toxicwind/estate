import re
import os
import sys

with open('devenv.nix', 'r') as f:
    text = f.read()

def extract_block(name, start_keyword):
    # Find the keyword
    pattern = r"^\s*" + start_keyword + r"\s*=\s*([\[\{]|'')"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return None
    
    start_idx = match.start()
    char_match = match.group(1)
    
    # We need to find the matching closing bracket
    idx = match.end() - len(char_match)
    if char_match == "''":
        # Multi-line string
        end_idx = text.find("''", idx + 2)
        if end_idx != -1:
            return text[start_idx:end_idx + 2]
    else:
        # Bracket matching
        open_char = char_match
        close_char = '}' if open_char == '{' else ']'
        count = 0
        in_string = False
        in_ml_string = False
        in_comment = False
        
        i = idx
        while i < len(text):
            if in_comment:
                if text[i] == '\n':
                    in_comment = False
                i += 1
                continue
                
            if in_ml_string:
                if text[i:i+2] == "''":
                    in_ml_string = False
                    i += 2
                    continue
                i += 1
                continue
                
            if in_string:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == '"':
                    in_string = False
                i += 1
                continue
                
            if text[i:i+2] == "''":
                in_ml_string = True
                i += 2
                continue
                
            if text[i] == '"':
                in_string = True
                i += 1
                continue
                
            if text[i] == '#':
                in_comment = True
                i += 1
                continue
                
            if text[i] == open_char:
                count += 1
            elif text[i] == close_char:
                count -= 1
                if count == 0:
                    # found the end
                    # return the whole block
                    # find the trailing semicolon if any
                    end_pos = i + 1
                    while end_pos < len(text) and text[end_pos] in ' \t\n':
                        end_pos += 1
                    if end_pos < len(text) and text[end_pos] == ';':
                        end_pos += 1
                    return text[start_idx:end_pos]
            i += 1
    return None

blocks = {}
for b in ["processes", "services", "tasks", "scripts", "enterShell", "enterTest", "languages", "packages", "env", "git-hooks", "containers"]:
    blocks[b] = extract_block(b, b)

os.makedirs('scratch/modular/extracted', exist_ok=True)
for k, v in blocks.items():
    if v:
        with open(f'scratch/modular/extracted/{k}.nix', 'w') as f:
            f.write(v)

print("Extracted:", list(blocks.keys()))

import re
with open('devenv.nix', 'r') as f:
    text = f.read()

pattern = r"^\s*packages\s*=\s*(.*?);"
match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
if match:
    with open('scratch/modular/extracted/packages.nix', 'w') as f:
        f.write("{\n  packages = " + match.group(1).strip() + ";\n}")
