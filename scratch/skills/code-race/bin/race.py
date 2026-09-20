#!/usr/bin/env python3
"""code-race: find similar/related code on GitHub by racing identifier-built queries.

HFT-like: strategies run concurrently, each with a fail-fast timeout; latency is
measured per strategy and reported first-class; the winning strategy is recorded
so the fast path stays hot next time. No sequential retry loops — if one
strategy is blocked, the others are already in flight.

Borrowed from emergent-enrich's GitHub leg (surrogate auth, best-match relevance,
never star-sorted) and annas-router's race-mirrors pattern.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body

USER_AGENT = "toxicwind-code-race/1.0"
GITHUB_HOSTS = ("api.github.com",)
WINNERS_LOG = os.path.expanduser("~/.cache/shingle/code_race_winners.jsonl")
LANG_EXT = {"python": "py", "typescript": "ts", "javascript": "js",
            "go": "go", "rust": "rs", "java": "java", "ruby": "rb"}


def gh_code_search(query, per_page, timeout):
    params = urllib.parse.urlencode({"q": query, "per_page": per_page})
    url = "https://api.github.com/search/code?%s" % params
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    add_surrogate_to_request(req, "custom.github", allowed_hosts=GITHUB_HOSTS)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(read_response_body(resp).decode("utf-8"))
        dt = time.monotonic() - t0
        items = []
        for it in data.get("items", []):
            repo = it.get("repository") or {}
            items.append({"name": it.get("name"), "path": it.get("path"),
                          "repo": repo.get("full_name"),
                          "html_url": it.get("html_url"), "score": it.get("score")})
        return {"ok": True, "latency_s": round(dt, 3),
                "total_count": data.get("total_count"), "items": items}
    except Exception as e:  # fail-fast: a dead strategy never blocks the race
        return {"ok": False, "latency_s": round(time.monotonic() - t0, 3),
                "error": "%s: %s" % (type(e).__name__, e)}


def build_strategies(args):
    """Complex find patterns from identifiers. Each is a race contestant."""
    ids = args.ident or []
    out = []
    for ident in ids:  # S1: exact identifier — strongest single signal
        out.append(("exact:%s" % ident, '"%s"' % ident))
    if args.lang:  # S2: identifier + language narrows the field
        for ident in ids[:3]:
            out.append(("lang:%s" % ident, '"%s" language:%s' % (ident, args.lang)))
    if len(ids) >= 2:  # S3: co-occurrence — same identifiers together ≈ same shape
        out.append(("cooccur", '"%s" "%s"' % (ids[0], ids[1])))
    if args.repo:  # S4: repo-scoped — how the reference repo itself uses them
        for ident in ids[:2]:
            out.append(("inscope:%s" % ident, 'repo:%s "%s"' % (args.repo, ident)))
    if args.lang:  # S5: path-qualified — identifier in matching file types
        ext = LANG_EXT.get(args.lang.lower())
        if ext:
            for ident in ids[:2]:
                out.append(("path:%s" % ident, 'path:*.%s "%s"' % (ext, ident)))
    if args.keyword:  # S6: distinctive raw keywords — broader net, unquoted
        out.append(("keyword", " ".join(args.keyword)))
    return out


def main():
    ap = argparse.ArgumentParser(description="Race GitHub code search for similar code.")
    ap.add_argument("--ident", action="append", default=[],
                    help="Class/function/variable name. Repeatable. (the core signal)")
    ap.add_argument("--lang", default=None, help="Language filter, e.g. python")
    ap.add_argument("--repo", default=None, help="Reference repo owner/name for scoping")
    ap.add_argument("--keyword", action="append", default=[], help="Extra raw keyword")
    ap.add_argument("--per-page", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=15, help="Per-strategy fail-fast seconds")
    ap.add_argument("--workers", type=int, default=4, help="Max concurrent strategies")
    args = ap.parse_args()
    if not args.ident and not args.keyword:
        ap.error("give at least one --ident or --keyword")

    strategies = build_strategies(args)
    results = {}
    first_hit_emitted = False
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(gh_code_search, q, args.per_page, args.timeout): name
                for name, q in strategies}
        for fut in as_completed(futs):
            name = futs[fut]
            results[name] = fut.result()
            # HFT: stream the first valid hit immediately on stderr instead of
            # making the consumer wait for the slowest strategy. The final
            # merged document still goes to stdout unchanged.
            if (not first_hit_emitted and results[name].get("ok")
                    and len(results[name].get("items", [])) > 0):
                first_hit_emitted = True
                print(json.dumps({"event": "first_hit", "strategy": name,
                                  "latency_s": results[name]["latency_s"],
                                  "hits": len(results[name]["items"]),
                                  "top": results[name]["items"][0]}),
                      file=sys.stderr, flush=True)

    # merge + dedupe by (repo, path); keep best score, note finder strategies
    merged = {}
    for name, r in results.items():
        if not r.get("ok"):
            continue
        for it in r["items"]:
            key = (it["repo"], it["path"])
            cur = merged.get(key)
            if cur is None or (it.get("score") or 0) > (cur.get("score") or 0):
                it = dict(it); it["found_by"] = [name]; merged[key] = it
            elif name not in cur["found_by"]:
                cur["found_by"].append(name)

    ranked = sorted(merged.values(), key=lambda i: (i.get("score") or 0), reverse=True)
    lat = {n: {"ok": r["ok"], "latency_s": r["latency_s"],
               "hits": len(r.get("items", []))} for n, r in results.items()}
    winner = min((n for n, r in results.items()
                 if r["ok"] and len(r.get("items", [])) > 0),
                 key=lambda n: results[n]["latency_s"], default=None)

    try:  # keep the fast path hot
        os.makedirs(os.path.dirname(WINNERS_LOG), exist_ok=True)
        with open(WINNERS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "winner": winner,
                                "latency": lat}) + "\n")
    except OSError:
        pass

    print(json.dumps({"winner_strategy": winner, "strategy_latency": lat,
                      "similar_code": ranked}, indent=1))


if __name__ == "__main__":
    main()
