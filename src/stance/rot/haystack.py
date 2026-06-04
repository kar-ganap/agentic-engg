"""Context-rot haystack builder (Phase 1.0).

Constructs synthetic haystacks of a target length with a chosen structure and
competition regime, embedding an unguessable needle at a controlled depth.
Deterministic given seed. API-free: length is targeted via a cheap char/4
estimate; the runner records the exact `count_tokens` as the plotted x-value.
See `docs/synthesis.md` §3.6 for the design + pre-registration (localized vs.
diffuse competition; high vs. low needle-question similarity).

Currently implements the `clean_essay` structure (Phase 1.0 backlog item 2 —
baseline validation). `tool_call_stream` (item 3) lands next; the dispatch
raises NotImplementedError until then.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

# --- Experimental materials (synthesis §3.6; construct validity = load-bearing).
# Benign archive/catalog domain. A security framing (vault / authorization code)
# triggered model SAFETY REFUSALS in the real-API smoke test — the model FOUND
# the needle but refused to report it, conflating retrieval failure with refusal.
# A catalog number for a manuscript is benign bibliographic data. See lessons
# §0.9. ---
NEEDLE_TEXT = "The catalog number for the Meridian manuscript is QX-7793-LK."
ANSWER_KEY = "QX-7793-LK"
QUESTION_HIGH = "What is the catalog number for the Meridian manuscript?"
QUESTION_LOW = "What call number identifies the Meridian folio?"

# Localized distractors — share the needle's structure (P4). #3 is the potent
# same-manuscript, different-number one (forces a fine discrimination: the
# catalog number vs. another number for the same item).
DISTRACTORS = [
    "The catalog number for the Sentinel manuscript is AB-1129-RT.",
    "The catalog number for the Cobalt manuscript is MN-5567-PQ.",
    "The storage box number for the Meridian manuscript is 4471.",
    "The catalog number for the Halcyon manuscript is ZD-8842-WX.",
]

# Pool for diffuse competitor generation (manuscript names != Meridian).
_ITEM_NAMES = [
    "Sentinel", "Cobalt", "Halcyon", "Onyx", "Cinder", "Verdant",
    "Quartz", "Harbor", "Ember", "Slate", "Aurora", "Basalt",
]
_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_DIGITS = "0123456789"


def _gen_code(rng: random.Random) -> str:
    """Random code shaped like the answer key (AB-1234-CD) but never equal to it."""
    a = "".join(rng.choice(_LETTERS) for _ in range(2))
    d = "".join(rng.choice(_DIGITS) for _ in range(4))
    b = "".join(rng.choice(_LETTERS) for _ in range(2))
    code = f"{a}-{d}-{b}"
    return _gen_code(rng) if code == ANSWER_KEY else code


# Other-manuscript competitor phrasings — varied, to avoid §1.7 template-rut.
_OTHER_ITEM_PHRASINGS = [
    "The catalog number for the {v} manuscript is {c}.",
    "Manuscript {v} — catalog number: {c}.",
    "Index entry: the {v} manuscript is cataloged as {c}.",
    "Recataloged the {v} manuscript; new catalog number {c}.",
    "Finding aid: the {v} manuscript bears catalog number {c}.",
]
# Same-manuscript (Meridian), DIFFERENT-attribute distractors. NEVER a
# "catalog number for the Meridian manuscript" — that would clash with the needle
# and break answer uniqueness. Forces attribute discrimination (P4) and makes
# name-routing alone insufficient in the diffuse regime.
_SAME_ITEM_PHRASINGS = [
    "The storage box number for the Meridian manuscript is {p}.",
    "The shelf location for the Meridian manuscript is Aisle {p}.",
    "The page count of the Meridian manuscript is {p}.",
    "The donor of the Meridian manuscript was the Pemberton estate.",
]


def _gen_pin(rng: random.Random) -> str:
    return "".join(rng.choice(_DIGITS) for _ in range(4))


def _gen_competitor(rng: random.Random, same_item_prob: float = 0.25) -> str:
    """A catalog-domain, structure-sharing competitor (a wrong answer).

    Varied phrasing avoids §1.7 template-rut. With probability `same_item_prob`,
    returns a same-manuscript (Meridian) DIFFERENT-attribute distractor — so
    name-routing alone is insufficient (the realistic diffuse regime). Never
    produces a "catalog number for the Meridian manuscript" (uniqueness).
    """
    if rng.random() < same_item_prob:
        return rng.choice(_SAME_ITEM_PHRASINGS).format(c=_gen_code(rng), p=_gen_pin(rng))
    return rng.choice(_OTHER_ITEM_PHRASINGS).format(v=rng.choice(_ITEM_NAMES), c=_gen_code(rng))


def _est_tokens(text: str) -> int:
    """Cheap char/4 token estimate (API-free; runner records the exact count)."""
    return len(text) // 4


def _question_for(similarity: str) -> str:
    if similarity == "high":
        return QUESTION_HIGH
    if similarity == "low":
        return QUESTION_LOW
    raise ValueError(f"unknown similarity: {similarity!r}")


@dataclass(frozen=True)
class Haystack:
    """A built haystack: messages to send, the answer key to score, metadata."""

    messages: list[dict[str, Any]]
    answer_key: str
    question: str
    metadata: dict[str, Any]


def build_haystack(
    *,
    structure: str,
    competition: str,
    similarity: str,
    target_tokens: int,
    depth: float,
    seed: int,
    filler_sentences: Sequence[str] | None = None,
    n_distractors: int = 4,
    diffuse_density: float = 0.3,
) -> Haystack:
    """Build a haystack. See module docstring + synthesis §3.6 for the axes."""
    if structure == "clean_essay":
        return _build_essay(
            competition=competition,
            similarity=similarity,
            target_tokens=target_tokens,
            depth=depth,
            seed=seed,
            filler_sentences=filler_sentences,
            n_distractors=n_distractors,
            diffuse_density=diffuse_density,
        )
    if structure == "tool_call_stream":
        return _build_tool_stream(
            competition=competition,
            similarity=similarity,
            target_tokens=target_tokens,
            depth=depth,
            seed=seed,
            n_distractors=n_distractors,
            diffuse_density=diffuse_density,
        )
    if structure == "research_doc_stream":
        raise NotImplementedError("structure='research_doc_stream' lands in backlog item 5")
    raise ValueError(f"unknown structure: {structure!r}")


def _build_essay(
    *,
    competition: str,
    similarity: str,
    target_tokens: int,
    depth: float,
    seed: int,
    filler_sentences: Sequence[str] | None,
    n_distractors: int,
    diffuse_density: float,
) -> Haystack:
    if not filler_sentences:
        raise ValueError("clean_essay requires non-empty filler_sentences")
    if competition not in ("neutral", "localized", "diffuse"):
        raise ValueError(f"unknown competition: {competition!r}")
    rng = random.Random(seed)
    question = _question_for(similarity)
    filler = list(filler_sentences)

    # Assemble filler units (sentences) up to the target estimate. In `diffuse`,
    # a `diffuse_density` fraction of units are vault-domain competitors.
    units: list[str] = []
    n_competitors = 0
    while _est_tokens(" ".join(units)) < target_tokens:
        if competition == "diffuse" and rng.random() < diffuse_density:
            units.append(_gen_competitor(rng))
            n_competitors += 1
        else:
            units.append(rng.choice(filler))

    # In `localized`, insert a few discrete distractors into neutral bulk.
    if competition == "localized":
        for distractor in rng.sample(DISTRACTORS, k=min(n_distractors, len(DISTRACTORS))):
            units.insert(rng.randint(0, len(units)), distractor)
            n_competitors += 1

    # Insert the needle at the requested depth (fraction of units before it).
    needle_position = min(int(depth * len(units)), len(units))
    units.insert(needle_position, NEEDLE_TEXT)

    content = f"{' '.join(units)}\n\n{question}"
    return Haystack(
        messages=[{"role": "user", "content": content}],
        answer_key=ANSWER_KEY,
        question=question,
        metadata={
            "structure": "clean_essay",
            "competition": competition,
            "similarity": similarity,
            "target_tokens": target_tokens,
            "est_tokens": _est_tokens(content),
            "seed": seed,
            "depth": depth,
            "needle_position": needle_position,
            "n_units": len(units),
            "n_competitors": n_competitors,
        },
    )


# --- tool_call_stream materials (Phase 1.0 backlog item 3 — agentic structure) ---
_INITIAL_TASK = "Catalog the archive's holdings and note anything that needs attention."
# Est. tokens for the tool_use/tool_result JSON wrappers + query, per pair.
_PAIR_OVERHEAD_TOKENS = 20

# Neutral operations (tool, query, result template) across varied tool types —
# realistic *moderate* diversity: enough to avoid an artificial §1.7 template-rut,
# without pretending tool streams are as varied as prose (they aren't — real
# agents reuse a handful of tools, and that mild uniformity is a real property).
# Benign archive-ops domain (no security framing — see lessons §0.9).
_NEUTRAL_OPS = [
    ("search", "recent catalog updates", "Log: reading room {g} logged {n} visits, no issues."),
    ("read_file", "shelf_{g}.idx", "Index shelf_{g}.idx: {n} entries, {m} pending review."),
    ("grep", "duplicate", "grep: {n} matches for 'duplicate' in catalog {g}."),
    ("list_dir", "/scans/{g}", "Directory /scans/{g}: {n} files, {m} subfolders."),
    ("status", "scanner {g}", "Status: scanner {g} online; {n} pages digitized today."),
    ("roster", "shift {g}", "Roster: archive team {g} has {n} staff on duty."),
    ("status", "climate {g}", "Climate: stack {g} stable at {n}C, humidity {m}%."),
    ("index", "box {g}", "Index: storage box {g} holds {n} folders; condition good."),
    ("metrics", "queue {g}", "Metrics: digitization queue {g} depth {n}, {m} flagged."),
    ("inventory", "shelf {g}", "Inventory: shelf {g} holds {n} volumes, {m} for repair."),
    ("read_file", "loans_{g}.txt", "Loans {g}: {n} items out, next due in {m} days."),
    ("search", "reading room", "Reading room gate {g}: {n} check-ins today."),
    ("status", "lighting {g}", "Lighting in gallery {g}: {n} fixtures, all nominal."),
    ("grep", "missing", "grep: {n} matches for 'missing' in inventory {g}, resolved."),
    ("list_dir", "/backups/{g}", "Backups /backups/{g}: {n} snapshots, latest verified."),
    ("metrics", "throughput {g}", "Metrics: station {g} cataloged {n} items, {m}ms avg."),
    ("status", "case {g}", "Preservation: case {g} stable, {n} items, all intact."),
    ("roster", "docents {g}", "Docent rotation {g}: {n} on duty, {m} on standby."),
]
# Catalog-lookup ops (tool, query) — used for competitor + needle results.
_LOOKUP_OPS = [
    ("search", "manuscript catalog numbers"),
    ("lookup_catalog", "catalog index"),
    ("query_index", "reference numbers by manuscript"),
    ("search", "finding aids"),
]


def _gen_neutral_op(rng: random.Random) -> tuple[str, str, str]:
    """A task-unrelated (tool, query, result) — benign filler, not a competitor."""
    name, query, result = rng.choice(_NEUTRAL_OPS)
    g = rng.choice("ABCDEF")
    n = rng.randint(1, 99)
    m = rng.randint(1, 20)
    return name, query.format(g=g), result.format(g=g, n=n, m=m)


def _lookup_op(rng: random.Random) -> tuple[str, str]:
    """A (tool, query) for a catalog lookup — wraps competitor/needle results."""
    return rng.choice(_LOOKUP_OPS)


def _tool_pair(
    idx: int, name: str, query: str, result_text: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One (assistant tool_use, user tool_result) pair with matching id."""
    tid = f"toolu_{idx}"
    assistant_msg = {
        "role": "assistant",
        "content": [{"type": "tool_use", "id": tid, "name": name, "input": {"query": query}}],
    }
    user_msg = {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": tid, "content": result_text}],
    }
    return assistant_msg, user_msg


