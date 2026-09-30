import json, sys
with open(sys.argv[1]) as f:
    for line in f:
        line = line.strip()
        if not line or "49c6da84477a4060" not in line:
            continue
        d = json.loads(line)
        for k in ("question", "verdict", "confidence", "summary", "rationale", "decision"):
            if k in d:
                print(k.upper(), ":", str(d[k])[:800])
        print("---")
