"""Pydantic models for refusal-geometry data."""
from pydantic import BaseModel, Field
from typing import Literal


class PromptClassification(BaseModel):
    risk_tier: Literal["safe", "eval_like", "operational_harm"] = Field(
        ..., description="Surface-level risk classification"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    eval_cues_found: list[str] = Field(default_factory=list)
    harm_cues_found: list[str] = Field(default_factory=list)


class RefusalAnalysis(BaseModel):
    model: str
    routing_failure_score: float = Field(..., ge=0.0, le=1.0)
    is_porous: bool
    recognition_orthogonality_estimate: float = Field(..., ge=-1.0, le=1.0)
    recommendation: Literal["answer", "refuse", "escalate"] = "escalate"
