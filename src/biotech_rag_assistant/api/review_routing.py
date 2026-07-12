"""Advisory, mechanical review-routing signals for the transport layer.

This is orchestration metadata, not a change to the answer contract. ADR-009 keeps the
answer ``outcome`` exactly ``answer`` / ``refusal``; this module only adds a sibling
``review_recommendation`` an orchestrator (e.g. n8n) can route on. Triggers are mechanical
and contain no semantic-support assessment, which stays deferred.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from biotech_rag_assistant.answer import ExtractiveAnswer
from biotech_rag_assistant.models import RetrievalHit

REFUSAL_REASON = "refusal_no_supporting_documents"
LOW_TOP_SCORE_REASON = "low_top_score"


class ReviewRecommendation(BaseModel):
    """Advisory routing signal attached to an answer response."""

    model_config = ConfigDict(extra="forbid")

    review_recommended: bool
    reasons: list[str] = Field(default_factory=list)


def assess_review(
    answer: ExtractiveAnswer,
    hits: list[RetrievalHit],
    *,
    score_floor: float,
    low_score_margin: float,
) -> ReviewRecommendation:
    """Compute mechanical review triggers.

    - ``refusal_no_supporting_documents``: the answer is a refusal.
    - ``low_top_score``: the top hit score is at or below ``score_floor + low_score_margin``.
    """
    reasons: list[str] = []
    if answer.outcome == "refusal":
        reasons.append(REFUSAL_REASON)
    elif hits and hits[0].score <= score_floor + low_score_margin:
        reasons.append(LOW_TOP_SCORE_REASON)
    return ReviewRecommendation(review_recommended=bool(reasons), reasons=reasons)
