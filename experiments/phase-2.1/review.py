"""Position-staleness scheduler SURFACE (Phase 2.1, throughline Property 3 — the must-ship surface).

Reads the live evidence graph, ranks positions by review-worthiness (`stance.review`), and surfaces
the stalest N for review — with a transparent per-axis breakdown + the retraction-trigger checklist
for the human to judge against recent evidence. This is the in-the-moment re-evaluation affordance:
run it before making a decision, and it tells you which position most needs a fresh look.

    uv run python experiments/phase-2.1/review.py                       # top stale positions today
    uv run python experiments/phase-2.1/review.py --n 12 --as-of 2026-09-01
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from stance.graph.store import GraphStore
from stance.review import rank

GRAPH_DIR = Path("data/graph")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--as-of", default="", help="ISO date to evaluate as-of (default: today)")
    args = ap.parse_args()
    today = date.fromisoformat(args.as_of) if args.as_of else date.today()

    scores = rank(GraphStore(GRAPH_DIR).load(), today)
    print(f"position-staleness — {len(scores)} positions, as of {today} "
          f"(most review-worthy first)\n")
    print(f"{'stale':>6}  {'position':<32} {'status':<10} {'age':>4} {'over':>5} "
          f"{'flux':>4} {'prb':>3} {'vol':>4}")
    print("  " + "-" * 78)
    for s in scores[:args.n]:
        print(f"{s.staleness:>6.2f}  {s.position_id:<32} {s.status:<10} {s.age_days:>4} "
              f"{s.overdue:>5.2f} {s.flux:>4} {s.open_probes:>3} {s.volatility:>4.2f}")

    top = scores[0] if scores else None
    if top is not None and top.retraction_flags:
        print(f"\nretraction checklist for the stalest — {top.position_id} "
              f"(judge each against evidence since {top.age_days}d ago):")
        for cond in top.retraction_flags:
            print(f"  [ ] {cond}")
    print("\n(overdue = age / review-interval[status]: hypothesis 30d, candidate 90d, active 180d; "
          "staleness = overdue × (1 + 0.5·flux + 0.5·probes + 0.3·vol))")


if __name__ == "__main__":
    main()
