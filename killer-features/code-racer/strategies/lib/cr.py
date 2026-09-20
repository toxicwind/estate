#!/usr/bin/env python3
"""code-racer shared adapter library (yote).

Small, dependency-free helpers every strategy adapter uses:
- chat(): OpenAI-compatible /v1/chat/completions with fail-fast ceilings
- extract_code(): pull fenced code out of a model response
- write_solution(): emit the solution file honoring the output-path contract
- deadline(): cooperative fail-fast checks
"""
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request

# ---- backend defaults (live on yote, verified 2026-09-20) -----------------
FAST_URL   = os.environ.get("CODERACER_FAST_URL",   "http://127.0.0.1:25122/v1")
TOOL_URL   = os.environ.get("CODERACER_TOOL_URL",   "http://127.0.0.1:25152/v1")
HERD_URL   = os.environ.get("CODERACER_HERD_URL",   "http://127.0.0.1:25100/v1")
ROUTER_URL = os.environ.get("CODERACER_ROUTER_URL", "http://127.0.0.1:25104/v1")

FAST_MODEL   = os.environ.get("CODERACER_FAST_MODEL",   "fast")
TOOL_MODEL   = os.environ.get("CODERACER_TOOL_MODEL",   "qwen3.5-9b-tool")
KIMI_MODEL   = os.environ.get("CODERACER_KIMI_MODEL",   "kimi-auto")
ROUTER_MODEL = os.environ.get("CODERACER_ROUTER_MODEL", "auto")


def deadline_remaining():
    """Seconds left until CODERACER_DEADLINE; inf if unset."""
    try:
        return max(0.0, float(os.environ.get("CODERACER_DEADLINE", "inf")) - time.time())
    except ValueError:
        return float("inf")


def check_deadline(tag=""):
    if deadline_remaining() <= 2.0:
        raise TimeoutError(f"deadline reached{(' ['+tag+']') if tag else ''}")


def chat(base_url, model, prompt, max_tokens=1024, temperature=0.2,
         timeout=60, system=None):
    """One OpenAI-compatible chat call. Fail-fast: timeout is a hard ceiling."""
    check_deadline("chat-pre")
    timeout = min(timeout, max(1.0, deadline_remaining() - 2.0))
    body = {
        "model": model,
        "messages": [],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system:
        body["messages"].append({"role": "system", "content": system})
    body["messages"].append({"role": "user", "content": prompt})
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        raise RuntimeError(f"chat {model}@{base_url} failed: {e}")
    check_deadline("chat-post")
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"chat {model}: unexpected response shape")


FENCE_RE = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)


def extract_code(text, language="python"):
    """Pull code out of a model response. Prefer fenced blocks, else raw."""
    fences = FENCE_RE.findall(text or "")
    if fences:
        # prefer a fence tagged with the target language
        for lang, code in fences:
            if (lang or "").lower() in (language.lower(), language[:2].lower()):
                return code.strip()
        return fences[0][1].strip()
    return (text or "").strip()


def _parse_simple_yaml(path):
    """Minimal 'key: value' YAML subset (no pyyaml on yote)."""
    out = {}
    try:
        for line in open(path):
            if ":" not in line or line[:1] in " \t-#":
                continue
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k and v:
                out[k] = v
    except OSError:
        pass
    return out


def read_task(task_dir):
    """Liberal task reader: task.json | task.yaml | task.md | problem.md."""
    spec = {}
    p_json = os.path.join(task_dir, "task.json")
    p_yaml = os.path.join(task_dir, "task.yaml")
    if os.path.exists(p_json):
        with open(p_json) as f:
            spec = json.load(f)
    elif os.path.exists(p_yaml):
        spec = _parse_simple_yaml(p_yaml)
    md_path = None
    for cand in ("task.md", "problem.md"):
        p = os.path.join(task_dir, cand)
        if os.path.exists(p):
            md_path = p
            break
    if md_path and not spec.get("description"):
        text = open(md_path).read()
        title = ""
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#"):
                title = s.lstrip("# ").strip()
                break
        spec.setdefault("title", title or os.path.basename(os.path.abspath(task_dir)))
        spec["description"] = text
    spec.setdefault("id", os.path.basename(os.path.abspath(task_dir)))
    lang = spec.get("language") or spec.get("lang") or "python"
    spec["language"] = lang
    return spec


def spec_prompt(spec):
    lang = spec.get("language", "python")
    return (f"Task: {spec.get('title', spec.get('id', ''))}\n\n"
            f"{spec.get('description', '')}\n\n"
            f"Write a {lang} solution using ONLY the standard library "
            f"(no network, no external packages). Output ONLY the {lang} "
            f"code in a single ```{lang} fence, no explanations.")


PROBE_SYS = ("You are a test-probe generator. Output ONLY python code in one "
             "```python fence, no explanations.")


