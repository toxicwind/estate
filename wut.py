import difflib, json, os, re

left_dir = "/home/toxic/sovereign/modules/nix_bak"
right_dir = "/home/toxic/sovereign/modules/nix_wtf"

def parse_unified_diff(diff_text):
    hunks = []
    current_hunk = None

    hunk_header_re = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')

    for line in diff_text.splitlines():
        m = hunk_header_re.match(line)
        if m:
            if current_hunk:
                hunks.append(current_hunk)

            current_hunk = {
                "old_start": int(m.group(1)),
                "old_count": int(m.group(2) or 1),
                "new_start": int(m.group(3)),
                "new_count": int(m.group(4) or 1),
                "lines": []
            }
            continue

        if current_hunk is None:
            continue

        if line.startswith('+'):
            current_hunk["lines"].append({"type": "added", "text": line[1:]})
        elif line.startswith('-'):
            current_hunk["lines"].append({"type": "removed", "text": line[1:]})
        else:
            current_hunk["lines"].append({"type": "context", "text": line[1:] if line.startswith(' ') else line})

    if current_hunk:
        hunks.append(current_hunk)

    return hunks


result = []

# Collect file sets
left_files = set()
right_files = set()

for root, _, files in os.walk(left_dir):
    for f in files:
        left_files.add(os.path.relpath(os.path.join(root, f), left_dir))

for root, _, files in os.walk(right_dir):
    for f in files:
        right_files.add(os.path.relpath(os.path.join(root, f), right_dir))

all_files = sorted(left_files | right_files)

for rel_path in all_files:
    left_path = os.path.join(left_dir, rel_path)
    right_path = os.path.join(right_dir, rel_path)

    entry = {"file": rel_path}

    # Added file
    if rel_path in left_files and rel_path not in right_files:
        with open(left_path) as lf:
            left_lines = lf.readlines()
        diff_text = ''.join(difflib.unified_diff([], left_lines,
                                                 fromfile="/dev/null",
                                                 tofile=left_path))
        entry["status"] = "added"
        entry["hunks"] = parse_unified_diff(diff_text)
        result.append(entry)
        continue

    # Deleted file
    if rel_path in right_files and rel_path not in left_files:
        with open(right_path) as rf:
            right_lines = rf.readlines()
        diff_text = ''.join(difflib.unified_diff(right_lines, [],
                                                 fromfile=right_path,
                                                 tofile="/dev/null"))
        entry["status"] = "deleted"
        entry["hunks"] = parse_unified_diff(diff_text)
        result.append(entry)
        continue

    # Modified file
    with open(left_path) as lf, open(right_path) as rf:
        left_lines = lf.readlines()
        right_lines = rf.readlines()

    diff_text = ''.join(difflib.unified_diff(left_lines, right_lines,
                                             fromfile=left_path,
                                             tofile=right_path))

    hunks = parse_unified_diff(diff_text)

    entry["status"] = "modified" if hunks else "same"
    entry["hunks"] = hunks

    result.append(entry)

print(json.dumps(result, indent=2))
