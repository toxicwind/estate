#!/usr/bin/env python3
"""Fast Google Drive search — name + full-text content, no rsync needed.
Usage: gdrive-search.py "query" [--content] [--type doc|sheet|slide|pdf] [--limit N]
"""
import json, subprocess, sys, urllib.parse

def drive_list(q, page_size=20):
    params = json.dumps({"q": q, "pageSize": page_size,
        "fields": "files(id,name,mimeType,modifiedTime,webViewLink)",
        "orderBy": "modifiedTime desc"})
    r = subprocess.run(["hatch_gws_cli", "drive", "files", "list",
                        "--params", params],
                       capture_output=True, text=True, timeout=30)
    try:
        return json.loads(r.stdout).get("files", [])
    except Exception:
        print(f"search failed: {r.stderr[:200]}", file=sys.stderr)
        return []

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    query, search_content, mime, limit = sys.argv[1], False, None, 20
    for a in sys.argv[2:]:
        if a == "--content": search_content = True
        elif a.startswith("--type="):
            t = a.split("=", 1)[1]
            mime = {"doc": "application/vnd.google-apps.document",
                    "sheet": "application/vnd.google-apps.spreadsheet",
                    "slide": "application/vnd.google-apps.presentation",
                    "pdf": "application/pdf"}.get(t)
        elif a.startswith("--limit="): limit = int(a.split("=", 1)[1])

    q = query.replace("'", "\\'")
    clauses = ["trashed=false"]
    if search_content:
        clauses.append(f"fullText contains '{q}'")
    else:
        clauses.append(f"name contains '{q}'")
    if mime: clauses.append(f"mimeType='{mime}'")

    files = drive_list(" and ".join(clauses), limit)
    if not files:
        print("no matches"); return
    for f in files:
        mt = f.get("modifiedTime", "")[:10]
        print(f"{f['name']}  [{mt}]")
        print(f"  {f.get('webViewLink', '')}")

if __name__ == "__main__":
    main()