def gen_probe_code(spec):
    """Model writes probe.py from the SPEC ONLY (never reads tests/).

    probe.py: imports solution, calls the entry point with 5-8 representative
    inputs incl. edge cases, prints one JSON object per line:
      {"probe": i, "ok": true, "output": repr(result)} on success
      {"probe": i, "ok": false, "error": repr(e)} on exception
    """
    prompt = (f"Task: {spec.get('title', spec.get('id',''))}\n\n"
              f"{spec.get('description','')}\n\n"
              "Write probe.py. Requirements: `import solution`; call the "
              "task's entry point (function/class/CLI as described above) "
              "with 5-8 representative inputs including edge cases; print "
              "ONE JSON object per stdout line: "
              '{"probe": <int>, "ok": true, "output": repr(result)} on '
              'success, {"probe": <int>, "ok": false, "error": repr(exc)} '
              "on exception. Stdlib only. Output ONLY the code in one "
              "```python fence.")
    return extract_code(chat(TOOL_URL, TOOL_MODEL, prompt, max_tokens=1024,
                             temperature=0.3, timeout=90), "python")


def run_probe(code, probe_src, timeout=30):
    """Run probe.py against one candidate solution.py in a temp dir.

    Returns (results, elapsed_s); results = parsed JSON lines (may be [])."""
    workdir = tempfile.mkdtemp(prefix="cr-probe-")
    try:
        with open(os.path.join(workdir, "solution.py"), "w") as f:
            f.write(code)
        with open(os.path.join(workdir, "probe.py"), "w") as f:
            f.write(probe_src)
        t0 = time.time()
        p = subprocess.run([sys.executable, "probe.py"], cwd=workdir,
                           capture_output=True, text=True, timeout=timeout)
        el = time.time() - t0
        results = []
        for line in p.stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    results.append(json.loads(line))
                except ValueError:
                    pass
        return results, el
    except Exception:
        return [], 0.0
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def behavior_key(results):
    """Hashable behavior signature: per-probe (ok, output/error repr)."""
    return tuple((bool(r.get("ok")),
                  str(r.get("output") if r.get("ok") else r.get("error")))
                 for r in results)


def ok_count(results):
    return sum(1 for r in results if r.get("ok"))


def write_solution(output_path, filename, content):
    """Honor the output-path contract: dir -> file inside; else the file."""
    if os.path.isdir(output_path):
        dest = os.path.join(output_path, filename)
    else:
        dest = output_path
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    with open(dest, "w") as f:
        f.write(content if content.endswith("\n") else content + "\n")
    return dest


def log(msg):
    print(f"[cr] {msg}", file=sys.stderr, flush=True)


def run_tests(workdir, timeout=90):
    """Dependency-free test runner (stdlib only): discover test_*.py in workdir,
    import each as a module, run callables named test_*, count pass/fail.
    Works with plain pytest-style test functions (asserts), no pytest needed.
    Returns (passed, failed, detail_text)."""
    import importlib.util, traceback
    passed, failed, details = 0, 0, []
    deadline = time.time() + timeout
    test_files = sorted(f for f in os.listdir(workdir)
                        if f.startswith("test_") and f.endswith(".py"))
    if not test_files:
        return 0, 0, "no test files found"
    sys.path.insert(0, workdir)
    try:
        for tf in test_files:
            modname = tf[:-3] + f"_{os.getpid()}"
            try:
                spec = importlib.util.spec_from_file_location(
                    modname, os.path.join(workdir, tf))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            except Exception:
                failed += 1
                details.append(f"{tf}: COLLECTION ERROR\n{traceback.format_exc(limit=3)}")
                continue
            for name in sorted(dir(mod)):
                if not name.startswith("test_"):
                    continue
                fn = getattr(mod, name)
                if not callable(fn):
                    continue
                if time.time() > deadline:
                    details.append("TIMEOUT: test budget exhausted")
                    return passed, failed, "\n".join(details)
                try:
                    fn()
                    passed += 1
                except AssertionError as e:
                    failed += 1
                    details.append(f"{tf}::{name} FAILED: {e}")
                except Exception:
                    failed += 1
                    details.append(f"{tf}::{name} ERROR\n{traceback.format_exc(limit=5)}")
    finally:
        if workdir in sys.path:
            sys.path.remove(workdir)
    return passed, failed, "\n".join(details) if details else "all green"


def arm_timeout(default_s):
    """Set CODERACER_DEADLINE from CODERACER_TIMEOUT_S (or default) if tighter."""
    try:
        budget = float(os.environ.get("CODERACER_TIMEOUT_S", str(default_s)))
    except ValueError:
        budget = float(default_s)
    mine = time.time() + budget
    try:
        cur = float(os.environ.get("CODERACER_DEADLINE", "inf"))
    except ValueError:
        cur = float("inf")
    os.environ["CODERACER_DEADLINE"] = str(min(mine, cur))
