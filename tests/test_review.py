"""Tests for the position-staleness scheduler (`stance.review`) — the Property-3 surface logic.

Staleness = overdue(status-interval) × (1 + w_flux·flux + w_probe·probes + w_vol·volatility);
retraction triggers are surfaced as a human flag. `today` is injected so tests are deterministic.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from stance.graph.models import DecisiveProbe, Evidence, Position, Retraction, Support
from stance.graph.store import Graph, GraphStore
from stance.review import rank, staleness

TODAY = date(2026, 7, 28)


def _pos(pid: str, *, status: str = "candidate", conf: int = 70, updated: str = "2026-06-01",
         retraction: tuple[Retraction, ...] = ()) -> Position:
    return Position(id=pid, title=pid, stance="...", confidence=conf, status=status,
                    registered="2026-01-01", updated=updated, retraction=retraction)


def _load(tmp_path: Path, *records: object) -> Graph:
    store = GraphStore(tmp_path)
    for r in records:
        store.add(r)  # type: ignore[arg-type]
    return store.load()


def test_staleness_grows_with_age(tmp_path: Path) -> None:
    g = _load(tmp_path, _pos("old", updated="2026-01-01"), _pos("fresh", updated="2026-07-25"))
    scores = {s.position_id: s.staleness for s in rank(g, TODAY)}
    assert scores["old"] > scores["fresh"]
    assert rank(g, TODAY)[0].position_id == "old"  # most review-worthy first


def test_status_interval_normalizes(tmp_path: Path) -> None:
    # same age, different status → the shorter-interval status is more overdue
    g = _load(tmp_path, _pos("cand", status="candidate", updated="2026-05-01"),
              _pos("act", status="active", updated="2026-05-01"))
    by = {s.position_id: s for s in rank(g, TODAY)}
    assert by["cand"].overdue > by["act"].overdue          # 88d/90 vs 88d/180
    assert by["cand"].staleness > by["act"].staleness       # → candidate is staler


def test_demoted_never_resurfaces(tmp_path: Path) -> None:
    g = _load(tmp_path, _pos("dead", status="demoted", updated="2024-01-01"))  # ancient
    assert staleness(g.positions["dead"], g, TODAY).staleness == 0.0


def test_open_probes_amplify_multiplicatively(tmp_path: Path) -> None:
    g = _load(
        tmp_path,
        _pos("plain", updated="2026-05-01"),
        _pos("probed", updated="2026-05-01"),
        DecisiveProbe(id="dp", description="a crux", would_move=("probed",), expected="toggle",
                      why_uncollected="cost", status="deferred"),
    )
    by = {s.position_id: s for s in rank(g, TODAY)}
    assert by["probed"].open_probes == 1 and by["plain"].open_probes == 0
    # multiplicative: same overdue, probed × (1 + 0.5) > plain × 1
    assert by["probed"].staleness > by["plain"].staleness


def test_flux_undated_is_baseline_dated_after_update_counts(tmp_path: Path) -> None:
    g = _load(
        tmp_path,
        _pos("hasflux", updated="2026-06-01"),
        _pos("noflux", updated="2026-06-01"),
        Evidence("ev-new", "experimental", "r.md", "...", "direct", date="2026-07-01"),
        Evidence("ev-old", "experimental", "r.md", "...", "direct"),  # undated
        Support("hasflux", "ev-new", warrant="w", polarity="supports", date="2026-07-01"),  # new
        Support("noflux", "ev-old", warrant="w", polarity="supports"),  # undated → baseline
    )
    by = {s.position_id: s for s in rank(g, TODAY)}
    assert by["hasflux"].flux == 1 and by["noflux"].flux == 0
    assert by["hasflux"].staleness > by["noflux"].staleness


def test_retraction_triggers_surfaced_as_flags(tmp_path: Path) -> None:
    p = _pos("p", retraction=(Retraction("down", 20, "a 3rd provider holds flat", ("x",)),))
    g = _load(tmp_path, p)
    assert staleness(g.positions["p"], g, TODAY).retraction_flags == ("a 3rd provider holds flat",)
