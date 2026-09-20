import subprocess

files = [
    "/home/toxic/projects/portal-audit/raw/user_pasted_clipboard_long_content_as_file_```meta_awareness bl.txt",
    "/home/toxic/projects/moonbox-live/BACKUP-1787105555/original/user_pasted_clipboard_long_content_as_file_```meta_awareness bl.txt",
]
for f in files:
    print("### " + f)
    p = subprocess.run(["rg", "-F", "-n", "-m", "10", ".krabby", f],
                       capture_output=True, text=True)
    for line in p.stdout.strip().split("\n")[:10]:
        print("  " + line[:250])
