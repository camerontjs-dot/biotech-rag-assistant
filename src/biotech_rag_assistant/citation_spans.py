"""Validate an exact quote inside caller-authorized BODY offsets.

This module does not infer sentence boundaries or establish their semantic
completeness. The caller must obtain that authority before using this helper.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_PARAGRAPH_BREAK = re.compile(r"(?>\r\n|\r|\n)[^\S\r\n]*(?>\r\n|\r|\n)|\u2029")


class SpanSelection(BaseModel):
    """An exact authorized slice, or a refusal with null text and offsets."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["selected", "not_found", "ambiguous", "bounds_required", "invalid_bounds"]
    text: str | None = None
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)


def select_authorized_span(
    body: str,
    quote: str,
    *,
    authorized_start: int | None = None,
    authorized_end: int | None = None,
) -> SpanSelection:
    """Return only the explicitly authorized slice containing one unique quote.

    Positions are Python Unicode string indices, with an inclusive start and
    exclusive end. Uniqueness is checked over the entire supplied BODY, including
    overlapping occurrences. The selected slice may not cross a paragraph break.
    Missing bounds are never reconstructed from punctuation or quote positions.

    The caller owns source status, provenance, body identity and the correctness
    and completeness of its supplied bounds. A ``selected`` result establishes
    literal containment only; it does not certify a sentence or claim support.
    """
    if not quote or quote.isspace():
        return SpanSelection(outcome="not_found")
    quote_at = body.find(quote)
    if quote_at < 0:
        return SpanSelection(outcome="not_found")
    if body.find(quote, quote_at + 1) >= 0:
        return SpanSelection(outcome="ambiguous")
    if authorized_start is None and authorized_end is None:
        return SpanSelection(outcome="bounds_required")
    if type(authorized_start) is not int or type(authorized_end) is not int:
        return SpanSelection(outcome="invalid_bounds")
    if not 0 <= authorized_start < authorized_end <= len(body):
        return SpanSelection(outcome="invalid_bounds")
    if not authorized_start <= quote_at < quote_at + len(quote) <= authorized_end:
        return SpanSelection(outcome="invalid_bounds")
    selected = body[authorized_start:authorized_end]
    if _PARAGRAPH_BREAK.search(selected):
        return SpanSelection(outcome="invalid_bounds")
    return SpanSelection(
        outcome="selected", text=selected, start=authorized_start, end=authorized_end,
    )
