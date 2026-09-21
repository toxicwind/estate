#!/usr/bin/env python3
"""e2e probe: one model, few requests, through the full GuideLLM scorer path."""
import asyncio
import json
import re
import sys

sys.path.insert(0, "/home/toxic/sovereign/projects/guidellm/src")

SECRETS = "/home/toxic/.secrets"
PROMPT = "Output exactly: ABSTRACT-7X3Q. No other text."
SENTINEL = "ABSTRACT-7X3Q"
MODEL = "nex-agi/nex-n2.5-mini:free"
TOKENIZER = "nex-agi/Nex-N2.5-mini"


def load_secret(name):
    pat = re.compile(r"^\s*(?:export\s+)?%s\s*=\s*(.+?)\s*$" % re.escape(name))
    with open(SECRETS) as f:
        for line in f:
            m = pat.match(line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    raise SystemExit("key %s not found" % name)


async def main():
    from guidellm.schemas.benchmark.entrypoints import (
        BenchmarkArgs,
        BenchmarkScenario,
    )
    from guidellm.benchmark.entrypoints import benchmark_generative_text

    key = load_secret("OPENROUTER_API_KEY_FREE")
    args = BenchmarkScenario(
        spec=BenchmarkArgs(
            backend={
                "kind": "openai_http",
                "target": "https://openrouter.ai/api/v1",
                "model": MODEL,
                "api_key": key,
                "validate_backend": False,
                "max_tokens": 300,
            },
            data=[
                {
                    "kind": "in_memory_dict_list",
                    "data": [{"prompt": PROMPT} for _ in range(3)],
                }
            ],
            profile={"kind": "synchronous"},
            tokenizer={"kind": "huggingface_auto", "model": TOKENIZER},
            metrics={
                "kind": "generative",
                "scorers": ["instruction_following"],
                "scorer_config": {
                    "instruction_following": {
                        "sentinel": SENTINEL,
                        "strip_thinking": True,
                    }
                },
            },
            outputs=[{"kind": "json", "path": "/tmp/e2e-probe.json"}],
            constraints=[{"kind": "max_requests", "count": 3}],
        )
    )
    report, _ = await benchmark_generative_text(args)
    d = json.loads(open("/tmp/e2e-probe.json").read())
    bench = d["benchmarks"][0]
    print("quality:", json.dumps(bench.get("quality"), indent=1))
    print("instrument:", json.dumps(bench.get("quality_instrument"), indent=1))
    print("req latency mean:", bench.get("request_latency", {}).get("mean"))
    print("completed:", bench.get("completed", {}).get("total"))


def _run():
    asyncio.run(main())


if __name__ == "__main__":
    _run()
