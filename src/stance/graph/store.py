"""Append-only JSONL persistence + Python-side queries for the evidence graph (v0).

One file per record type under `<root>/`. `Claim`/`Evidence`/`Support`/`DecisiveProbe`
are pure append-only. `Position` is append-only too, but **latest-wins**: re-saving a
position appends a new line; `Graph.position(id)` returns the last, `position_history(id)`
returns all in order — so the confidence trajectory is free. SQLite + a real query
surface are deferred to Phase 2.2 (Property 2); for v0 the queries are plain Python.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, assert_never

from stance.graph.models import Claim, DecisiveProbe, Evidence, Position, Record, Support

CLAIMS = "claims.jsonl"
EVIDENCE = "evidence.jsonl"
SUPPORT = "support.jsonl"
POSITIONS = "positions.jsonl"
PROBES = "probes.jsonl"


def _filename(record: Record) -> str:
    match record:
        case Claim():
            return CLAIMS
        case Evidence():
            return EVIDENCE
        case Support():
            return SUPPORT
        case Position():
            return POSITIONS
        case DecisiveProbe():
            return PROBES
        case _:  # pragma: no cover - exhaustiveness guard over the Record union
            assert_never(record)


@dataclass
class Graph:
    """In-memory snapshot. `positions` is latest-wins current; `position_history` exposes
    the full append-only trajectory."""

    claims: dict[str, Claim] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    supports: tuple[Support, ...] = ()
    probes: dict[str, DecisiveProbe] = field(default_factory=dict)
    positions: dict[str, Position] = field(default_factory=dict)
    position_log: tuple[Position, ...] = ()  # full append order (the trajectory)

    def position(self, pid: str) -> Position | None:
        return self.positions.get(pid)

    def position_history(self, pid: str) -> list[Position]:
        return [p for p in self.position_log if p.id == pid]

    def positions_where(self, *, min_confidence: int = 0,
                        status: str | None = None) -> list[Position]:
        out = [p for p in self.positions.values()
               if p.confidence >= min_confidence and (status is None or p.status == status)]
        return sorted(out, key=lambda p: p.id)

    def supports_for(self, pid: str, *, polarity: str | None = None) -> list[Support]:
        return [s for s in self.supports
                if s.position_id == pid and (polarity is None or s.polarity == polarity)]

    def evidence_for(self, pid: str, *, polarity: str | None = None) -> list[Evidence]:
        return [self.evidence[s.evidence_id]
                for s in self.supports_for(pid, polarity=polarity)
                if s.evidence_id in self.evidence]

    def probes_for(self, pid: str) -> list[DecisiveProbe]:
        return [pr for pr in self.probes.values() if pid in pr.would_move]

    def edges_of(self, pid: str, *, kind: str | None = None) -> list[tuple[str, str]]:
        p = self.positions.get(pid)
        if p is None:
            return []
        return [e for e in p.edges if kind is None or e[0] == kind]


class GraphStore:
    """Append-only JSONL store over a directory (one file per record type)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def add(self, record: Record) -> None:
        with (self.root / _filename(record)).open("a", encoding="utf-8") as f:
            f.write(record.to_jsonl() + "\n")

    def _lines(self, filename: str) -> list[dict[str, Any]]:
        path = self.root / filename
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def load(self) -> Graph:
        g = Graph()
        for d in self._lines(CLAIMS):
            c = Claim.from_dict(d)
            g.claims[c.id] = c
        for d in self._lines(EVIDENCE):
            e = Evidence.from_dict(d)
            g.evidence[e.id] = e
        for d in self._lines(PROBES):
            pr = DecisiveProbe.from_dict(d)
            g.probes[pr.id] = pr
        g.supports = tuple(Support.from_dict(d) for d in self._lines(SUPPORT))
        log = [Position.from_dict(d) for d in self._lines(POSITIONS)]
        g.position_log = tuple(log)
        for p in log:
            g.positions[p.id] = p  # latest-wins
        return g
