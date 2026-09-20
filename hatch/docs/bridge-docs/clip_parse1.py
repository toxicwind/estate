"""Parse the 2 unique HAR clipboard files into DataFrames, save CSVs."""
import json, os, re, hashlib
import pandas as pd
import numpy as np
from urllib.parse import urlparse, parse_qsl
from datetime import datetime

OUT = "/home/toxic/analysis-clipboard-20260914"
os.makedirs(OUT, exist_ok=True)

FILES = {
    "A": "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "B": "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve(1).txt",
}
DUPES = {
    "A": "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "B": "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve(1).txt",
}

stats = {}
all_rows = []
for tag, f in FILES.items():
    with open(f, encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)
    log = data["log"]
    entries = log.get("entries", [])
    stats[tag] = {"entries": len(entries), "creator": log.get("creator", {}).get("name")}
    for i, e in enumerate(entries):
        req = e.get("request", {})
        resp = e.get("response", {})
        url = req.get("url", "")
        pu = urlparse(url)
        content = resp.get("content", {}) or {}
        text = content.get("text") or ""
        rows = {
            "file_tag": tag,
            "entry_idx": i,
            "started": e.get("startedDateTime"),
            "method": req.get("method"),
            "url": url,
            "host": pu.hostname,
            "path": pu.path,
            "query": pu.query,
            "status": resp.get("status"),
            "mime": content.get("mimeType"),
            "body_len": len(text),
            "body_bytes_reported": content.get("size"),
            "time_ms": e.get("time"),
            "timings": json.dumps(e.get("timings", {})),
            "req_body_len": len(json.dumps(req.get("postData", {}) or {})),
            "service": (pu.path.split("/apiv2/")[-1] if "/apiv2/" in pu.path else ""),
        }
        all_rows.append(rows)
    # keep one sample body per file for text mining
    with open(os.path.join(OUT, "sample_bodies_%s.txt" % tag), "w", encoding="utf-8") as sf:
        n = 0
        for e in entries:
            t = (e.get("response", {}).get("content", {}) or {}).get("text") or ""
            if t and n < 30:
                sf.write(t[:1500] + "\n====ENTRY====\n")
                n += 1

df = pd.DataFrame(all_rows)
df.to_csv(os.path.join(OUT, "har_entries_all.csv"), index=False)
print("rows:", len(df), "cols:", len(df.columns))
print("parse stats:", json.dumps(stats))
print("hosts:", df["host"].value_counts().to_dict())
print("status dist:", df["status"].value_counts().to_dict())
print("top paths:")
print(df["path"].value_counts().head(15).to_string())
print("body_len>0 rows:", int((df["body_len"] > 0).sum()))
print("time range:", df["started"].min(), "->", df["started"].max())
