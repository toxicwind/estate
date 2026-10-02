import subprocess

SOV = "/home/toxic/sovereign"
r = subprocess.run(["git", "show", "origin/main:.tau/models.yml"],
                   capture_output=True, text=True, cwd=SOV, timeout=60)
print(r.stdout)
