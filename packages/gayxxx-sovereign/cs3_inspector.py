#!/usr/bin/env python3
"""
Sovereign .cs3 / DEX Inspector for CloudStream Extensions
Read-only forensic inspection. Stdlib only.
"""
import sys
import re
import string
from pathlib import Path
from collections import Counter

PRINTABLE = set(string.printable.encode('ascii'))

def is_printable(b: int) -> bool:
    return b in PRINTABLE

def extract_strings(data: bytes, min_len: int = 5) -> list[str]:
    strings = []
    current = []
    for byte in data:
        if is_printable(byte):
            current.append(chr(byte))
        else:
            if len(current) >= min_len:
                strings.append(''.join(current))
            current = []
    if len(current) >= min_len:
        strings.append(''.join(current))
    return strings

def categorize_strings(strings: list[str]) -> dict:
    cats = {'urls': [], 'domains': [], 'paths': [], 'user_agents': [], 'potential_endpoints': [], 'other_interesting': []}
    url_re = re.compile(r'https?://[^\s"\'<>]+', re.IGNORECASE)
    domain_re = re.compile(r'\b([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b')
    path_re = re.compile(r'/(api|v[0-9]|video|stream|embed|player|source|extract)[^\s"\'<>]*', re.IGNORECASE)
    ua_re = re.compile(r'(User-Agent|Mozilla|OkHttp|Dalvik|Android)', re.IGNORECASE)
    for s in strings:
        if url_re.search(s):
            cats['urls'].append(s)
        elif ua_re.search(s):
            cats['user_agents'].append(s)
        elif path_re.search(s):
            cats['paths'].append(s)
        elif domain_re.search(s) and len(s) > 8:
            if not any(x in s.lower() for x in ['example', 'test', 'localhost']):
                cats['domains'].append(s)
        elif any(kw in s.lower() for kw in ['api', 'endpoint', 'baseurl', 'host']):
            cats['potential_endpoints'].append(s)
        elif len(s) > 20:
            cats['other_interesting'].append(s[:250])
    for k in cats:
        seen = set()
        cats[k] = [x for x in cats[k] if not (x in seen or seen.add(x))]
    return cats

def inspect_cs3(file_path: Path):
    print(f"=== Sovereign .cs3 Inspector ===")
    print(f"File: {file_path}")
    if not file_path.exists():
        print("ERROR: File not found"); return
    data = file_path.read_bytes()
    size = len(data)
    print(f"Size: {size:,} bytes")
    if data[:3] == b'dex':
        print("Magic: 'dex' header → Standard Android DEX (renamed .cs3)")
    elif data[:4] == b'PK\x03\x04':
        print("Magic: ZIP header")
    else:
        print(f"Magic: {data[:8].hex()}")
    strings = extract_strings(data)
    print(f"Printable strings: {len(strings)}")
    cats = categorize_strings(strings)
    for cat, items in cats.items():
        if items:
            print(f"\n[{cat.upper()}] ({len(items)})")
            for item in items[:12]:
                print(f"  - {item[:280]}")
            if len(items) > 12:
                print(f"  ... +{len(items)-12} more")
    print("\n=== Done. Review domains/URLs above ===")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cs3_inspector.py file.cs3"); sys.exit(1)
    inspect_cs3(Path(sys.argv[1]).expanduser().resolve())
