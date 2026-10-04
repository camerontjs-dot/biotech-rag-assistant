"""Select a span in an already authorized body under a bounded punctuation policy.

This pure helper neither finds sources nor determines semantic support. See
``docs/citation-span-selection.md`` for its deliberately limited input language.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_ABBREVIATION = re.compile(r"(?<!\w)(Dr|No|[ap]\.m)\.(?!\w)")
_UNCERTAIN_WORDS = frozenset(
    {"approx", "art", "cf", "dept", "e.g", "est", "etc", "fig", "i.e", "inc", "ref",
     "resp", "rev", "sec", "vol", "vs"}
)
_UNSUPPORTED = frozenset("()[]{}<>…。！？")


class SpanSelection(BaseModel):
    """Exact body-relative offsets, or an explicit refusal with no selected text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["selected", "not_found", "ambiguous", "boundary_uncertain"]
    text: str | None = None
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)


def _next_nonspace(body: str, start: int) -> int:
    while start < len(body) and body[start].isspace():
        start += 1
    return start


def _internal_periods(body: str) -> set[int] | None:
    """Recognize only the documented abbreviation contexts; otherwise refuse."""
    periods: set[int] = set()
    for match in _ABBREVIATION.finditer(body):
        after = _next_nonspace(body, match.end())
        if after == match.end() or after == len(body):
            return None
        token = match[1]
        if token == "No":
            accepted = body[after].isascii() and body[after].isdigit()
        elif token == "Dr":
            accepted = re.match(r"[A-Z][a-z]+\b", body[after:]) is not None
        else:
            accepted = body[after].islower()
        if not accepted:
            return None
        periods.update(
            index for index in range(match.start(), match.end()) if body[index] == "."
        )
    return periods


def sentence_spans(body: str) -> list[tuple[int, int]] | None:
    """Return bounded syntactic spans, or ``None`` for an uncertain boundary.

    Offsets are Python string indices. Nothing is normalized or synthesized.
    Uncertainty anywhere in the supplied body refuses the entire selection.
    """
    if any(character in _UNSUPPORTED for character in body):
        return None
    if any(ord(character) < 32 and character not in "\t\r\n" for character in body):
        return None
    internal_periods = _internal_periods(body)
    if internal_periods is None:
        return None

    spans: list[tuple[int, int]] = []
    start = index = _next_nonspace(body, 0)
    quoted = False
    while index < len(body):
        character = body[index]
        if character == '"':
            quoted = not quoted
            index += 1
            continue
        if character in "'’":
            # Apostrophes inside words are punctuation-free for this policy.
            if not (index > 0 and index + 1 < len(body)
                    and body[index - 1].isalpha() and body[index + 1].isalpha()):
                return None
        elif character in "‘“”":
            return None
        if character not in ".!?":
            index += 1
            continue
        if index in internal_periods:
            index += 1
            continue
        if (character == "." and index > 0 and index + 1 < len(body)
                and body[index - 1].isdigit() and body[index + 1].isdigit()):
            index += 1
            continue

        end = index + 1
        if end < len(body) and body[end] == '"':
            if not quoted:
                return None
            end += 1
            quoted = False
        if quoted or (end < len(body) and not body[end].isspace()):
            return None
        after = _next_nonspace(body, end)
        if after < len(body) and (
            body[after] in "abcdefghijklmnopqrstuvwxyz" or body[after].isdigit()
        ):
            return None
        if character == ".":
            word_start = index
            while word_start > 0 and body[word_start - 1].isalpha():
                word_start -= 1
            word = body[word_start:index]
            if not word or word.lower() in _UNCERTAIN_WORDS:
                return None
            # Short tokens may be initials or abbreviations. EOS cannot omit
            # following text; before more text this uncertainty is not guessed.
            if after < len(body) and len(word) <= 3:
                return None
        spans.append((start, end))
        start = index = after
    if quoted:
        return None
    end = len(body.rstrip())
    if start < end:
        spans.append((start, end))
    return spans


def select_enclosing_sentence(body: str, quote: str) -> SpanSelection:
    """Select one enclosing span only for a unique exact quote and safe boundaries.

    A second match is searched from one character after the first so overlapping
    occurrences are ambiguous too. This does not establish sentence completeness
    in arbitrary language, source authorization, or claim-level support.
    """
    if not quote or quote.isspace():
        return SpanSelection(outcome="not_found")
    quote_at = body.find(quote)
    if quote_at < 0:
        return SpanSelection(outcome="not_found")
    if body.find(quote, quote_at + 1) >= 0:
        return SpanSelection(outcome="ambiguous")
    spans = sentence_spans(body)
    if spans is None:
        return SpanSelection(outcome="boundary_uncertain")
    quote_end = quote_at + len(quote)
    for start, end in spans:
        if start <= quote_at and quote_end <= end:
            return SpanSelection(outcome="selected", text=body[start:end], start=start, end=end)
    return SpanSelection(outcome="not_found")