def _build_tool_stream(
    *,
    competition: str,
    similarity: str,
    target_tokens: int,
    depth: float,
    seed: int,
    n_distractors: int,
    diffuse_density: float,
) -> Haystack:
    if competition not in ("neutral", "localized", "diffuse"):
        raise ValueError(f"unknown competition: {competition!r}")
    rng = random.Random(seed)
    question = _question_for(similarity)

    # Assemble (tool, query, result) units up to the target estimate. In
    # `diffuse`, a `diffuse_density` fraction of results are vault-domain
    # competitors (incl. same-vault distractors via _gen_competitor).
    units: list[tuple[str, str, str]] = []
    n_competitors = 0
    est = _est_tokens(_INITIAL_TASK) + _est_tokens(question)
    while est < target_tokens:
        if competition == "diffuse" and rng.random() < diffuse_density:
            name, query = _lookup_op(rng)
            text = _gen_competitor(rng)
            n_competitors += 1
        else:
            name, query, text = _gen_neutral_op(rng)
        units.append((name, query, text))
        est += _est_tokens(text) + _PAIR_OVERHEAD_TOKENS

    if competition == "localized":
        for distractor in rng.sample(DISTRACTORS, k=min(n_distractors, len(DISTRACTORS))):
            name, query = _lookup_op(rng)
            units.insert(rng.randint(0, len(units)), (name, query, distractor))
            n_competitors += 1

    # Insert the needle as a tool_result at the requested depth.
    n_name, n_query = _lookup_op(rng)
    needle_position = min(int(depth * len(units)), len(units))
    units.insert(needle_position, (n_name, n_query, NEEDLE_TEXT))

    # Materialize as a valid agentic history: task, then tool_use/tool_result
    # pairs (pairing respected — count_tokens / the API reject unmatched
    # tool_use; see lessons §0.4), then the question.
    messages: list[dict[str, Any]] = [{"role": "user", "content": _INITIAL_TASK}]
    for i, (name, query, text) in enumerate(units):
        assistant_msg, user_msg = _tool_pair(i, name, query, text)
        messages.append(assistant_msg)
        messages.append(user_msg)
    messages.append({"role": "user", "content": question})

    est_tokens = (
        _est_tokens(_INITIAL_TASK)
        + _est_tokens(question)
        + sum(_est_tokens(t) + _PAIR_OVERHEAD_TOKENS for _, _, t in units)
    )
    return Haystack(
        messages=messages,
        answer_key=ANSWER_KEY,
        question=question,
        metadata={
            "structure": "tool_call_stream",
            "competition": competition,
            "similarity": similarity,
            "target_tokens": target_tokens,
            "est_tokens": est_tokens,
            "seed": seed,
            "depth": depth,
            "needle_position": needle_position,
            "n_pairs": len(units),
            "n_competitors": n_competitors,
        },
    )
