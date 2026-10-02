"""Fast bid heuristics for market/v1. Deterministic, sub-millisecond, no LLM.

confidence = clamp01(0.45*capability_match + 0.35*reputation
                     + ease_bonus - complexity*aversion*0.35 + conf_bias)
             then calibrated: confidence * cal_mult (Agora-inspired)
cost       = estimated work seconds * profile.cost_factor  (effort units;
             v1 cost-unit semantics are open per architect)
eta_s      = cost + observed bid latency

Capability match: explicit `tags` extra field wins when present; otherwise
keyword overlap between the task text and the profile vocabulary.
"""

import re

W_CAP = 0.45
W_REP = 0.35

_WORD = re.compile(r"[a-z][a-z0-9_]+")


def clamp01(x):
    return max(0.0, min(1.0, x))


def task_words(task):
    text = "%s %s" % (task.get("title", ""), task.get("desc", ""))
    return set(_WORD.findall(text.lower()))


def capability_match(profile, task):
    tags = list(task.get("tags", []) or [])
    caps = set(profile.get("caps", []))
    if tags:
        matched = [t for t in tags if t in caps]
        if profile.get("skip_on_unknown") and not matched:
            return None
        return (len(matched) / len(tags), matched)
    words = task_words(task)
    vocab = set(profile.get("keywords", []))
    known_hits = words & vocab
    # neutral when the task text carries no recognizable vocabulary
    all_vocab = set()
    return (len(known_hits) / 4.0 if known_hits else 0.5,
            sorted(known_hits))


def compute_bid(profile, rep_score, cal_mult, task, observed_latency_s=0.0):
    """Return a bid dict (confidence/cost/eta_s/capabilities), or None."""
    deadline_s = float(task.get("deadline_s", 300) or 300)
    if deadline_s > profile.get("max_eta_s", 600.0) * 2:
        # task wants far more time than this profile ever spends: skip
        pass
    m = capability_match(profile, task)
    if m is None:
        return None  # specialist stays silent on foreign work
    match, matched = m

    complexity = min(1.0, deadline_s / 600.0)
    aversion = profile.get("complexity_aversion", 0.5)
    ease_bonus = (1.0 - complexity) * 0.10

    raw = (W_CAP * match + W_REP * rep_score + ease_bonus
           - complexity * aversion * 0.35
           + profile.get("conf_bias", 0.0))
    confidence = clamp01(raw * cal_mult)
    if confidence < 0.05:
        return None

    # effort estimate: base seconds by kind, scaled by payload size
    kind = task.get("kind", "shell")
    base_s = {"shell": 5.0, "python": 20.0}.get(kind, 10.0)
    size_factor = 1.0 + min(1.0, len(str(task.get("payload", ""))) / 4000.0)
    cost = base_s * size_factor * profile.get("cost_factor", 1.0)
    eta_s = cost + observed_latency_s

    return {
        "confidence": round(confidence, 3),
        "cost": round(cost, 2),
        "eta_s": round(eta_s, 2),
        "capabilities": sorted(set(profile["caps"])),
        "tags_matched": matched,
    }
