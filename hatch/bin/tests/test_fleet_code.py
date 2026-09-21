#!/usr/bin/env python3
"""Tests for fleet-code (hatch/bin/fleet-code).

Runs the full session lifecycle against scratch git repos in /tmp.
Each test uses a fresh FLEET_CODE_ROOT. Exits nonzero on first failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

FLEET_CODE = os.environ.get("FLEET_CODE_BIN",
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fleet-code"))

passed = []
def check(name, cond, detail=""):
    if cond:
        passed.append(name)
        print(f"ok   {name}")
    else:
        print(f"FAIL {name} {detail}")
        sys.exit(1)

def run(*args, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, FLEET_CODE, *args],
                       capture_output=True, text=True, env=env)
    return r

def gconfig(d):
    subprocess.run(["git", "-C", d, "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", d, "config", "user.name", "t"], check=True)

def mkrepo():
    d = tempfile.mkdtemp(prefix="fc-repo-")
    subprocess.run(["git", "init", "-q", "-b", "main", d], check=True)
    gconfig(d)
    open(os.path.join(d, "a.txt"), "w").write("a\n")
    open(os.path.join(d, "b.txt"), "w").write("b\n")
    subprocess.run(["git", "-C", d, "add", "."], check=True)
    subprocess.run(["git", "-C", d, "commit", "-qm", "init"], check=True)
    return d

def fresh_env():
    root = tempfile.mkdtemp(prefix="fc-root-")
    return {"FLEET_CODE_ROOT": root}, root

# --- 1. start + packet + merge + done (happy path) ---
env, root = fresh_env()
repo = mkrepo()
r = run("start", repo, "s1", env_extra=env)
check("start", r.returncode == 0, r.stderr)
gconfig(os.path.join(root, "sessions", "s1", "main"))
r = run("packet", "s1", "p1", "a.txt", env_extra=env)
check("packet p1", r.returncode == 0, r.stderr)
r = run("packet", "s1", "p2", "b.txt", env_extra=env)
check("packet p2", r.returncode == 0, r.stderr)
# simulate agent work in each packet worktree
for pkt, fn, content in (("p1", "a.txt", "a1\n"), ("p2", "b.txt", "b2\n")):
    wt = os.path.join(root, "sessions", "s1", "packets", pkt)
    open(os.path.join(wt, fn), "w").write(content)
    subprocess.run(["git", "-C", wt, "commit", "-qam", f"work {pkt}"],
                   check=True)
main_wt = os.path.join(root, "sessions", "s1", "main")
pre = subprocess.run(["git", "-C", main_wt, "rev-parse", "HEAD"],
                     capture_output=True, text=True).stdout.strip()
r = run("merge", "s1", "--test", "true", env_extra=env)
check("merge ok", r.returncode == 0, r.stderr)
rep = json.load(open(os.path.join(root, "sessions", "s1", "merge-report.json")))
check("merge report", rep["merged"] == ["p1", "p2"] and not rep["quarantined"],
      json.dumps(rep))
check("merged content",
      open(os.path.join(main_wt, "a.txt")).read() == "a1\n"
      and open(os.path.join(main_wt, "b.txt")).read() == "b2\n")
check("no-ff merges",
      subprocess.run(["git", "-C", main_wt, "log", "--oneline", "--merges"],
                     capture_output=True, text=True).stdout.count("\n") >= 2)
r = run("done", "s1", env_extra=env)
check("done archives", r.returncode == 0 and "archived" in r.stdout, r.stderr)

# --- 2. path collision refused (exact + parent dir) ---
env, root = fresh_env()
repo = mkrepo()
run("start", repo, "s2", env_extra=env)
gconfig(os.path.join(root, "sessions", "s2", "main"))
run("packet", "s2", "p1", "sub/dir", env_extra=env)
r = run("packet", "s2", "p2", "sub/dir/file.txt", env_extra=env)
check("child-path collision refused", r.returncode != 0 and "collision" in r.stderr,
      r.stderr)
r = run("packet", "s2", "p3", "sub", env_extra=env)
check("parent-dir collision refused", r.returncode != 0 and "collision" in r.stderr,
      r.stderr)
r = run("packet", "s2", "p4", "other.txt", env_extra=env)
check("non-overlap allowed", r.returncode == 0, r.stderr)

# --- 3. failing test quarantines, history rolled back, branch kept ---
env, root = fresh_env()
repo = mkrepo()
run("start", repo, "s3", env_extra=env)
gconfig(os.path.join(root, "sessions", "s3", "main"))
run("packet", "s3", "good", "a.txt", env_extra=env)
run("packet", "s3", "bad", "b.txt", env_extra=env)
wt = os.path.join(root, "sessions", "s3", "packets", "good")
open(os.path.join(wt, "a.txt"), "w").write("good\n")
subprocess.run(["git", "-C", wt, "commit", "-qam", "good"], check=True)
wt = os.path.join(root, "sessions", "s3", "packets", "bad")
open(os.path.join(wt, "b.txt"), "w").write("bad\n")
subprocess.run(["git", "-C", wt, "commit", "-qam", "bad"], check=True)
main_wt = os.path.join(root, "sessions", "s3", "main")
# test passes for first packet, fails after second: use a marker file
open(os.path.join(main_wt, "gate.sh"), "w").write("#!/bin/sh\ntest ! -f b.txt || grep -q good b.txt\n")
# simpler: fail when b.txt contains "bad"
open(os.path.join(main_wt, "gate.sh"), "w").write("#!/bin/sh\n! grep -q bad b.txt 2>/dev/null\n")
subprocess.run(["chmod", "+x", os.path.join(main_wt, "gate.sh")], check=True)
subprocess.run(["git", "-C", main_wt, "add", "gate.sh"], check=True)
subprocess.run(["git", "-C", main_wt, "commit", "-qm", "gate"], check=True)
pre_sha = subprocess.run(["git", "-C", main_wt, "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
r = run("merge", "s3", "--test", "./gate.sh", env_extra=env)
check("merge stops on test failure", r.returncode == 0, r.stderr)
rep = json.load(open(os.path.join(root, "sessions", "s3", "merge-report.json")))
check("bad quarantined", rep["quarantined"][0]["packet"] == "bad"
      and rep["failed_test"] == "bad", json.dumps(rep))
check("good merged", rep["merged"] == ["good"], json.dumps(rep))
post_sha = subprocess.run(["git", "-C", main_wt, "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
check("history rolled back past bad merge",
      post_sha != pre_sha and
      subprocess.run(["git", "-C", main_wt, "log", "--oneline", "--merges"],
                     capture_output=True, text=True).stdout.count("bad") == 0)
check("bad branch preserved",
      subprocess.run(["git", "-C", main_wt, "branch", "--list",
                      "fleet/s3/bad"], capture_output=True,
                     text=True).stdout.strip() != "")
r = run("done", "s3", env_extra=env)
check("done refuses with quarantined", r.returncode != 0, r.stdout)

# --- 4. shlex: quoted test args work ---
env, root = fresh_env()
repo = mkrepo()
run("start", repo, "s4", env_extra=env)
gconfig(os.path.join(root, "sessions", "s4", "main"))
run("packet", "s4", "p1", "a.txt", env_extra=env)
wt = os.path.join(root, "sessions", "s4", "packets", "p1")
open(os.path.join(wt, "a.txt"), "w").write("x\n")
subprocess.run(["git", "-C", wt, "commit", "-qam", "x"], check=True)
r = run("merge", "s4", "--test", "sh -c 'exit 0'", env_extra=env)
check("shlex quoted test", r.returncode == 0, r.stderr)
rep = json.load(open(os.path.join(root, "sessions", "s4", "merge-report.json")))
check("shlex merged", rep["merged"] == ["p1"], json.dumps(rep))

print(f"\n{len(passed)} tests passed")
