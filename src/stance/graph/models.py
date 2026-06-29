"""Evidence-graph data model (v0) — `Claim` / `Evidence` / `Position`, the reified
`Support` edge (Toulmin warrant), the `DecisiveProbe` value-of-information node, and
the `Retraction` / `Leg` sub-records.

Frozen dataclasses serialized to append-only JSONL by `stance.graph.store`. Schema
locked 2026-06-15 (`docs/phases/phase-2.0-plan.md`): qualifier→`confidence`,
rebuttal→`preconditions`, plus the Popper `retraction` overlay Toulmin lacks. `Position`
is stored append-only with latest-wins, so its confidence trajectory is the ordered set
of records sharing an `id` — no separate history field. Deferred to v1: mechanism-data
(the evaluator-output layer), and the `Tension` (§2) / `Framing` (§5) node types.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Claim:
    """An atomic proposition, from a source or an experiment. Append-only."""

    id: str
    text: str
    kind: str  # proposition | finding
    evidence_ids: tuple[str, ...] = ()

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Claim:
        return cls(id=d["id"], text=d["text"], kind=d["kind"],
                   evidence_ids=tuple(d.get("evidence_ids", ())))


@dataclass(frozen=True)
class Evidence:
    """What backs or contradicts a claim (literature / experiment / …). Append-only."""

    id: str
    type: str      # literature | mechanistic | experimental | analogous
    source: str    # provenance: citation / file path / experiment id
    summary: str
    strength: str  # direct | corroborating | lower_bound | contradicting
    claim_ids: tuple[str, ...] = ()

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Evidence:
        return cls(id=d["id"], type=d["type"], source=d["source"], summary=d["summary"],
                   strength=d["strength"], claim_ids=tuple(d.get("claim_ids", ())))


@dataclass(frozen=True)
class Support:
    """Reified support edge: which evidence licenses which position, and WHY — the
    Toulmin `warrant` (usually the mechanism). Append-only."""

    position_id: str
    evidence_id: str
    warrant: str
    polarity: str  # supports | contradicts | inconclusive (related but confounded/unresolved)

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Support:
        return cls(position_id=d["position_id"], evidence_id=d["evidence_id"],
                   warrant=d["warrant"], polarity=d["polarity"])


@dataclass(frozen=True)
class Retraction:
    """A forward falsification trigger: what evidence would move confidence, by how much."""

    direction: str  # down | up
    delta: int
    condition: str
    tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Retraction:
        return cls(direction=d["direction"], delta=int(d["delta"]),
                   condition=d["condition"], tags=tuple(d.get("tags", ())))


@dataclass(frozen=True)
class Leg:
    """A sub-confidence split of a position (e.g. §1.1 cache~90 / coherence~65)."""

    label: str
    confidence: int
    note: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Leg:
        return cls(label=d["label"], confidence=int(d["confidence"]), note=d.get("note", ""))


@dataclass(frozen=True)
class Position:
    """A stance on a contested debate. Stored append-only, latest-wins → the confidence
    trajectory is the ordered set of records sharing an `id` (no separate history field)."""

    id: str
    title: str
    stance: str
    confidence: int  # headline qualifier (author-set; capped by the weakest leg)
    status: str      # hypothesis | candidate | active | demoted
    registered: str
    updated: str
    legs: tuple[Leg, ...] = ()
    preconditions: tuple[str, ...] = ()
    retraction: tuple[Retraction, ...] = ()
    edges: tuple[tuple[str, str], ...] = ()  # (kind, target): tension_with|qualifies|subsumes
    demoted_reason: str | None = None
    synthesis_ref: str | None = None

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Position:
        return cls(
            id=d["id"], title=d["title"], stance=d["stance"],
            confidence=int(d["confidence"]), status=d["status"],
            registered=d["registered"], updated=d["updated"],
            legs=tuple(Leg.from_dict(x) for x in d.get("legs", ())),
            preconditions=tuple(d.get("preconditions", ())),
            retraction=tuple(Retraction.from_dict(x) for x in d.get("retraction", ())),
            edges=tuple((e[0], e[1]) for e in d.get("edges", ())),
            demoted_reason=d.get("demoted_reason"),
            synthesis_ref=d.get("synthesis_ref"),
        )


@dataclass(frozen=True)
class DecisiveProbe:
    """The crux / value-of-information node: the highest-VoI *uncollected* datum that
    would most likely toggle the position(s) it bears on, and why it's uncollected."""

    id: str
    description: str
    would_move: tuple[str, ...]  # position ids
    expected: str                # up | down | toggle
    why_uncollected: str         # cost | capability | access | methodology-gap
    status: str                  # blocked | deferred | planned
    note: str = ""

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DecisiveProbe:
        return cls(id=d["id"], description=d["description"],
                   would_move=tuple(d.get("would_move", ())), expected=d["expected"],
                   why_uncollected=d["why_uncollected"], status=d["status"],
                   note=d.get("note", ""))


# Top-level record types (Retraction/Leg are nested-only). Used by the store's dispatch.
Record = Claim | Evidence | Support | Position | DecisiveProbe
