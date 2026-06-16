"""Tests for the evidence-graph store (Phase 2.0, schema v0).

Covers the load-bearing invariants: frozen round-trip through JSONL, the append-only
Position latest-wins + derived trajectory, the reified Support edge (warrant + polarity),
sub-confidence legs, the DecisiveProbe value-of-information node, and edge/query helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stance.graph.models import (
    DecisiveProbe,
    Evidence,
    Leg,
    Position,
    Retraction,
    Support,
)
from stance.graph.store import GraphStore


def _pos(pid: str, conf: int, **kw: Any) -> Position:
    return Position(
        id=pid, title=f"pos {pid}", stance="...", confidence=conf,
        status=kw.pop("status", "candidate"), registered="2026-06-15",
        updated="2026-06-15", **kw,
    )


def test_position_round_trip(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    p = _pos(
        "1.1", 80,
        legs=(Leg("cache", 90, "measured"), Leg("coherence", 65, "lit-only")),
        preconditions=("KV-cache", ">=3 turns"),
        retraction=(Retraction("down", 25, "no cache cost", ("measurement",)),),
        edges=(("tension_with", "2.1"),), synthesis_ref="1.1",
    )
    store.add(p)
    assert store.load().position("1.1") == p  # exact frozen-dataclass round-trip


def test_position_latest_wins_and_history(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    for conf in (70, 78, 80):
        store.add(_pos("1.8", conf))
    g = store.load()
    current = g.position("1.8")
    assert current is not None and current.confidence == 80  # latest wins
    assert [p.confidence for p in g.position_history("1.8")] == [70, 78, 80]  # full trajectory


def test_evidence_append_only(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    store.add(Evidence("ev-ruler", "literature", "RULER", "...", "corroborating"))
    store.add(Evidence("ev-exp", "experimental", "results.md", "...", "direct"))
    assert (tmp_path / "evidence.jsonl").read_text().count("\n") == 2  # both persisted
    assert set(store.load().evidence) == {"ev-ruler", "ev-exp"}


def test_support_warrant_and_polarity(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    store.add(Evidence("ev-x", "experimental", "results.md", "...", "contradicting"))
    store.add(Support("3.8", "ev-x", warrant="opposite scaling in the parametric regime",
                      polarity="contradicts"))
    g = store.load()
    assert [e.id for e in g.evidence_for("3.8", polarity="contradicts")] == ["ev-x"]
    assert g.supports_for("3.8")[0].warrant.startswith("opposite scaling")


def test_legs_preserved(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    store.add(_pos("1.1", 80, legs=(Leg("cache", 90), Leg("coherence", 65))))
    p = store.load().position("1.1")
    assert p is not None
    assert {leg.label: leg.confidence for leg in p.legs} == {"cache": 90, "coherence": 65}
    assert p.confidence == 80  # headline distinct from the legs


def test_decisiveprobe_would_move(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    store.add(DecisiveProbe("probe-claude-cache", "Claude cache anchor",
                            would_move=("3.3", "1.1"), expected="toggle",
                            why_uncollected="cost", status="deferred"))
    assert [pr.id for pr in store.load().probes_for("1.1")] == ["probe-claude-cache"]


def test_edges_query(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    store.add(_pos("3.3", 78, edges=(("qualifies", "1.1"), ("subsumes", "9.9"))))
    assert store.load().edges_of("3.3", kind="qualifies") == [("qualifies", "1.1")]


def test_positions_where(tmp_path: Path) -> None:
    store = GraphStore(tmp_path)
    store.add(_pos("1.1", 80, status="candidate"))
    store.add(_pos("3.8", 45, status="hypothesis"))
    g = store.load()
    assert [p.id for p in g.positions_where(min_confidence=70)] == ["1.1"]
    assert [p.id for p in g.positions_where(status="hypothesis")] == ["3.8"]
