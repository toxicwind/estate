#!/usr/bin/env python3
"""Assemble the 15 corrected cron bodies for the main agent to apply via cron.update.
Worker-run cron.update is blocked ('resolve cron chat owner: execution has no durable
presentation chat owner'), so this package hands the exact bodies to the main agent.
"""
import json, re, sys

WS = "/home/hatch/workspace"
PROJECT = f"{WS}/skills/classifier-project"

MIRRORS = {
    "cell-mirror-supervisor": f"{WS}/cron.d/minutely/cell-mirror-supervisor__interval@5m.md",
    "lane-poller-forge": f"{WS}/cron.d/minutely/lane-poller-forge__interval@1m.md",
    "lane-poller-lumen": f"{WS}/cron.d/minutely/lane-poller-lumen__interval@1m.md",
    "lane-poller-pry": f"{WS}/cron.d/minutely/lane-poller-pry__interval@1m.md",
    "lane-poller-tally": f"{WS}/cron.d/minutely/lane-poller-tally__interval@1m.md",
    "lane-poller-sable": f"{WS}/cron.d/minutely/lane-poller-sable__interval@1m.md",
    "lane-poller-cinder": f"{WS}/cron.d/minutely/lane-poller-cinder__interval@1m.md",
    "lane-poller-vesper": f"{WS}/cron.d/minutely/lane-poller-vesper__interval@1m.md",
    "lane-poller-warden": f"{WS}/cron.d/minutely/lane-poller-warden__interval@1m.md",
    "reshim-side-channel": f"{WS}/cron.d/minutely/reshim-side-channel__interval@15m.md",
    "nudge-queue-drain": f"{WS}/cron.d/minutely/nudge-queue-drain__interval@2m.md",
    "lane-poller-finch": f"{WS}/cron.d/minutely/lane-poller-finch__interval@1m.md",
    "lane-poller-nightjar": f"{WS}/cron.d/minutely/lane-poller-nightjar__interval@1m.md",
    "muse-db-drain": f"{WS}/cron.d/minutely/muse-db-drain__interval@1m.md",
    "warden-wakeup": f"{WS}/cron.d/minutely/warden-wakeup__interval@15m.md",
}

DELIVERY = {
    "cell-mirror-supervisor": [],
    "reshim-side-channel": [{"chat_id": "25d4da06-0b4e-4ac9-9e6d-ba6f796f78e1"}],
    "warden-wakeup": [{"chat_id": "d4c283e6-185f-420e-a8cc-1a2c1aa35a61"}],
}
POLLER_OPS = [{"chat_id": "3c80069b-7b76-4467-83c3-6400d5a14260"}]
for _id in MIRRORS:
    if _id not in DELIVERY:
        DELIVERY[_id] = POLLER_OPS

REASONS = {
    "cell-mirror-supervisor": "prepended canonical directive block",
    "lane-poller-forge": "prepended canonical directive block",
    "lane-poller-lumen": "prepended canonical directive block",
    "lane-poller-pry": "prepended canonical directive block",
    "lane-poller-tally": "prepended canonical directive block",
    "lane-poller-sable": "prepended canonical directive block",
    "lane-poller-cinder": "prepended canonical directive block",
    "lane-poller-vesper": "prepended canonical directive block",
    "lane-poller-warden": "prepended canonical directive block",
    "reshim-side-channel": "prepended canonical directive block",
    "nudge-queue-drain": "cross-chat-wake false positive on a prohibition/documentation line: restored the CRITICAL no-send paragraph with behavioral rewording (trigger phrase removed, shim path + main-agent ownership kept); prepended canonical directive block",
    "lane-poller-finch": "prepended canonical directive block",
    "lane-poller-nightjar": "prepended canonical directive block",
    "muse-db-drain": "prepended canonical directive block",
    "warden-wakeup": "never-ask false positive on three auto-repair bullets: kept each bullet's operational instruction, replaced the bare tail with a behavioral line naming the standing auto-repair permission; prepended canonical directive block",
}

MARKER = "Standing task directive (Chris's autonomous-operation order"


def extract_body(path):
    """Mirror layout: directive blockquote, blank, ---, frontmatter, ---, body."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    # directive blockquote = leading lines starting with '>'
    qi = 0
    while qi < len(lines) and lines[qi].startswith(">"):
        qi += 1
    quote = "\n".join(lines[:qi]).strip()
    rest = "\n".join(lines[qi:])
    m = re.match(r"^\s*---\n[\s\S]*?\n---\n([\s\S]*)$", rest)
    assert m, f"frontmatter parse failed for {path}"
    body = quote + "\n\n" + m.group(1).lstrip("\n")
    assert MARKER in body, f"directive marker missing in {path}"
    assert body.count(MARKER) == 1, f"directive marker duplicated in {path}"
    return body.rstrip("\n") + "\n"


entries = []
for _id, path in MIRRORS.items():
    body = extract_body(path)
    entries.append({
        "id": _id,
        "delivery": DELIVERY[_id],
        "reason": REASONS[_id],
        "body": body,
    })

out = {
    "at": "2026-10-03T03:15:52Z",
    "blocker": (
        "cron.update is rejected from this detached worker run: "
        "'resolve cron chat owner: execution has no durable presentation chat owner' "
        "(6 attempts, two parameter variants incl. explicit delivery). "
        "Apply from Main Chat: for each entry, cron.update(id, body=entry.body). "
        "Omit other fields to preserve schedule/delivery/timeout. "
        "Then re-read each via cron.view to confirm the marker appears exactly once."
    ),
    "verified": (
        "All 29 non-system saved bodies read via cron.view 2026-10-03; mirrors matched "
        "saved bodies on all 15 changed tasks. 14 tasks clean (directive present, no "
        "trigger shapes). 15 need the bodies below. System jobs and diagnostic probes untouched."
    ),
    "entries": entries,
}

out_path = f"{PROJECT}/reports/corrected-bodies-2026-10-03.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(f"wrote {out_path} with {len(entries)} entries")
