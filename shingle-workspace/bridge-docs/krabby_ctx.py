import subprocess, shlex

files = [
    "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_{ log { ve.txt",
    "/home/toxic/projects/portal-audit/har/www.kimi.com_Archive [26-08-14 10-50-25].har.txt",
    "/home/toxic/projects/cattle-mutilation-osint/sandbox-dump-20260807-114707/subprocess_run_log.json",
]
for f in files:
    print("### " + f)
    p = subprocess.run(["rg", "-F", "-n", "-o", ".krabby", f, "--max-count", "6"],
                       capture_output=True, text=True)
    for line in p.stdout.strip().split("\n")[:6]:
        print("  " + line[:150])
    # context sample: first match with surrounding text
    p2 = subprocess.run(["rg", "-F", "-n", "-m", "3", ".krabby", f],
                        capture_output=True, text=True)
    for line in p2.stdout.strip().split("\n")[:3]:
        print("  CTX: " + line[:220])
