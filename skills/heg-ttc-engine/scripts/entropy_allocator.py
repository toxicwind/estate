#!/usr/bin/env python3
"""
Entropy-Based Compute Allocator
Measures lexical/syntactic ambiguity in problem statements and sets dynamic compute tiers.
Reference: Scaling Test-Time Compute for Agentic Coding (arXiv:2604.16529)
"""
import sys
import re
import json

def calculate_entropy_tier(issue_text: str) -> dict:
    tokens = re.findall(r'\b\w+\b', issue_text.lower())
    total_tokens = len(tokens)
    unique_tokens = len(set(tokens))
    lexical_diversity = unique_tokens / total_tokens if total_tokens > 0 else 0.0
    
    # Complexity indicators
    has_traceback = bool(re.search(r'traceback|file ".*?", line \d+', issue_text, re.IGNORECASE))
    has_async = bool(re.search(r'\basync\b|\bawait\b|coroutine', issue_text, re.IGNORECASE))
    has_multi_file = len(re.findall(r'[\w/]+\.py\b', issue_text)) > 1
    
    score = 0
    if has_traceback: score += 1
    if has_async: score += 2
    if has_multi_file: score += 2
    if total_tokens > 150: score += 1
    
    if score <= 1:
        tier = "FAST_PATH"
        budget_sec = 60
        max_turns = 6
    else:
        tier = "DEEP_SEARCH"
        budget_sec = 240
        max_turns = 18
        
    return {
        "tier": tier,
        "complexity_score": score,
        "budget_seconds": budget_sec,
        "max_turns": max_turns,
        "has_async": has_async,
        "has_traceback": has_traceback
    }

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Fix KeyError in serializer when handling async request"
    res = calculate_entropy_tier(text)
    print(json.dumps(res, indent=2))
