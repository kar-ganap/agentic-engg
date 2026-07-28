"""Reliability report (Phase 2.1, Module 6 L185) — the Module-2 reliability primitives as SENSORS.

"Agents fail silently far more than they crash." Module 2 built explicit terminal states, the
sliding-window loop guard, and return-a-reference as GUARDS that *prevent* silent failure; here the
same signals become SENSORS that *measure* it. Pure aggregation over the `TaskSummary` corpus the
scorer already emits — no new runs, no LLM, no cost.

The headline is the **silent-vs-loud** split: a crash (`terminal_status` crash/timeout) is easy to
see; a run that finished clean but wrong, exhausted its budget, or looped is not. Silent-failure
taxonomy (over the runs that did NOT succeed):
    silent-wrong       terminal_status == "complete"   (finished clean, task not achieved)
    silent-exhaustion  terminal_status == "max_turns"  (ran out of turns without terminating)
    silent-loop        terminal_status == "loop_guard" (the guard had to break a stuck loop)
    loud               terminal_status in {crash, timeout}
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from stance.tooluse.score import TaskSummary

_LOUD = frozenset({"crash", "timeout"})


@dataclass(frozen=True)
class ReliabilityReport:
    n: int
    success_rate: float
    terminal_status: dict[str, int]  # full distribution — nothing hides behind the buckets
    # failure taxonomy (over the FAILURES only):
    silent_wrong: int
    silent_exhaustion: int
    silent_loop: int
    loud: int
    # wrong-value breakdown (tool-level silent-wrong): correct-use|re-fetch|mis-bind|fabricate|error
    critical_outcomes: dict[str, int]
    # waste / recovery / reference-health sensors (across ALL runs):
    redundant_calls_mean: float
    redundant_calls_max: int
    loop_guard_fire_rate: float
    error_recovery_rate: float | None  # of runs that erred, the fraction that still succeeded
    handle_use_rate: float | None      # of runs offered a reference, the fraction that used it

    @property
    def silent_failures(self) -> int:
        return self.silent_wrong + self.silent_exhaustion + self.silent_loop

    @property
    def silent_failure_share(self) -> float | None:
        """Of the failures, the fraction that failed *quietly* (None if nothing failed)."""
        failed = self.silent_failures + self.loud
        return self.silent_failures / failed if failed else None


def _rate(num: int, den: int) -> float | None:
    return num / den if den else None


def reliability(summaries: Sequence[TaskSummary]) -> ReliabilityReport:
    if not summaries:
        raise ValueError("reliability() needs at least one run")
    n = len(summaries)
    fails = [s for s in summaries if not s.success]

    term: dict[str, int] = {}
    crit: dict[str, int] = {}
    for s in summaries:
        term[s.terminal_status] = term.get(s.terminal_status, 0) + 1
        key = s.critical_outcome or "n/a"
        crit[key] = crit.get(key, 0) + 1

    redundant = [s.redundant_call_count for s in summaries]
    erred = [s for s in summaries if s.first_error_depth is not None]
    offered = [s for s in summaries if s.handle_available is True]

    return ReliabilityReport(
        n=n,
        success_rate=sum(s.success for s in summaries) / n,
        terminal_status=term,
        silent_wrong=sum(1 for s in fails if s.terminal_status == "complete"),
        silent_exhaustion=sum(1 for s in fails if s.terminal_status == "max_turns"),
        silent_loop=sum(1 for s in fails if s.terminal_status == "loop_guard"),
        loud=sum(1 for s in fails if s.terminal_status in _LOUD),
        critical_outcomes=crit,
        redundant_calls_mean=sum(redundant) / n,
        redundant_calls_max=max(redundant, default=0),
        loop_guard_fire_rate=term.get("loop_guard", 0) / n,
        error_recovery_rate=_rate(sum(s.success for s in erred), len(erred)),
        handle_use_rate=_rate(sum(1 for s in offered if s.handle_used), len(offered)),
    )
