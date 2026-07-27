"""Summarize a Thread-B results JSONL: per (arm, n_distractors) across seeds -> mean grade, spread,
the §1.8 sidestep metric (n_reads), cost (output tokens), latency. Flags unparsed rows.

    uv run python experiments/phase-2.0/analyze_reasoning.py            # latest results file
    uv run python experiments/phase-2.0/analyze_reasoning.py <path.jsonl>
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

RESULTS = Path("experiments/phase-2.0/results")


def _mean(xs: list[float]) -> float:
    return statistics.mean(xs) if xs else 0.0


def _sd(xs: list[float]) -> float:
    return statistics.pstdev(xs) if len(xs) > 1 else 0.0


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(RESULTS.glob("reasoning-*.jsonl"))[-1]
    rows = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
    print(f"{path.name}  ({len(rows)} rows)")

    groups: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["arm"], r["n_distractors"], r["pool"])].append(r)

    hdr = (f"{'arm':<13}{'nD':>3}{'n':>3}{'grade':>10}{'reads':>7}"
           f"{'calls':>6}{'out_tok':>8}{'lat_s':>7}{'bad':>4}")
    print(hdr)
    print("-" * len(hdr))
    for (arm, nd, _pool), rs in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        totals = [r["grade_total"] for r in rs]
        bad = sum(1 for r in rs if not r["grade_parsed_ok"] or r["confidence"] < 0)
        print(f"{arm:<13}{nd:>3}{len(rs):>3}"
              f"{_mean(totals):>6.1f}±{_sd(totals):<3.1f}"
              f"{_mean([r['n_reads'] for r in rs]):>7.1f}"
              f"{_mean([r['n_calls'] for r in rs]):>6.1f}"
              f"{_mean([r['arm_output_tokens'] for r in rs]):>8.0f}"
              f"{_mean([r['latency_s'] for r in rs]):>7.1f}"
              f"{bad:>4}")

    # per-criterion means by arm (collapsed over sizes/seeds), to see WHERE arms differ
    crit = ("stance_correctness", "calibration", "retraction", "evidence_use", "epistemic_humility")
    print("\nper-criterion mean (0-4), by arm:")
    print(f"{'arm':<13}" + "".join(f"{c[:5]:>7}" for c in crit))
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    for arm, rs in sorted(by_arm.items()):
        print(f"{arm:<13}" + "".join(f"{_mean([r[f'grade_{c}'] for r in rs]):>7.1f}" for c in crit))


if __name__ == "__main__":
    main()
