#!/usr/bin/env python3
"""Book pipeline: rate-limited IA download -> validate -> Parquet. Fully automated.

Usage: pipeline.py [config.json]   (default: config.law-of-one.json next to script)

Config schema:
  {"workdir": "wilcock",
   "books": [{"item": "<ia identifier>", "file": "<path inside item>",
              "title": "<book title>", "out": "<local pdf filename>"}, ...]}

Portable: all paths resolve from Path.home()/workspace or this file's
location; no hardcoded /home/... prefixes. Idempotent: existing valid
files are kept.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

HERE = Path(__file__).resolve().parent
SKILL_DIR = Path.home() / "workspace" / "skills" / "book-to-dataframe"

# Politeness: Internet Archive asks for gentle crawling.
RATE_LIMIT_S = 3.0        # minimum gap between download starts
REQUEST_TIMEOUT = 180
RETRIES = 4
BACKOFF_BASE_S = 5.0      # exponential backoff: base * 2**attempt
UA = "shingle-book-pipeline/1.0 (personal archiving)"

timings = {}


class Timer:
    """Timing module: records wall time per stage into `timings`."""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        dt = time.perf_counter() - self.t0
        timings[self.name] = round(dt, 2)
        print(f"  [time] {self.name}: {dt:.1f}s")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def download_one(label, item, file_path, dest):
    """Download with rate limiting + exponential-backoff retries."""
    url = f"https://archive.org/download/{item}/{quote(file_path)}"
    last_err = None
    for attempt in range(RETRIES):
        try:
            with Timer(f"download {label} (attempt {attempt + 1})"):
                r = requests.get(url, headers={"User-Agent": UA},
                                 timeout=REQUEST_TIMEOUT, stream=True)
                if r.status_code == 429:
                    wait = float(r.headers.get("Retry-After", BACKOFF_BASE_S * 2 ** attempt))
                    log(f"{label}: 429, sleeping {wait:.0f}s")
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                data = b"".join(r.iter_content(chunk_size=1 << 20))
            if not data.startswith(b"%PDF"):
                raise ValueError("bad magic: not a PDF")
            dest.write_bytes(data)
            return len(data)
        except Exception as e:  # noqa: BLE001 - retry loop
            last_err = e
            wait = BACKOFF_BASE_S * 2 ** attempt
            log(f"{label}: attempt {attempt + 1} failed ({e}); backoff {wait:.0f}s")
            time.sleep(wait)
    raise RuntimeError(f"{label}: download failed after {RETRIES} tries: {last_err}")


def validate(pdf_path):
    """Signature, size, page count, text coverage. Returns dict."""
    import hashlib
    from pypdf import PdfReader
    data = pdf_path.read_bytes()
    assert data.startswith(b"%PDF"), "not a PDF"
    reader = PdfReader(str(pdf_path))
    pages = len(reader.pages)
    sample = "".join((reader.pages[i].extract_text() or "") for i in range(min(3, pages)))
    return {
        "bytes": len(data),
        "pages": pages,
        "sample_chars": len(sample),
        "sha256": hashlib.sha256(data).hexdigest()[:16],
    }


def convert(pdf_path, title, out_path):
    if out_path.exists():
        log(f"skip convert (exists): {out_path.name}")
        return out_path
    with Timer(f"convert {pdf_path.stem}"):
        r = subprocess.run(
            [str(SKILL_DIR / "runner.sh"), "convert", str(pdf_path),
             "-o", str(out_path), "--title", title],
            capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"convert failed: {r.stderr[-2000:]}")
    return out_path


def inspect_parquet(pq_path):
    import pyarrow.parquet as pq
    with Timer(f"inspect {pq_path.stem}"):
        t = pq.read_table(pq_path, columns=["unit_index", "text", "word_count", "char_count"])
        d = t.to_pydict()
        words = sum(d["word_count"])
        chars = sum(d["char_count"])
        empty = sum(1 for x in d["text"] if not x.strip())
    return {"rows": t.num_rows, "words": words, "chars": chars,
            "empty_units": empty, "bytes": pq_path.stat().st_size}


def main():
    cfg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "config.law-of-one.json"
    cfg = json.loads(cfg_path.read_text())
    workdir = Path.home() / "workspace" / cfg["workdir"]
    src_dir = workdir / "source"
    out_dir = workdir / "parquet"
    src_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.perf_counter()
    report = {"config": str(cfg_path.name), "books": {}, "timings": timings}

    for b in cfg["books"]:
        label, item, file_path = b["out"], b["item"], b["file"]
        dest = src_dir / b["out"]
        log(f"--- {label} ---")
        entry = {"item": item, "title": b["title"]}

        # 1. download (rate-limited)
        if dest.exists() and dest.stat().st_size > 0 and dest.read_bytes()[:4] == b"%PDF":
            log(f"keep existing {dest.name} ({dest.stat().st_size}b)")
            entry["downloaded"] = False
        else:
            with Timer("rate-limit gap"):
                time.sleep(RATE_LIMIT_S)
            nbytes = download_one(label, item, file_path, dest)
            log(f"downloaded {dest.name}: {nbytes}b")
            entry["downloaded"] = True

        # 2. validate
        with Timer(f"validate {label}"):
            entry["validation"] = validate(dest)
        log(f"valid: {entry['validation']['pages']} pages, "
            f"sample {entry['validation']['sample_chars']} chars")

        # 3. convert
        pq_path = out_dir / (dest.stem + ".parquet")
        convert(dest, b["title"], pq_path)
        entry["parquet"] = str(pq_path)

        # 4. inspect
        entry["stats"] = inspect_parquet(pq_path)
        log(f"parquet: {entry['stats']['rows']} rows, "
            f"{entry['stats']['words']:,} words, {entry['stats']['bytes']}b")

        report["books"][label] = entry

    report["total_s"] = round(time.perf_counter() - t_start, 1)
    rep_path = workdir / "report.json"
    rep_path.write_text(json.dumps(report, indent=2))
    print("\n==== TIMING SUMMARY ====")
    for k, v in timings.items():
        print(f"  {v:>8.1f}s  {k}")
    print(f"  {report['total_s']:>8.1f}s  TOTAL")
    print(f"report -> {rep_path}")


if __name__ == "__main__":
    sys.exit(main())
