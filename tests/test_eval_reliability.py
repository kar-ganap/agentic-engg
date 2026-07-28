"""Tests for the reliability report (`stance.eval.reliability`, Phase 2.1, Module 6 L185).

The load-bearing metric is the **silent-vs-loud** split: a run that finished clean but wrong (or
exhausted turns, or looped) is a *silent* failure; a crash/timeout is *loud*. The real corpus is
all-clean, so these synthetic fixtures are what prove the taxonomy discriminates.
"""

from __future__ import annotations

from typing import Any

import pytest

from stance.eval.reliability import reliability
from stance.tooluse.score import TaskSummary


def _s(**kw: Any) -> TaskSummary:
    """A clean, successful run by default; override fields per test."""
    base: dict[str, Any] = dict(
        run_id="r", model="m", cell_id=None, task_id=None, seed=1, terminal_status="complete",
        intended_ivs={}, achieved_depth=1, peak_fill=100, fill_at_use=None, competitors_surfaced=0,
        success=True, assertions_passed=1, assertions_total=1, critical_outcome="correct-use",
        handle_available=None, handle_used=None, first_error_depth=None, cascade=False,
        redundant_call_count=0, recovered=False, wrong_tool_count=0, confusion_pairs=[],
        total_tokens=100, total_output_tokens=10, total_cache_read=0, total_cache_creation=0,
        total_cost_usd=0.0, sequential_round_trips=1,
    )
    base.update(kw)
    return TaskSummary(**base)


def test_all_clean_corpus_has_no_silent_failures() -> None:
    rep = reliability([_s(), _s(), _s()])
    assert rep.success_rate == 1.0
    assert rep.silent_failures == 0
    assert rep.silent_failure_share is None  # nothing failed → share undefined


def test_silent_wrong_is_finished_clean_but_failed() -> None:
    rep = reliability([_s(success=False, terminal_status="complete", critical_outcome="fabricate")])
    assert rep.silent_wrong == 1
    assert rep.loud == 0
    assert rep.silent_failure_share == 1.0  # a failure that looked fine is 100% silent


def test_exhaustion_and_loop_are_silent() -> None:
    rep = reliability([
        _s(success=False, terminal_status="max_turns"),
        _s(success=False, terminal_status="loop_guard"),
    ])
    assert rep.silent_exhaustion == 1
    assert rep.silent_loop == 1
    assert rep.loud == 0
    assert rep.loop_guard_fire_rate == 0.5


def test_silent_vs_loud_share_is_the_headline() -> None:
    # one silent-wrong + one loud crash → half the failures were silent
    rep = reliability([
        _s(success=False, terminal_status="complete"),
        _s(success=False, terminal_status="crash"),
    ])
    assert rep.silent_failures == 1 and rep.loud == 1
    assert rep.silent_failure_share == 0.5


def test_waste_recovery_and_reference_sensors() -> None:
    rep = reliability([
        _s(redundant_call_count=3, first_error_depth=2, success=True),   # erred then recovered
        _s(redundant_call_count=1, first_error_depth=1, success=False),  # erred, did not
        _s(handle_available=True, handle_used=True),
        _s(handle_available=True, handle_used=False),
    ])
    assert rep.redundant_calls_max == 3
    assert rep.redundant_calls_mean == 1.0            # (3+1+0+0)/4
    assert rep.error_recovery_rate == 0.5             # 1 of 2 erred runs succeeded
    assert rep.handle_use_rate == 0.5                 # 1 of 2 offered a handle used it


def test_critical_outcome_breakdown_surfaces_wrong_binds() -> None:
    rep = reliability([
        _s(critical_outcome="mis-bind", success=False),
        _s(critical_outcome="correct-use"),
    ])
    assert rep.critical_outcomes["mis-bind"] == 1
    assert rep.critical_outcomes["correct-use"] == 1


def test_empty_corpus_raises() -> None:
    with pytest.raises(ValueError, match="at least one run"):
        reliability([])
