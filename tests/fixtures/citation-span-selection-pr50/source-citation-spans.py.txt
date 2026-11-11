"""Select a citation span inside one already authorized body.

The caller supplies the body. This module does not retrieve, read headings,
or decide whether the selected sentence supports a claim.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SpanSelection(BaseModel):
    """One deterministic sentence selection, or a refusal to guess."""

    model_config = ConfigDict(extra="forbid")

    outcome: Literal["selected", "not_found", "ambiguous"]
    text: str | None = None
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """Return sentence offsets. A sentence ends at a period before whitespace or EOS."""
    spans: list[tuple[int, int]] = []
    start = 0
    index = 0
    while index < len(text):
        at_period = text[index] == "."
        boundary = index + 1 == len(text) or text[index + 1].isspace()
        if at_period and boundary:
            spans.append((start, index + 1))
            start = index + 1
            while start < len(text) and text[start].isspace():
                start += 1
            index = start
            continue
        index += 1
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def select_enclosing_sentence(body: str, quote: str) -> SpanSelection:
    """Select the one sentence in ``body`` that contains ``quote`` exactly once.

    A missing quote is ``not_found``. A repeated quote is ``ambiguous``.
    The returned offsets are into ``body`` and never extend past it.
    """
    if quote == "":
        return SpanSelection(outcome="not_found")
    count = body.count(quote)
    if count == 0:
        return SpanSelection(outcome="not_found")
    if count != 1:
        return SpanSelection(outcome="ambiguous")
    quote_at = body.find(quote)
    quote_end = quote_at + len(quote)
    covers = [
        (end - start, start, end)
        for start, end in sentence_spans(body)
        if start <= quote_at and quote_end <= end
    ]
    if not covers:
        return SpanSelection(outcome="not_found")
    covers.sort()
    _, start, end = covers[0]
    selected = body[start:end]
    if quote not in selected:
        return SpanSelection(outcome="not_found")
    return SpanSelection(outcome="selected", text=selected, start=start, end=end)
