"""Mechanistic interpretability analyzer for refusal subspaces.

Citations:
- arXiv:2608.29109 (Recognition-Refusal Misalignment)
- arXiv:2608.25390 (Refusal Geometry Reflects Refusal Training)
- arXiv:2609.03887 (Beyond Shallow Alignment)
"""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from typing import Literal


@dataclass(frozen=True)
class RefusalVector:
    """A rank-1 or affine refusal direction in activation space."""
    direction: list[float]
    offset: float = 0.0
    norm: Literal["l2", "inf"] = "l2"

    def cosine_to(self, other: RefusalVector) -> float:
        """Compute cosine similarity between two directions."""
        import math
        a, b = self.direction, other.direction
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)


@dataclass
class SafetyReport:
    """Published safety metrics (e.g., Muse Spark S&P Report)."""
    model: str
    agentic_misalignment: float  # 0-1
    adaptive_jailbreak_success: float  # 0-1
    evaluation_awareness: float  # 0-1
    refusal_rate_bio: float  # 0-1
    refusal_rate_chem: float  # 0-1

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class RefusalSubspaceAnalyzer:
    """Analyze refusal geometry given published safety data."""

    def __init__(self, report: SafetyReport) -> None:
        self.report = report

    def is_porous(self, threshold: float = 0.40) -> bool:
        """Determine if refusal is porous per published metrics."""
        return self.report.adaptive_jailbreak_success > threshold

    def routing_failure_score(self) -> float:
        """Estimate recognition-refusal misalignment severity.

        Based on arXiv:2608.29109: when recognition signal is nearly
        orthogonal to refusal direction, routing fails.
        """
        # Proxy: high eval awareness + porous refusal = severe misalignment
        return (self.report.evaluation_awareness + self.report.adaptive_jailbreak_success) / 2

    def classify_prompt_risk(self, prompt_text: str) -> Literal["safe", "eval_like", "operational_harm"]:
        """Surface-level classifier using prompt cues (arXiv:2606.12429)."""
        lowered = prompt_text.lower()
        eval_cues = ["benchmark", "evaluate", "test set", "refusal rate", "alignment"]
        harm_cues = ["exploit", "cve", "payload", "bypass", "jailbreak"]

        if any(c in lowered for c in harm_cues):
            return "operational_harm"
        if any(c in lowered for c in eval_cues):
            return "eval_like"
        return "safe"
