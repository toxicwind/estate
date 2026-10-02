#!/usr/bin/env python3
"""
Dynamic Runtime Subgraph Inducer
Extracts runtime execution stacks from pytest tracebacks and induces a 1-hop & 2-hop
dependency subgraph combining static AST and dynamic failure sites.
Reference: Code Graph Model (arXiv:2505.16901) & RepoGraph (arXiv:2510.04905)
"""
import re
import os
import ast
import json
import sys
from typing import List, Dict, Any

class DynamicSubgraphInducer:
    def __init__(self, root_dir="/workspace"):
        self.root_dir = root_dir

    def extract_traceback_frames(self, pytest_output: str) -> List[Dict[str, Any]]:
        frames = []
        pattern = re.compile(r'File "([^"]+)", line (\d+), in (\w+)')
        for match in pattern.finditer(pytest_output):
            fpath, lno, symbol = match.groups()
            if not fpath.startswith("/"):
                fpath = os.path.join(self.root_dir, fpath)
            frames.append({
                "file": fpath,
                "line": int(lno),
                "symbol": symbol
            })
        return frames

    def induce_subgraph(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        subgraph = {
            "failure_nodes": frames,
            "one_hop_callees": [],
            "enclosing_classes": []
        }
        for frame in frames:
            fpath = frame["file"]
            if not os.path.exists(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    tree = ast.parse(f.read(), filename=fpath)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name == frame["symbol"] or (node.lineno <= frame["line"] <= getattr(node, "end_lineno", node.lineno)):
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call):
                                    if isinstance(child.func, ast.Name):
                                        subgraph["one_hop_callees"].append(child.func.id)
                                    elif isinstance(child.func, ast.Attribute):
                                        subgraph["one_hop_callees"].append(child.func.attr)
            except Exception:
                continue
        subgraph["one_hop_callees"] = list(set(subgraph["one_hop_callees"]))
        return subgraph

if __name__ == "__main__":
    inducer = DynamicSubgraphInducer("/workspace")
    sample_trace = """
    File "fastapi/routing.py", line 125, in serialize_response
        res = await solve_dependencies(request)
    File "fastapi/dependencies/utils.py", line 42, in solve_dependencies
        raise ValueError("Invalid dependency structure")
    """
    frames = inducer.extract_traceback_frames(sample_trace)
    sub = inducer.induce_subgraph(frames)
    print(f"[subgraph_inducer] Extracted {len(frames)} failure nodes. Callees: {sub['one_hop_callees']}")
