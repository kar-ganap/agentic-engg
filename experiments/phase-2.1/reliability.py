"""Reliability report SURFACE (Phase 2.1, Module 6 L185) — silent-vs-loud failure over a run corpus.

Loads a `TaskSummary` corpus (the scorer's `summaries.jsonl`) and prints the reliability report: the
silent-vs-loud failure split + the waste / recovery / reference-health sensors. The Module-2
reliability primitives read as SENSORS instead of guards — "agents fail silently far more than they
crash" made measurable.

    uv run python experiments/phase-2.1/reliability.py                       # default corpus
    uv run python experiments/phase-2.1/reliability.py runs/phase-1.1/binding/summaries.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from stance.eval.reliability import reliability
from stance.tooluse.score import TaskSummary

DEFAULT = Path("runs/phase-1.1/summaries.jsonl")


def _load(path: Path) -> list[TaskSummary]:
    out: list[TaskSummary] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        d["confusion_pairs"] = [tuple(p) for p in d.get("confusion_pairs", [])]
        out.append(TaskSummary(**d))
    return out


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    rep = reliability(_load(path))
    print(f"reliability — {path} ({rep.n} runs)\n")
    print(f"  success rate:      {rep.success_rate:.2f}")
    print(f"  terminal status:   {rep.terminal_status}")
    print(f"  silent failures:   {rep.silent_failures}  (wrong={rep.silent_wrong} "
          f"exhaustion={rep.silent_exhaustion} loop={rep.silent_loop})")
    print(f"  loud failures:     {rep.loud}  (crash/timeout — the easy ones)")
    print(f"  SILENT SHARE:      {_fmt(rep.silent_failure_share)}  "
          "(of failures, fraction that failed quietly)")
    print(f"  critical outcomes: {rep.critical_outcomes}")
    rc = f"mean {rep.redundant_calls_mean:.2f}, max {rep.redundant_calls_max}"
    print(f"  redundant calls:   {rc}")
    print(f"  loop-guard fire:   {rep.loop_guard_fire_rate:.2f}")
    print(f"  error recovery:    {_fmt(rep.error_recovery_rate)}  (erred, still succeeded)")
    print(f"  handle-use (ref):  {_fmt(rep.handle_use_rate)}  (offered a ref, then used it)")


if __name__ == "__main__":
    main()
