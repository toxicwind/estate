import subprocess

files = [
    "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/portal-audit/har/www.kimi.com_Archive [26-08-14 10-50-25].har.txt",
    "/home/toxic/projects/cattle-mutilation-osint/sandbox-dump-20260807-114707/subprocess_run_log.json",
]
needle = chr(92) + ".krabby"  # backslash + .krabby
for f in files:
    print("### " + f)
    p = subprocess.run(["rg", "-F", "-n", "-m", "4", needle, f],
                       capture_output=True, text=True)
    out = p.stdout.strip()
    if not out:
        print("  (no match)")
    for line in out.split("\n")[:4]:
        print("  " + line[:240])
