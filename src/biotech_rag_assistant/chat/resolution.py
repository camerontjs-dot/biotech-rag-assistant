"""Deterministic turn resolution: which retrieval queries a chat message runs.

Conversation history may resolve a reference ("that step", "the stated procedure"), but it never
becomes evidence. Resolution only chooses which queries go through the maintained retrieval path
(unchanged ``RetrievalConfig``: status gate, BM25, ``score_floor``, 0.6 coverage gate):

- the current message, after removing leading correction/discourse markers and a fixed list of
  conversational task words (only when the word is absent from the corpus vocabulary, so a word
  that could describe document content is never removed); and/or
- the *anchor*: the retrieval query of the topic the conversation is on, carried forward
  verbatim when the message refers back or is too short to search on its own.

The user's message itself is never rewritten; the model always sees it verbatim. Every attempt
(query, origin, hits, top coverage) is recorded so a reader can see exactly what was searched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from biotech_rag_assistant.chat.evidence import CorpusBinding
from biotech_rag_assistant.models import RetrievalHit
from biotech_rag_assistant.retrieval import (
    RetrievalConfig,
    content_terms,
    coverage,
    index_text,
    query_retriever,
    tokenize,
)

ResolutionKind = Literal[
    "standalone",
    "topic_change",
    "follow_up",
    "follow_up_with_new_terms",
    "correction",
    "clarification_needed",
    "not_found",
    "courtesy",
]

# Words that say what to do with an answer rather than what it is about. Removed from the
# retrieval query only when absent from the corpus vocabulary.
TASK_WORDS = frozenset(
    """
    explain explaining summarize summarise summary describe outline overview checklist list
    tell show give walk please kindly help simplify rephrase clarify plain english bullet
    bullets format table briefly quickly me say says turn convert into
    """.split()
)

CORRECTION_LEADS: tuple[tuple[str, ...], ...] = (
    ("i", "meant"),
    ("i", "mean"),
    ("not", "that"),
    ("not", "quite"),
    ("no",),
    ("nope",),
    ("actually",),
    ("sorry",),
    ("correction",),
    ("wrong",),
    ("rather",),
    ("instead",),
)
DISCOURSE_LEADS: tuple[tuple[str, ...], ...] = (
    ("what", "about"),
    ("how", "about"),
    ("what", "else"),
    ("and",),
    ("also",),
    ("then",),
    ("but",),
)
ANAPHORA = frozenset(
    """
    that this it its those these they them their there above previous prior earlier preceding
    same former latter aforementioned stated mentioned described listed quoted cited
    """.split()
)
COURTESY = frozenset(
    "thanks thank you ok okay great cool perfect got it hello hi hey bye goodbye cheers much"
    " very so".split()
)

ELLIPTICAL_MAX_TERMS = 3
NEW_TERMS_MIN = 3
TOPIC_CHANGE_MIN_TERMS = 2
COURTESY_MAX_TOKENS = 6


class RetrievalAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: str
    query: str
    hit_chunk_ids: list[str]
    top_coverage: float | None
    passed_relevance_gate: bool


class Resolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ResolutionKind
    explanation: str
    retrieval_query: str
    removed_words: list[str]
    cues: list[str]
    content_term_count: int
    new_topic_requested: bool
    anchor_turn: int | None = None
    anchor_query: str | None = None
    anchor_message: str | None = None
    attempts: list[RetrievalAttempt]

    @property
    def is_follow_up(self) -> bool:
        return self.kind in {"follow_up", "follow_up_with_new_terms"}


@dataclass(frozen=True)
class ActiveTopic:
    """The topic a conversation is on: the retrieval query that produced its evidence."""

    query: str
    turn_index: int
    user_message: str


@dataclass(frozen=True)
class ResolvedTurn:
    resolution: Resolution
    hit_sets: list[tuple[str, list[RetrievalHit]]]
    next_topic: ActiveTopic | None


def resolve_turn(
    message: str,
    *,
    turn_index: int,
    active_topic: ActiveTopic | None,
    new_topic: bool,
    binding: CorpusBinding,
    config: RetrievalConfig,
) -> ResolvedTurn:
    tokens = tokenize(message)
    if tokens and len(tokens) <= COURTESY_MAX_TOKENS and set(tokens) <= COURTESY:
        return ResolvedTurn(
            resolution=Resolution(
                kind="courtesy",
                explanation="No search was needed for this message.",
                retrieval_query="",
                removed_words=[],
                cues=[],
                content_term_count=0,
                new_topic_requested=new_topic,
                attempts=[],
            ),
            hit_sets=[],
            next_topic=active_topic,
        )

    if new_topic:
        active_topic = None

    correction_lead, rest = _strip_leads(tokens, CORRECTION_LEADS)
    discourse_lead, rest = _strip_leads(rest, DISCOURSE_LEADS)
    kept: list[str] = []
    removed: list[str] = [*correction_lead, *discourse_lead]
    for token in rest:
        if token in TASK_WORDS and token not in binding.vocabulary:
            removed.append(token)
        else:
            kept.append(token)
    # When nothing was removed, search the message exactly as typed, so a plain question runs
    # the same retrieval as ``/answer`` would.
    retrieval_query = message if not removed else " ".join(kept)
    term_count = len(content_terms(retrieval_query))
    anaphora = sorted(set(kept) & ANAPHORA)
    cues = [*anaphora]
    if discourse_lead:
        cues.append(" ".join(discourse_lead))
    if correction_lead:
        cues.append(" ".join(correction_lead))

    current_attempt, current_hits = _attempt(
        binding, retrieval_query, config, origin="current_message"
    )
    attempts = [current_attempt]

    def result(
        kind: ResolutionKind,
        explanation: str,
        hit_sets: list[tuple[str, list[RetrievalHit]]],
        next_topic: ActiveTopic | None,
        anchor: ActiveTopic | None = None,
    ) -> ResolvedTurn:
        return ResolvedTurn(
            resolution=Resolution(
                kind=kind,
                explanation=explanation,
                retrieval_query=retrieval_query,
                removed_words=removed,
                cues=cues,
                content_term_count=term_count,
                new_topic_requested=new_topic,
                anchor_turn=anchor.turn_index if anchor else None,
                anchor_query=anchor.query if anchor else None,
                anchor_message=anchor.user_message if anchor else None,
                attempts=attempts,
            ),
            hit_sets=hit_sets,
            next_topic=next_topic,
        )

    this_topic = ActiveTopic(query=retrieval_query, turn_index=turn_index, user_message=message)
    current = ("current_message", current_hits)

    if correction_lead:
        if current_hits and term_count >= TOPIC_CHANGE_MIN_TERMS:
            return result(
                "correction",
                "Treated as a correction: the earlier topic was set aside and only the "
                "corrected request was searched.",
                [current],
                this_topic,
            )
        return result(
            "clarification_needed",
            "Treated as a correction, but the corrected request did not match an approved "
            "passage on its own, so the earlier topic was set aside without a replacement.",
            [],
            None,
        )

    if active_topic is None:
        if current_hits:
            return result(
                "standalone",
                "Searched the approved documents for this message.",
                [current],
                this_topic,
            )
        # Only a short message that leans on a reference ("explain that step") needs the earlier
        # topic; a longer one stands on its own and simply found nothing.
        if (anaphora or discourse_lead) and term_count <= ELLIPTICAL_MAX_TERMS:
            return result(
                "clarification_needed",
                "This message refers back to something, but there is no earlier answered "
                "topic in this conversation to connect it to.",
                [],
                None,
            )
        return result(
            "not_found",
            "No approved passage matched enough of this message's key terms.",
            [],
            None,
        )

    anchor_origin = f"anchor:turn_{active_topic.turn_index}"
    anchor_attempt, anchor_hits = _attempt(
        binding, active_topic.query, config, origin=anchor_origin
    )
    attempts.insert(0, anchor_attempt)
    anchor = (anchor_origin, anchor_hits)
    turn = active_topic.turn_index

    def follow_up(reason: str) -> ResolvedTurn:
        return result(
            "follow_up",
            f"Treated as a follow-up to turn {turn}: the message {reason}, so the passages for "
            f"turn {turn}'s question were retrieved again.",
            [anchor],
            active_topic,
            active_topic,
        )

    def follow_up_with_new_terms() -> ResolvedTurn:
        return result(
            "follow_up_with_new_terms",
            f"Treated as a follow-up to turn {turn} that adds new terms: passages for turn "
            f"{turn}'s question and for this message were both retrieved.",
            [anchor, current],
            active_topic,
            active_topic,
        )

    if anaphora:
        if current_hits and term_count >= NEW_TERMS_MIN:
            return follow_up_with_new_terms()
        return follow_up(f"refers back ({', '.join(repr(word) for word in anaphora)})")
    if discourse_lead:
        if current_hits:
            return follow_up_with_new_terms()
        if term_count <= 1:
            return follow_up("continues the previous question")
        return result(
            "not_found",
            "This message adds a new focus, but no approved passage matched enough of its "
            "key terms.",
            [],
            None,
        )
    if current_hits and term_count >= TOPIC_CHANGE_MIN_TERMS:
        anchor_docs = {hit.chunk.doc_id for hit in anchor_hits}
        if current_hits[0].chunk.doc_id in anchor_docs:
            return result(
                "standalone",
                "Searched this message on its own: it matched approved passages without "
                "needing the earlier question (same document as the current topic).",
                [current],
                this_topic,
            )
        return result(
            "topic_change",
            "Treated as a new topic: the message matched approved passages on its own and "
            "did not refer back to the earlier answer.",
            [current],
            this_topic,
        )
    if current_hits:
        return follow_up_with_new_terms()
    if term_count <= ELLIPTICAL_MAX_TERMS:
        return follow_up("is too short to search on its own")
    return result(
        "not_found",
        "No approved passage matched enough of this message's key terms.",
        [],
        None,
    )


def _strip_leads(
    tokens: list[str], leads: tuple[tuple[str, ...], ...]
) -> tuple[list[str], list[str]]:
    """Remove repeated leading marker phrases (e.g. "no sorry i meant")."""
    removed: list[str] = []
    rest = list(tokens)
    changed = True
    while changed and rest:
        changed = False
        for lead in leads:
            if tuple(rest[: len(lead)]) == lead:
                removed.extend(lead)
                rest = rest[len(lead) :]
                changed = True
                break
    return removed, rest


def _attempt(
    binding: CorpusBinding, query: str, config: RetrievalConfig, *, origin: str
) -> tuple[RetrievalAttempt, list[RetrievalHit]]:
    hits = query_retriever(binding.retriever, query, config) if query.strip() else []
    top = binding.retriever.query(query, top_k=1) if query.strip() else []
    top_coverage = round(coverage(query, index_text(top[0].chunk)), 4) if top else None
    return (
        RetrievalAttempt(
            origin=origin,
            query=query,
            hit_chunk_ids=[hit.chunk.chunk_id for hit in hits],
            top_coverage=top_coverage,
            passed_relevance_gate=bool(hits),
        ),
        hits,
    )
