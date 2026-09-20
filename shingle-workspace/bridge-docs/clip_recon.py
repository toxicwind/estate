import os, json

files = [
    "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve(1).txt",
    "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve(1).txt",
]
for f in files:
    st = os.stat(f)
    print("FILE:", f)
    print("  bytes:", st.st_size)
    with open(f, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    print("  lines:", len(lines))
    for i, ln in enumerate(lines[:4]):
        print("  L%d: %s" % (i, ln[:200].replace("\n", " ")))

print()
print("=== libs ===")
for mod in ["scipy", "gensim", "torch", "nltk", "pyarrow", "fastparquet"]:
    try:
        m = __import__(mod)
        print(mod, getattr(m, "__version__", "ok"))
    except Exception as e:
        print(mod, "MISSING")
