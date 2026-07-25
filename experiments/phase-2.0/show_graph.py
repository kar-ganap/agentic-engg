"""Read-only inspector for the evidence graph (Phase 2.0 review aid; a proto of the
Property-2 query surface). No args -> summary table of all positions; a position id ->
that position's full subgraph (stance / legs / retraction / evidence+warrants / probes / edges).

    uv run python experiments/phase-2.0/show_graph.py            # summary table
    uv run python experiments/phase-2.0/show_graph.py 3.8        # one position, resolved
"""

from __future__ import annotations

import argparse
from pathlib import Path

from stance.graph.store import Graph, GraphStore

GRAPH_DIR = Path("data/graph")


def summary(g: Graph) -> None:
    print(f"{'id':<11} {'conf':>4} {'status':<10} {'#ev':>3} {'#probe':>6}  edges")
    for pid in sorted(g.positions):
        p = g.positions[pid]
        print(f"{pid:<11} {p.confidence:>4} {p.status:<10} "
              f"{len(g.evidence_for(pid)):>3} {len(g.probes_for(pid)):>6}  {g.edges_of(pid)}")
    print(f"\nclaims={len(g.claims)}  evidence={len(g.evidence)}  "
          f"supports={len(g.supports)}  probes={len(g.probes)}")


def detail(g: Graph, pid: str) -> None:
    p = g.position(pid)
    if p is None:
        print(f"no position {pid!r}; known: {sorted(g.positions)}")
        return
    print(f"POSITION {p.id}  \"{p.title}\"")
    print(f"  status={p.status}  confidence={p.confidence}  "
          f"(trajectory {[v.confidence for v in g.position_history(pid)]})")
    ref = f"§{p.synthesis_ref}" if p.synthesis_ref else "(no synthesis section)"
    print(f"  registered {p.registered}  updated {p.updated}  synthesis_ref {ref}")
    print(f"  stance: {p.stance}")
    if p.legs:
        print("  legs:")
        for leg in p.legs:
            print(f"    - {leg.label} = {leg.confidence}  ({leg.note})")
    print("  preconditions:")
    for pc in p.preconditions:
        print(f"    - {pc}")
    print("  retraction:")
    for r in p.retraction:
        print(f"    - [{r.direction} {r.delta}] ({','.join(r.tags)}) {r.condition}")
    print("  support (evidence -- warrant):")
    for s in g.supports_for(pid):
        ev = g.evidence.get(s.evidence_id)
        print(f"    [{s.polarity}] [{ev.type if ev else '?'}] {s.evidence_id}: {s.warrant}")
    print("  decisive probes:")
    for pr in g.probes_for(pid):
        print(f"    {pr.id} [expected={pr.expected}|{pr.status}|{pr.why_uncollected}]")
        print(f"        {pr.description}")
    print(f"  edges: {p.edges}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("position_id", nargs="?", help="e.g. 1.8, 3.8, carry-swap")
    args = ap.parse_args()
    g = GraphStore(GRAPH_DIR).load()
    if args.position_id:
        detail(g, args.position_id)
    else:
        summary(g)


if __name__ == "__main__":
    main()
