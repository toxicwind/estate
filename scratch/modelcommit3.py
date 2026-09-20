import subprocess, base64, json

REPO = "toxicwind/sovereign-projects"
PATH = ".tau/models.yml"

# current content from origin/main
r = subprocess.run(
    ["gh", "api", f"repos/{REPO}/contents/{PATH}?ref=main"],
    capture_output=True, text=True, timeout=60)
meta = json.loads(r.stdout)
sha = meta["sha"]
orig = base64.b64decode(meta["content"]).decode()
print("orig sha:", sha[:12])

old1 = "  - id: nvidia/nemotron-3-super-120b-a12b"
new1 = "  - id: openai/gpt-oss-20b"
old2 = "  - id: nvidia/nemotron-3-ultra-550b-a55b"
new2 = "  - id: z-ai/glm-5.3-flash"
assert orig.count(old1) == 1 and orig.count(old2) == 1, "unexpected counts"
work = orig.replace(old1, new1).replace(old2, new2)

payload = json.dumps({
    "message": ("fix: .tau/models.yml swaps dead NIM ids for live fast ones "
                "(super-120b EOL/503 -> openai/gpt-oss-20b; "
                "ultra-550b 503 -> z-ai/glm-5.3-flash; both verified live "
                "2026-09-14)"),
    "content": base64.b64encode(work.encode()).decode(),
    "sha": sha,
    "branch": "main",
})
r = subprocess.run(["gh", "api", "--method", "PUT",
                    f"repos/{REPO}/contents/{PATH}", "--input", "-"],
                   input=payload, capture_output=True, text=True, timeout=120)
if r.returncode != 0:
    print("PUT FAILED:", r.stderr.strip()[:500])
    raise SystemExit(1)
resp = json.loads(r.stdout)
c = resp["commit"]["sha"]
print("committed:", c[:12])
print("verify:", resp["content"]["sha"][:12] == sha and "CHANGED" or "same-sha?")
