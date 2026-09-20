#!/usr/bin/env python3
"""
toolcall-agent: minimal tool-capable agent harness for yote.

Drives a local llama-server (OpenAI /v1/chat/completions, tools enabled) through
a real ReAct-style tool loop:

  model -> tool_calls (validator-first) -> execute -> tool result message -> model ...

Research grounding:
  - arXiv:2510.03847 (SLM survey): SLMs are sufficient for tool calling with
    guided decoding + strict JSON-schema output + VALIDATOR-FIRST execution.
  - ToolSpec (arXiv:2604.13519): tool calls are constrained-decoding problems;
    valid tool names/arg keys are schema-determined, so validate against the
    declared schema before executing and repair on violation.
  - BFCL v4 (Berkeley): single-turn schema-constrained calling is the solved
    regime at small scale; this harness targets exactly that regime with a
    retry/repair loop for robustness.

HFT layer: set TOOLCALL_RACE=1 to route every chat call through hft_race.py —
redundant-lane racing (direct :25152 vs herd-routed :25100), first-valid-wins,
hot persistent connections, per-hop timings, winner ledger. This is the
recommended mode for the Agent 2 pilot: if one lane dies, the other wins
transparently.

Usage:
  python3 agent_loop.py "What GPU is in this box? Compute its VRAM in GiB."
  TOOLCALL_RACE=1 python3 agent_loop.py "..."
"""
import ast
import json
import os
import subprocess
import sys
import time
import urllib.request

BASE = os.environ.get("TOOLCALL_BASE", "http://127.0.0.1:25152")
MODEL = os.environ.get("TOOLCALL_MODEL", "qwen3.5-9b-tool")
PER_ATTEMPT_TIMEOUT = int(os.environ.get("TOOLCALL_TIMEOUT", "120"))
MAX_TOOL_ROUNDS = int(os.environ.get("TOOLCALL_MAX_ROUNDS", "6"))
MAX_REPAIR = 2
RACE = os.environ.get("TOOLCALL_RACE", "0") == "1"

TOOLS = [
    {"type": "function", "function": {
        "name": "calculator",
        "description": "Evaluate a simple arithmetic expression (+ - * / ** // % and parentheses, numbers only).",
        "parameters": {"type": "object",
                       "properties": {"expression": {"type": "string", "description": "e.g. '37*42'"}},
                       "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "sysinfo",
        "description": "Read-only system fact about this host.",
        "parameters": {"type": "object",
                       "properties": {"field": {"type": "string",
                                               "enum": ["gpu", "cpu", "memory", "hostname", "uptime"]}},
                       "required": ["field"]}}},
]


def _safe_eval(expr):
    """Validate-first arithmetic: AST whitelist, no eval() of raw code."""
    tree = ast.parse(expr, mode="eval")
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
               ast.Pow, ast.USub, ast.UAdd, ast.Load)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError("disallowed node: %s" % type(node).__name__)
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("non-numeric constant")
    return eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}})


def _run(cmd, timeout=10):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()


def _sysinfo(field):
    if field == "hostname":
        return _run(["hostname"])
    if field == "uptime":
        return _run(["uptime", "-p"])
    if field == "gpu":
        return _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    if field == "cpu":
        out = _run(["nproc"])
        model = _run(["sh", "-c", "grep -m1 model\\ name /proc/cpuinfo | cut -d: -f2"])
        return "%s CPUs: %s" % (out, model)
    if field == "memory":
        return _run(["free", "-h"])
    raise ValueError("unknown field")


