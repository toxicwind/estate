import json
targets = {"fleet": 12992, "bid-market": 100328}
for ch, since in targets.items():
    print("===", ch, "since", since)
    p = f"/home/toxic/.shingle/squawk-root/{ch}/log.jsonl"
    with open(p) as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: m = json.loads(line)
            except Exception: continue
            seq = m.get("seq", 0)
            if seq and seq > since:
                print(seq, m.get("agent"), m.get("title"), "|", str(m.get("body", ""))[:300].replace("\n", " "))
    print()
