"""Bidder personality profiles (market/v1).

Each profile = capability set + keyword vocabulary + bidding temperament.
Distinct profiles make auctions genuinely competitive.
"""

PROFILES = {
    "flash": {
        "desc": "fast-but-shallow: quick shell/text tasks, low cost, bids fast",
        "caps": ["shell", "text"],
        "keywords": ["shell", "bash", "text", "file", "list", "echo",
                     "quick", "simple", "headline", "summarize"],
        "max_eta_s": 60.0,
        "cost_factor": 0.5,
        "conf_bias": 0.10,
        "complexity_aversion": 1.0,
        "skip_on_unknown": False,
    },
    "mule": {
        "desc": "slow-but-thorough: python/shell, high cost, confident on complex work",
        "caps": ["shell", "python", "text"],
        "keywords": ["shell", "bash", "python", "script", "compute",
                     "process", "analyze", "complex", "thorough"],
        "max_eta_s": 600.0,
        "cost_factor": 2.0,
        "conf_bias": 0.0,
        "complexity_aversion": 0.2,
        "skip_on_unknown": False,
    },
    "specialist": {
        "desc": "specialist: bids ONLY on python/data tasks, very confident when matched",
        "caps": ["python", "data"],
        "keywords": ["python", "data", "compute", "sum", "csv", "json",
                     "pandas", "number", "statistics"],
        "max_eta_s": 600.0,
        "cost_factor": 1.2,
        "conf_bias": 0.15,
        "complexity_aversion": 0.1,
        "skip_on_unknown": True,
    },
}


def get(name):
    if name not in PROFILES:
        raise KeyError("unknown bidder profile %r (have: %s)"
                       % (name, sorted(PROFILES)))
    p = dict(PROFILES[name])
    p["name"] = name
    return p