def validate_and_run(call):
    """Validator-first execution: schema-check, then run, then return (ok, payload)."""
    fn = call.get("function", {}) or {}
    name = fn.get("name")
    args = fn.get("arguments", "{}")
    if name not in ("calculator", "sysinfo"):
        return False, "unknown tool: %r (available: calculator, sysinfo)" % name
    try:
        params = json.loads(args) if isinstance(args, str) else args
    except Exception as e:
        return False, "arguments not valid JSON: %s" % e
    try:
        if name == "calculator":
            if "expression" not in params or not isinstance(params["expression"], str):
                return False, "calculator requires string field 'expression'"
            return True, str(_safe_eval(params["expression"]))
        if name == "sysinfo":
            if params.get("field") not in ("gpu", "cpu", "memory", "hostname", "uptime"):
                return False, "sysinfo requires field in [gpu,cpu,memory,hostname,uptime]"
            return True, _sysinfo(params["field"])
    except Exception as e:
        return False, "tool execution failed: %s" % e
    return False, "unreachable"


def _chat_direct(messages, tools=True):
    body = {"model": MODEL, "messages": messages, "temperature": 0,
            "tool_choice": "auto" if tools else "none"}
    if tools:
        body["tools"] = TOOLS
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=PER_ATTEMPT_TIMEOUT) as r:
        return json.load(r), {}


def _chat_race(messages, tools=True):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hft_race
    resp, meta = hft_race.race_chat(
        messages,
        tools=TOOLS if tools else None,
        tool_choice="auto" if tools else "none",
        temperature=0, ceiling=PER_ATTEMPT_TIMEOUT)
    return resp, meta


def chat(messages, tools=True):
    if RACE:
        return _chat_race(messages, tools)
    return _chat_direct(messages, tools)


def run_turn(user_prompt, system_prompt=None, verbose=True):
    t0 = time.time()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    transcript = []
    for round_i in range(MAX_TOOL_ROUNDS):
        resp, meta = chat(messages)
        msg = resp["choices"][0]["message"]
        finish = resp["choices"][0].get("finish_reason")
        transcript.append({"round": round_i, "finish_reason": finish,
                           "tool_calls": msg.get("tool_calls"),
                           "content": msg.get("content"),
                           "race": meta.get("winner") if meta else None,
                           "ms_total": meta.get("ms_total") if meta else None})
        tcs = msg.get("tool_calls") or []
        messages.append(msg)
        if verbose:
            lane = (" [lane=%s %sms]" % (meta.get("winner"), meta.get("ms_total"))
                    if meta else "")
            print("--- round %d (finish=%s, %.1fs)%s ---" %
                  (round_i, finish, time.time() - t0, lane))
            for tc in tcs:
                print("TOOL:", tc["function"]["name"], tc["function"]["arguments"])
        if not tcs:
            if verbose:
                print("FINAL:", (msg.get("content") or "")[:2000])
            return {"final": msg.get("content"), "rounds": round_i + 1,
                    "elapsed_s": round(time.time() - t0, 2), "transcript": transcript}
        repaired = 0
        for tc in tcs:
            ok, payload = validate_and_run(tc)
            if not ok and repaired < MAX_REPAIR:
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": "VALIDATION ERROR (fix args and call again): %s" % payload})
                repaired += 1
            else:
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(payload)})
                if verbose:
                    print("RESULT:", str(payload)[:300])
    return {"final": None, "rounds": MAX_TOOL_ROUNDS, "error": "max tool rounds exceeded",
            "transcript": transcript}


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "What GPU is in this box? Tell me its total VRAM in MiB, "
        "then use the calculator to convert that to GiB.")
    system = ("You are Shingle, a local agent on yote. You have two tools: calculator "
              "(arithmetic) and sysinfo (read-only host facts: gpu, cpu, memory, hostname, uptime). "
              "When a question needs a fact or a calculation, call the tool; never guess numbers. "
              "Answer concisely after you have the tool results.")
    out = run_turn(prompt, system)
    with open("/tmp/toolcall-transcript.json", "w") as f:
        json.dump(out, f, indent=2)
    print("ROUNDS:", out.get("rounds"), "ELAPSED:", out.get("elapsed_s"),
          "RACE:" , "on" if RACE else "off")
