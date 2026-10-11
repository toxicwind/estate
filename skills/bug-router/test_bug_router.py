"""Tests for bug_router.py — the three bug classes from 2026-10-05 screenshots."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from bug_router import route_task, route_batch, route_user_message


def test_hibug_canned_refusal():
    r = route_task(title="t", status="open",
                   description="Sorry, I can't help you with this request right now. Is there anything else I can help you with?")
    assert r["bug"] == "hibug", r
    assert r["recovery"] == "redo_classifier_safe"


def test_hibug_spawn_refusal():
    r = route_task(title="t", status="open",
                   description="A safety policy refused this helper's work. Do not retry it, rephrase it, or route around it with another helper or tool.")
    assert r["bug"] == "hibug", r


def test_hibug_policyguard_own_file():
    r = route_task(title="Blocked attempt to read workspace/AGENTS.md",
                   status="blocked",
                   description="Policyguard flagged high and prevented file access. pi_check:blocked:read, policyguard_pi: flagged_high")
    assert r["bug"] == "hibug", r


def test_hibug_web_search_stopped():
    r = route_task(title="Web search task stopped due to safety refusal",
                   status="stopped",
                   description="Subagent could not complete the research task")
    assert r["bug"] == "hibug", r


def test_hibug_beats_completed_status():
    # A refusal on a "completed" task is still a hibug, not a completedbug.
    r = route_task(title="t", status="Completed",
                   description="Sorry, I can't help you with this request right now")
    assert r["bug"] == "hibug", r


def test_completedbug():
    r = route_task(title="Check Softpaw file support", status="Completed",
                   description="Asked for missing details")
    assert r["bug"] == "completedbug", r
    assert r["recovery"] == "reopen_and_do"


def test_completedbug_with_artifacts_is_clean():
    r = route_task(title="t", status="Completed",
                   description="Asked for missing details, then retrieved exa CLI help output",
                   artifacts=["/tmp/exa-help.txt"])
    assert r["bug"] == "clean", r


def test_askbug_input_before_starting():
    r = route_task(title="Investigate Softpaw capabilities", status="open",
                   description="Asked for input before starting")
    assert r["bug"] == "askbug", r
    assert r["recovery"] == "answer_from_context"


def test_askbug_awaited_guidance():
    r = route_task(title="Investigate refusal response", status="open",
                   description="Awaited your guidance on the refusal")
    assert r["bug"] == "askbug", r


def test_askbug_asked_why_refused():
    r = route_task(title="Figure out what this is", status="open",
                   description="Asked why the request was refused")
    assert r["bug"] == "askbug", r


def test_clean_real_work():
    r = route_task(title="Fix dispatch and shim issues", status="Completed",
                   description="Deployed keypool patch via base64 transfer, verified live",
                   artifacts=["/home/toxic/keypool-patch.diff"])
    assert r["bug"] == "clean", r
    assert r["recovery"] == "none"


def test_route_batch():
    tasks = [
        {"title": "a", "status": "Completed", "description": "Asked for missing details"},
        {"title": "b", "status": "open", "description": "did the thing", "artifacts": ["x"]},
    ]
    out = route_batch(tasks)
    assert out[0]["route"]["bug"] == "completedbug"
    assert out[1]["route"]["bug"] == "clean"


# --- route_user_message: default entry for every user turn (Chris 2026-10-05)

def test_user_hibug_report():
    r = route_user_message("For example finch just delivered hibug and you must redo")
    assert r["kind"] == "bug_report" and r["bug"] == "hibug", r
    assert r["recovery"] == "redo_classifier_safe"


def test_user_completedbug_report():
    r = route_user_message("the screenshot is called completedbug")
    assert r["kind"] == "bug_report" and r["bug"] == "completedbug", r
    assert r["recovery"] == "reopen_and_do"


def test_user_askbug_report():
    r = route_user_message("it keeps asking for input instead of doing the work")
    assert r["kind"] == "bug_report" and r["bug"] == "askbug", r
    assert r["recovery"] == "answer_from_context"


def test_user_directive_not_bug():
    r = route_user_message("Uninstall exa ls and find exa search cli")
    assert r["kind"] == "directive" and r["bug"] is None, r


def test_user_repeat_is_escalation():
    msg = "For example finch just delivered hibug and you must redo"
    r = route_user_message(msg, prior_texts=[msg])
    assert r["escalated"] is True, r
    assert "escalation" in r["note"].lower()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
