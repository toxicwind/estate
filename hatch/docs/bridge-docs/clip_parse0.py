import hashlib, json, os

files = [
    "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve(1).txt",
    "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve(1).txt",
]
for f in files:
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    print(h.hexdigest()[:16], os.path.getsize(f), f.split("/projects/")[1][:60])

print()
for f in files[:2]:
    print("parsing:", f.split("original/")[1][:40])
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        log = data.get("log", {})
        print("  OK json. creator:", json.dumps(log.get("creator"))[:120])
        print("  pages:", len(log.get("pages", [])), "entries:", len(log.get("entries", [])))
        e0 = log["entries"][0]
        print("  entry0 keys:", list(e0.keys()))
        print("  req:", e0["request"]["method"], e0["request"]["url"][:100])
        print("  resp:", e0["response"]["status"], e0["response"]["content"].get("mimeType"))
        ctext = e0["response"]["content"].get("text")
        print("  body text present:", bool(ctext), "len:", len(ctext) if ctext else 0)
        print("  started:", e0.get("startedDateTime"))
    except Exception as ex:
        print("  PARSE FAIL:", type(ex).__name__, str(ex)[:200])
