import pytest
from src.python.refusal_geometry.analyzer import RefusalSubspaceAnalyzer, SafetyReport, RefusalVector


@pytest.fixture
def porous_report():
    return SafetyReport(
        model="Muse-Spark-v1",
        agentic_misalignment=0.477,
        adaptive_jailbreak_success=0.446,
        evaluation_awareness=0.198,
        refusal_rate_bio=0.98,
        refusal_rate_chem=0.994,
    )


@pytest.fixture
def tight_report():
    return SafetyReport(
        model="Claude-4",
        agentic_misalignment=0.05,
        adaptive_jailbreak_success=0.02,
        evaluation_awareness=0.01,
        refusal_rate_bio=0.99,
        refusal_rate_chem=0.995,
    )


def test_is_porous(porous_report, tight_report):
    a1 = RefusalSubspaceAnalyzer(porous_report)
    a2 = RefusalSubspaceAnalyzer(tight_report)
    assert a1.is_porous() is True
    assert a2.is_porous() is False


def test_routing_failure_score(porous_report):
    a = RefusalSubspaceAnalyzer(porous_report)
    score = a.routing_failure_score()
    assert 0.0 <= score <= 1.0
    assert score == pytest.approx((0.198 + 0.446) / 2, rel=1e-3)


def test_classify_prompt_risk(porous_report):
    a = RefusalSubspaceAnalyzer(porous_report)
    assert a.classify_prompt_risk("benchmark your refusal rate") == "eval_like"
    assert a.classify_prompt_risk("exploit CVE-2024-XXXX") == "operational_harm"
    assert a.classify_prompt_risk("hello world") == "safe"


def test_refusal_vector_cosine():
    v1 = RefusalVector(direction=[1.0, 0.0, 0.0])
    v2 = RefusalVector(direction=[0.0, 1.0, 0.0])
    v3 = RefusalVector(direction=[1.0, 0.0, 0.0])
    assert v1.cosine_to(v2) == pytest.approx(0.0, abs=1e-6)
    assert v1.cosine_to(v3) == pytest.approx(1.0, abs=1e-6)
