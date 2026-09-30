#!/usr/bin/env python3
"""Inspect herd.yaml models/routing section structure (read-only)."""
import re

lines = open("/tmp/lg-wt/config/herd.yaml", encoding="utf-8").read().split("\n")
for i, l in enumerate(lines):
    if l == "models:":
        print("models: at line", i + 1)
        for j in range(i + 1, min(i + 25, len(lines))):
            print("   ", repr(lines[j][:80]))
        break
for i, l in enumerate(lines):
    if l == "routing:":
        print("routing: at line", i + 1)
        for j in range(i + 1, min(i + 15, len(lines))):
            print("   ", repr(lines[j][:80]))
        break
