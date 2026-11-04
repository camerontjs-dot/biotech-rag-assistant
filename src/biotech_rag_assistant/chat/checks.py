"""Mechanical checks on a model answer. These are not semantic-support checks.

A block of generated text is shown only if all of these hold:

1. every citation ref names a passage supplied for this turn (no invented refs);
2. at least one citation's quotation is located verbatim in its passage's trusted text (after
   whitespace/quote-mark/dash folding), and is at least three words long;
3. every number in the block (digits and common number words) appears in the text or identity
   metadata of a passage the block validly cites. This targets the known fabrication path: an
   invented value cited to a real passage that never states it (tests/test_known_gaps.py).

Otherwise the block is withheld, with the reason recorded. Displayed quotations are always the
application's own source text located by offsets; the model's quote string is only used to find
the span.

Advisory notes (never withholding): source conditions whose markers do not appear in the blocks
citing that passage, steps in a different order from the source, frequency words absent from the
cited body text (for example "daily" found only in a section heading), and verification language.

Passing these checks means the cited passage was supplied and contains the quoted words and the
numbers. It does not mean the passage supports the statement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from biotech_rag_assistant.chat.contract import ModelAnswer
from biotech_rag_assistant.chat.evidence import EvidencePassage
from biotech_rag_assistant.retrieval import STOPWORDS, tokenize

MECHANICAL_NOTE = (
    "Mechanical checks only: each shown statement cites a passage supplied for this turn, its "
    "quotation was found word for word in that passage, and every number in it appears in the "
    "cited passage. That does not establish that the passage supports the statement. Read the "
    "source passages."
)
MIN_QUOTE_WORDS = 3
MAX_ADVISORIES = 8

NUMBER_WORDS: dict[str, float] = {
    "zero": 0,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
    "million": 1_000_000,
    "twice": 2,
    "half": 0.5,
    "quarter": 0.25,
    "tenth": 0.1,
    "dozen": 12,
}
# "one", "once" and "single" are omitted on purpose: they are overwhelmingly non-numeric
# ("one of the weights"); a digit "1" is still checked.
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
FREQUENCY_WORDS = frozenset(
    "daily weekly monthly quarterly annually annual yearly hourly nightly biweekly".split()
)
VERIFICATION_WORDS = frozenset(
    "verified validated certified compliant guaranteed verification validation".split()
)
# Words that introduce a condition, exception, or ordering constraint in source text. A condition
# counts as reflected when the answer contains at least half of the content words that follow the
# marker (up to the next punctuation or marker), so paraphrases ("before the run can start" for
# "cannot start until") do not raise notes, while a dropped trigger or hold condition does.
_CONDITION_MARKERS = (
    r"prior to|must not|may not|before|until|unless|except|if|when|whenever|only|cannot|after"
    r"|without"
)
_MARKER_RE = re.compile(rf"(?i)\b(?:{_CONDITION_MARKERS})\b")
_CLAUSE_STOP_RE = re.compile(rf"(?i)[,.;:!?]|\b(?:{_CONDITION_MARKERS})\b")
MAX_CLAUSE_WORDS = 8

_FOLD = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        " ": " ",
    }
)


class CheckIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    ref: str | None = None


class CitationCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str
    resolved: bool
    chunk_id: str | None = None
    quote_found: bool = False
    highlight_start: int | None = None
    highlight_end: int | None = None
    issue: str | None = None


class BlockView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    kind: str
    text: str | None
    withheld: bool
    withheld_reason: str | None = None
    withheld_text: str | None = None
    citations: list[CitationCheck]
    valid_refs: list[str]
    issues: list[CheckIssue]


class MissingView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested: str
    explanation: str
    related_refs: list[str]


class AnswerView(BaseModel):
    """What the interface may render for a model answer, after mechanical checks."""

    model_config = ConfigDict(extra="forbid")

    status: str
    blocks: list[BlockView]
    missing_information: list[MissingView]
    clarifying_question: str
    advisories: list[CheckIssue]
    unknown_refs: list[str]
    withheld_count: int
    shown_count: int
    support_scope: str = "mechanical_only"
    support_note: str = MECHANICAL_NOTE


@dataclass(frozen=True)
class _Folded:
    text: str
    index_map: list[int]


def check_answer(
    answer: ModelAnswer,
    evidence: list[EvidencePassage],
    *,
    user_messages: list[str],
) -> AnswerView:
    by_ref = {passage.ref: passage for passage in evidence}
    position = {passage.ref: index for index, passage in enumerate(evidence)}
    user_values = _values(" ".join(user_messages))
    unknown_refs: list[str] = []
    blocks: list[BlockView] = []

    for index, block in enumerate(answer.blocks, start=1):
        citations: list[CitationCheck] = []
        issues: list[CheckIssue] = []
        invented = False
        for citation in block.citations:
            passage = by_ref.get(citation.ref)
            if passage is None:
                invented = True
                if citation.ref not in unknown_refs:
                    unknown_refs.append(citation.ref)
                citations.append(
                    CitationCheck(ref=citation.ref, resolved=False, issue="unknown_ref")
                )
                issues.append(
                    CheckIssue(
                        code="unknown_citation_ref",
                        ref=citation.ref,
                        message=f"cites {citation.ref!r}, which was not supplied for this turn",
                    )
                )
                continue
            located = locate_quote(passage.text, citation.quote)
            if located is None:
                problem = (
                    "quote_too_short"
                    if len(tokenize(citation.quote)) < MIN_QUOTE_WORDS
                    else "quote_not_in_passage"
                )
                citations.append(
                    CitationCheck(
                        ref=citation.ref,
                        resolved=True,
                        chunk_id=passage.chunk_id,
                        issue=problem,
                    )
                )
                issues.append(
                    CheckIssue(
                        code=problem,
                        ref=citation.ref,
                        message=(
                            f"the quotation for {citation.ref} is shorter than "
                            f"{MIN_QUOTE_WORDS} words"
                            if problem == "quote_too_short"
                            else f"the quotation for {citation.ref} does not appear in that "
                            "passage"
                        ),
                    )
                )
                continue
            citations.append(
                CitationCheck(
                    ref=citation.ref,
                    resolved=True,
                    chunk_id=passage.chunk_id,
                    quote_found=True,
                    highlight_start=located[0],
                    highlight_end=located[1],
                )
            )

        valid_refs = list(dict.fromkeys(c.ref for c in citations if c.quote_found))
        withheld_reason: str | None = None
        if invented:
            withheld_reason = "It cites a source that was not supplied for this turn."
        elif not valid_refs:
            withheld_reason = (
                "No quotation from a supplied passage could be located for it."
                if block.citations
                else "It cites no source passage."
            )
        else:
            unsupported = _values(_strip_identifiers(block.text, evidence)) - _allowed_values(
                [by_ref[ref] for ref in valid_refs]
            )
            if unsupported:
                shown = ", ".join(_fmt(value) for value in sorted(unsupported))
                from_user = sorted(unsupported & user_values)
                withheld_reason = (
                    f"It states {shown}, which does not appear in its cited passage text."
                )
                if from_user:
                    withheld_reason += (
                        f" ({', '.join(_fmt(v) for v in from_user)} appears in your messages, "
                        "not in the documents.)"
                    )
                issues.append(
                    CheckIssue(code="value_not_in_cited_source", message=withheld_reason)
                )

        blocks.append(
            BlockView(
                index=index,
                kind=block.kind,
                text=None if withheld_reason else block.text,
                withheld=withheld_reason is not None,
                withheld_reason=withheld_reason,
                withheld_text=block.text if withheld_reason else None,
                citations=citations,
                valid_refs=valid_refs if not withheld_reason else [],
                issues=issues,
            )
        )

    missing: list[MissingView] = []
    for item in answer.missing_information:
        related = [ref for ref in item.related_refs if ref in by_ref]
        for ref in item.related_refs:
            if ref not in by_ref and ref not in unknown_refs:
                unknown_refs.append(ref)
        missing.append(
            MissingView(
                requested=item.requested, explanation=item.explanation, related_refs=related
            )
        )

    shown = [block for block in blocks if not block.withheld]
    advisories = _advisories(answer, shown, by_ref, position)
    return AnswerView(
        status=answer.status,
        blocks=blocks,
        missing_information=missing,
        clarifying_question=answer.clarifying_question.strip(),
        advisories=advisories[:MAX_ADVISORIES],
        unknown_refs=unknown_refs,
        withheld_count=len(blocks) - len(shown),
        shown_count=len(shown),
    )


def locate_quote(passage_text: str, quote: str) -> tuple[int, int] | None:
    """Return ``(start, end)`` offsets of ``quote`` in ``passage_text``, or ``None``.

    Matching folds case, runs of whitespace, curly quotes, and dashes, then maps the match back
    to original offsets. The first occurrence is returned. Quotes under three words never match.
    """
    needle = _fold(quote).text.strip().strip("\"'").strip()
    if len(tokenize(needle)) < MIN_QUOTE_WORDS:
        return None
    haystack = _fold(passage_text)
    found = haystack.text.find(needle)
    if found < 0:
        return None
    start = haystack.index_map[found]
    end = haystack.index_map[found + len(needle) - 1] + 1
    return start, end


def _fold(text: str) -> _Folded:
    chars: list[str] = []
    index_map: list[int] = []
    previous_space = True
    for position, char in enumerate(text.translate(_FOLD)):
        if char.isspace():
            if previous_space:
                continue
            char = " "
            previous_space = True
        else:
            previous_space = False
        lowered = char.lower()
        # Keep one output char per input char so offsets map back exactly.
        chars.append(lowered if len(lowered) == 1 else char)
        index_map.append(position)
    return _Folded(text="".join(chars), index_map=index_map)


def _values(text: str) -> set[float]:
    values: set[float] = set()
    for match in NUMBER_RE.finditer(text):
        raw = match.group(0)
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", raw):
            raw = raw.replace(",", "")
        try:
            values.add(float(raw.replace(",", ".")))
        except ValueError:
            continue
    for token in tokenize(text):
        if token in NUMBER_WORDS:
            values.add(float(NUMBER_WORDS[token]))
    return values


def _allowed_values(passages: list[EvidencePassage]) -> set[float]:
    allowed: set[float] = set()
    for passage in passages:
        allowed |= _values(passage.text)
        allowed |= _values(f"{passage.version} {passage.effective_date}")
    return allowed


def _strip_identifiers(text: str, evidence: list[EvidencePassage]) -> str:
    """Remove document ids, versions, refs, and list enumerators before reading numbers."""
    for passage in evidence:
        text = text.replace(passage.chunk_id, " ").replace(passage.doc_id, " ")
        text = re.sub(
            rf"(?i)\b(?:v|version)\s?{re.escape(passage.version)}\b", " ", text
        )
    text = re.sub(r"\[?\bS\d{1,2}\b\]?", " ", text)
    return re.sub(r"(?i)^\s*(?:step\s*)?\d{1,2}[.):]\s+", " ", text)


def _fmt(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?i)\b{re.escape(phrase)}\b", text) is not None


def _advisories(
    answer: ModelAnswer,
    shown: list[BlockView],
    by_ref: dict[str, EvidencePassage],
    position: dict[str, int],
) -> list[CheckIssue]:
    advisories: list[CheckIssue] = []

    # Conditions in the cited sentences whose content no block citing them reflects. Scoped to
    # sentences a shown quotation overlaps: a condition in an uncited sentence is not the claim's.
    citing: dict[str, list[str]] = {}
    spans: dict[str, list[tuple[int, int]]] = {}
    for block in shown:
        for ref in block.valid_refs:
            citing.setdefault(ref, []).append(block.text or "")
        for citation in block.citations:
            if citation.quote_found and citation.highlight_start is not None:
                spans.setdefault(citation.ref, []).append(
                    (citation.highlight_start, citation.highlight_end or citation.highlight_start)
                )
    for ref, texts in citing.items():
        answer_terms = {_stem(token) for token in tokenize(" ".join(texts))}
        cited_text = " ".join(_cited_sentences(by_ref[ref].text, spans.get(ref, [])))
        for clause, terms in _condition_clauses(cited_text):
            needed = max(1, -(-len(terms) // 2))
            if len(terms & answer_terms) >= needed:
                continue
            advisories.append(
                CheckIssue(
                    code="condition_not_reflected",
                    ref=ref,
                    message=(
                        f"{by_ref[ref].label} ({ref}) states a condition the answer may not "
                        f"reflect: “{clause}”"
                    ),
                )
            )

    # Steps or checklist items cited out of source order.
    previous: tuple[int, int] | None = None
    for block in shown:
        if block.kind not in {"step", "checklist_item"}:
            continue
        first = next((c for c in block.citations if c.quote_found), None)
        if first is None:
            continue
        key = (position[first.ref], first.highlight_start or 0)
        if previous is not None and key < previous:
            advisories.append(
                CheckIssue(
                    code="order_differs_from_source",
                    message="Some steps are listed in a different order from the source text.",
                )
            )
            break
        previous = key

    # Frequency words absent from the cited body text.
    for block in shown:
        words = set(tokenize(block.text or "")) & FREQUENCY_WORDS
        for word in sorted(words):
            cited = [by_ref[ref] for ref in block.valid_refs]
            if any(_contains_phrase(passage.text, word) for passage in cited):
                continue
            in_heading = [p for p in cited if _contains_phrase(p.section_heading, word)]
            note = (
                f" It appears only in the section heading “{in_heading[0].section_heading}"
                "”, which is not treated as evidence."
                if in_heading
                else ""
            )
            advisories.append(
                CheckIssue(
                    code="qualifier_not_in_cited_text",
                    message=f"“{word}” does not appear in the cited passage text.{note}",
                )
            )

    # Verification language the application cannot back.
    for block in shown:
        words = set(tokenize(block.text or "")) & VERIFICATION_WORDS
        if words:
            advisories.append(
                CheckIssue(
                    code="verification_language",
                    message=(
                        f"The answer uses “{sorted(words)[0]}”. The application does not "
                        "verify claims; it checks citations mechanically."
                    ),
                )
            )
            break

    if answer.status in {"answered", "partially_answered"} and not shown:
        advisories.append(
            CheckIssue(
                code="status_without_shown_statements",
                message=f"The model reported status '{answer.status}', but no statement passed "
                "the citation checks.",
            )
        )
    return advisories


def _stem(token: str) -> str:
    """A deliberately crude stem so "documents"/"documented" or "sign"/"signs" compare equal."""
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return token


def _cited_sentences(text: str, spans: list[tuple[int, int]]) -> list[str]:
    """Sentences of ``text`` that overlap any ``(start, end)`` span, in source order."""
    sentences: list[str] = []
    for match in re.finditer(r"[^.!?]+[.!?]*", text):
        if any(start < match.end() and end > match.start() for start, end in spans):
            sentences.append(match.group(0).strip())
    return sentences


def _condition_clauses(text: str) -> list[tuple[str, set[str]]]:
    """Each condition marker in ``text`` with the source words that follow it."""
    clauses: list[tuple[str, set[str]]] = []
    for match in _MARKER_RE.finditer(text):
        tail = text[match.end() :]
        stop = _CLAUSE_STOP_RE.search(tail)
        words = (tail[: stop.start()] if stop else tail).split()[:MAX_CLAUSE_WORDS]
        terms = {
            _stem(token)
            for token in tokenize(" ".join(words))
            if token not in STOPWORDS and len(token) > 1
        }
        if terms:
            clauses.append((" ".join([match.group(0), *words]), terms))
    return clauses
