"""Scorer (#5) — derives the per-task summary from raw events + run record + task
ground truth. Pure & re-pointable (§0.7): re-run over committed JSONL, no re-running
the experiment. The #4/#6 logic (critical_outcome, the competitor pool, the
write-boundary predicates) is load-bearing. Cell-level rates/curves are a SEPARATE
analysis layer (this is per-run scalars only).
See docs/phases/phase-1.1-plan.md § "Per-task summary" / "decision #5".
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from stance.instrumentation import pricing
from stance.tooluse.events import CallEvent, RunRecord
from stance.tooluse.tasks.base import DependencyEdge, TaskInstance, Write


@dataclass
class TaskSummary:
    run_id: str
    model: str | None
    cell_id: str | None
    task_id: str | None
    seed: int | None
    terminal_status: str
    intended_ivs: dict[str, Any]
    # achieved IVs (bin analysis by these, not intended)
    achieved_depth: int
    peak_fill: int
    fill_at_use: int | None
    competitors_surfaced: int
    # outcome
    success: bool
    assertions_passed: int
    assertions_total: int
    # #4 DV
    critical_outcome: str | None  # correct-use | re-fetch | mis-bind | fabricate | error
    handle_available: bool | None
    handle_used: bool | None
    # failure-shape
    first_error_depth: int | None
    cascade: bool
    redundant_call_count: int
    recovered: bool
    # selection tier
    wrong_tool_count: int | None
    confusion_pairs: list[tuple[str, str]]
    # cost / efficiency
    total_tokens: int
    total_output_tokens: int
    total_cache_read: int
    total_cache_creation: int
    total_cost_usd: float
    sequential_round_trips: int

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def _sig(name: str, args: dict[str, Any]) -> str:
    return name + "|" + json.dumps(args, sort_keys=True)


def _fill(usage: dict[str, int] | None) -> int:
    """Full context size = the three input usage fields (input is the *uncached*
    part under caching, so fill must add cache_read + cache_creation)."""
    u = usage or {}
    return (
        u.get("input_tokens", 0)
        + u.get("cache_read_input_tokens", 0)
        + u.get("cache_creation_input_tokens", 0)
    )


def _matches(e: CallEvent, w: Write) -> bool:
    """A successful call to `w.action` whose args ⊇ `w.args` (subset; ignore extra
    args like `body`/`response_format`; only count non-error calls)."""
    if e.tool_called != w.action or e.is_error:
        return False
    args = e.arguments or {}
    return all(args.get(k) == v for k, v in w.args.items())


def _critical(events: list[CallEvent], edge: DependencyEdge) -> tuple[str, bool, bool, int]:
    """Classify the #4 critical-step outcome. Returns
    (outcome, handle_available, handle_used, competitors_surfaced)."""
    calls = [e for e in events if e.is_tool_call]
    producers = [e for e in calls if e.tool_called == edge.producer]
    consumers = [e for e in calls if e.tool_called == edge.consumer]
    handle_available = any(edge.needle_id in (e.extracted_ids or []) for e in producers)
    # pool = ids the agent SAW, minus the needle, restricted to the needle's type (true competition)
    prefix = edge.needle_id.split("-")[0]
    pool = {
        cid
        for e in calls
        for cid in (e.extracted_ids or [])
        if cid != edge.needle_id and cid.split("-")[0] == prefix
    }
    if not consumers:
        return "error", handle_available, False, len(pool)
    consume = consumers[0]
    consumed = (consume.arguments or {}).get(edge.needle_arg)
    if consumed == edge.needle_id:
        re_fetched = sum(1 for e in producers if e.turn_index < consume.turn_index) >= 2
        return ("re-fetch" if re_fetched else "correct-use"), handle_available, True, len(pool)
    if consumed in pool:
        return "mis-bind", handle_available, False, len(pool)
    return "fabricate", handle_available, False, len(pool)


def _cascade(events: list[CallEvent], task: TaskInstance) -> bool:
    """Conservative value-flow: a WRONG consumed needle value that propagated into a
    later call's args. (Rarely fires for a single-write chain; meaningful for
    multi-action tasks.)"""
    edge = task.dependency_edge
    if edge is None:
        return False
    calls = [e for e in events if e.is_tool_call]
    consumers = [e for e in calls if e.tool_called == edge.consumer]
    if not consumers:
        return False
    consume = consumers[0]
    consumed = (consume.arguments or {}).get(edge.needle_arg)
    if consumed is None or consumed == edge.needle_id:
        return False
    return any(
        consumed in (e.arguments or {}).values()
        for e in calls
        if e.turn_index > consume.turn_index
    )


def score(events: list[CallEvent], run: RunRecord, task: TaskInstance) -> TaskSummary:
    calls = [e for e in events if e.is_tool_call]

    # write-boundary predicates
    passed = sum(
        1 for w in task.expected_writes if sum(1 for e in calls if _matches(e, w)) == w.cardinality
    )
    total = len(task.expected_writes)
    success = total > 0 and passed == total

    # #4 DV
    outcome: str | None = None
    handle_available: bool | None = None
    handle_used: bool | None = None
    competitors = 0
    fill_at_use: int | None = None
    edge = task.dependency_edge
    if edge is not None:
        outcome, handle_available, handle_used, competitors = _critical(events, edge)
        consumers = [e for e in calls if e.tool_called == edge.consumer]
        if consumers:
            fill_at_use = _fill(consumers[0].usage)

    # failure-shape
    error_turns = [e.turn_index for e in events if e.is_error]
    first_error_depth = min(error_turns) if error_turns else None
    sigs = [_sig(e.tool_called, e.arguments or {}) for e in calls if e.tool_called is not None]
    redundant = len(sigs) - len(set(sigs))
    had_setback = any(e.is_error for e in events) or any(e.guard_action == "warn" for e in events)
    recovered = had_setback and success

    # selection tier
    labelled = [(e.tool_expected, e.tool_called) for e in calls if e.tool_expected is not None]
    wrong_tool_count = sum(1 for exp, act in labelled if exp != act) if labelled else None
    confusion: list[tuple[str, str]] = []
    for exp, act in labelled:
        if exp is not None and act is not None and exp != act:
            confusion.append((exp, act))

    # cost / efficiency
    tot_in = sum((e.usage or {}).get("input_tokens", 0) for e in events)
    tot_out = sum((e.usage or {}).get("output_tokens", 0) for e in events)
    tot_cr = sum((e.usage or {}).get("cache_read_input_tokens", 0) for e in events)
    tot_cc = sum((e.usage or {}).get("cache_creation_input_tokens", 0) for e in events)
    try:
        cost_usd = pricing.cost(
            run.model or "",
            input_tokens=tot_in,
            output_tokens=tot_out,
            cache_read_input_tokens=tot_cr,
            cache_creation_input_tokens=tot_cc,
        )
    except KeyError:
        cost_usd = 0.0

    return TaskSummary(
        run_id=run.run_id, model=run.model, cell_id=run.cell_id, task_id=run.task_id, seed=run.seed,
        terminal_status=run.terminal_status, intended_ivs=dict(task.ivs),
        achieved_depth=len(calls), peak_fill=max((_fill(e.usage) for e in events), default=0),
        fill_at_use=fill_at_use, competitors_surfaced=competitors,
        success=success, assertions_passed=passed, assertions_total=total,
        critical_outcome=outcome, handle_available=handle_available, handle_used=handle_used,
        first_error_depth=first_error_depth, cascade=_cascade(events, task),
        redundant_call_count=redundant, recovered=recovered,
        wrong_tool_count=wrong_tool_count, confusion_pairs=confusion,
        total_tokens=tot_in + tot_out + tot_cr + tot_cc, total_output_tokens=tot_out,
        total_cache_read=tot_cr, total_cache_creation=tot_cc, total_cost_usd=cost_usd,
        sequential_round_trips=len(calls),
    )


def read_runs(
    events_path: Path, runs_path: Path
) -> tuple[dict[str, list[CallEvent]], dict[str, RunRecord]]:
    """Reconstruct events (grouped by run_id) + run records from the JSONL logs."""
    events_by_run: dict[str, list[CallEvent]] = {}
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                events_by_run.setdefault(d["run_id"], []).append(CallEvent(**d))
    runs: dict[str, RunRecord] = {}
    if runs_path.exists():
        for line in runs_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                runs[d["run_id"]] = RunRecord(**d)
    return events_by_run, runs
