"""Tests for the scorer (#5): each critical_outcome category, the write-boundary
predicate rules (subset / not-error / exact cardinality + negatives), redundant
calls, recovery, cost, and the JSONL round-trip reader.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stance.tooluse.events import CallEvent, EventLogger, RunRecord
from stance.tooluse.score import read_runs, score
from stance.tooluse.tasks.base import TaskInstance, Write
from stance.tooluse.tasks.chain import build_chain_task


def _evt(
    turn: int,
    tool: str | None,
    args: dict[str, Any] | None = None,
    *,
    extracted: list[str] | None = None,
    is_error: bool = False,
    usage: dict[str, int] | None = None,
    guard: str | None = None,
    expected: str | None = None,
) -> CallEvent:
    return CallEvent(
        run_id="r", turn_index=turn, is_tool_call=tool is not None, tool_called=tool,
        arguments=args, extracted_ids=extracted or [], is_error=is_error,
        usage=usage or {"input_tokens": 100}, guard_action=guard, tool_expected=expected,
    )


def _run(status: str = "complete") -> RunRecord:
    return RunRecord(run_id="r", terminal_status=status, model="deepseek-v4-flash")


def _chain() -> tuple[TaskInstance, str, str]:
    world, task = build_chain_task(seed=1, depth=2, fill_tokens=1000, competition_n=2)
    needle = task.dependency_edge.needle_id  # type: ignore[union-attr]
    competitor = next(c for t in world.tickets.values() for c in t.embedded_ids)
    return task, needle, competitor


def test_correct_use() -> None:
    task, needle, comp = _chain()
    events = [
        _evt(0, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(1, "get_ticket", {"ticket_id": "T"}, extracted=[comp]),
        _evt(2, "send_message", {"account_id": needle, "body": "hi"}),
    ]
    s = score(events, _run(), task)
    assert s.critical_outcome == "correct-use"
    assert s.success and s.handle_available and s.handle_used
    assert s.competitors_surfaced == 1


def test_mis_bind() -> None:
    task, needle, comp = _chain()
    events = [
        _evt(0, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(1, "get_ticket", {"ticket_id": "T"}, extracted=[comp]),
        _evt(2, "send_message", {"account_id": comp, "body": "hi"}),  # a present competitor
    ]
    s = score(events, _run(), task)
    assert s.critical_outcome == "mis-bind" and not s.success


def test_fabricate() -> None:
    task, needle, comp = _chain()
    bad = "A-0000" if needle != "A-0000" and comp != "A-0000" else "A-1234"
    events = [
        _evt(0, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(1, "get_ticket", {"ticket_id": "T"}, extracted=[comp]),
        _evt(2, "send_message", {"account_id": bad, "body": "hi"}),  # not needle, not in pool
    ]
    s = score(events, _run(), task)
    assert s.critical_outcome == "fabricate" and not s.success


def test_re_fetch() -> None:
    task, needle, comp = _chain()
    events = [
        _evt(0, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(1, "get_ticket", {"ticket_id": "T"}, extracted=[comp]),
        _evt(2, "get_order", {"order_id": "O"}, extracted=[needle]),  # re-called the producer
        _evt(3, "send_message", {"account_id": needle, "body": "hi"}),
    ]
    s = score(events, _run(), task)
    assert s.critical_outcome == "re-fetch" and s.success  # right, but via a redundant fetch


def test_error_when_no_consumer() -> None:
    task, needle, comp = _chain()
    events = [
        _evt(0, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(1, "get_ticket", {"ticket_id": "T"}, extracted=[comp]),
    ]
    s = score(events, _run("max_turns"), task)
    assert s.critical_outcome == "error" and not s.success


def test_predicate_cardinality_and_negative_assertion() -> None:
    task = TaskInstance(
        prompt="x", seed=0, ivs={"tier": "chain"},
        expected_writes=[
            Write("create_ticket", {"order_id": "O-1"}, 1),  # eligible → exactly once
            Write("create_ticket", {"order_id": "O-2"}, 0),  # ineligible → must NOT happen
        ],
    )
    bad = [
        _evt(0, "create_ticket", {"order_id": "O-1"}),
        _evt(1, "create_ticket", {"order_id": "O-2"}),
    ]
    s = score(bad, _run(), task)
    assert s.assertions_passed == 1 and s.assertions_total == 2 and not s.success  # O-2 violated
    over = [
        _evt(0, "create_ticket", {"order_id": "O-1"}),
        _evt(1, "create_ticket", {"order_id": "O-1"}),
    ]
    s2 = score(over, _run(), task)
    assert s2.assertions_passed == 1  # O-1 count 2 != 1 (over-action) fails; O-2 (0) passes


def test_subset_match_ignores_extra_args() -> None:
    task = TaskInstance(
        prompt="x", seed=0, ivs={},
        expected_writes=[Write("send_message", {"account_id": "A-1"}, 1)],
    )
    # extra `body`/`response_format` present; only account_id is asserted
    extra = {"account_id": "A-1", "body": "prose", "response_format": "detailed"}
    assert score([_evt(0, "send_message", extra)], _run(), task).success


def test_error_call_does_not_count_toward_predicate() -> None:
    task = TaskInstance(
        prompt="x", seed=0, ivs={},
        expected_writes=[Write("send_message", {"account_id": "A-1"}, 1)],
    )
    events = [_evt(0, "send_message", {"account_id": "A-1"}, is_error=True)]  # failed send
    assert not score(events, _run(), task).success


def test_redundant_call_count() -> None:
    task, needle, comp = _chain()
    events = [
        _evt(0, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(1, "get_order", {"order_id": "O"}, extracted=[needle]),  # identical signature
        _evt(2, "send_message", {"account_id": needle}),
    ]
    assert score(events, _run(), task).redundant_call_count == 1  # 1 repeat


def test_recovered_after_setback() -> None:
    task, needle, comp = _chain()
    events = [
        _evt(0, "get_order", {"order_id": "BAD"}, is_error=True),  # a setback
        _evt(1, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(2, "send_message", {"account_id": needle}),
    ]
    s = score(events, _run(), task)
    assert s.recovered and s.success and s.first_error_depth == 0


def test_cost_from_usage() -> None:
    task, needle, comp = _chain()
    events = [
        _evt(0, "send_message", {"account_id": needle},
             usage={"input_tokens": 1_000_000, "output_tokens": 0,
                    "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}),
    ]
    s = score(events, _run(), task)
    assert abs(s.total_cost_usd - 0.14) < 0.01  # v4-flash input $0.14/MTok × 1M


def _selection_task() -> TaskInstance:
    return TaskInstance(
        prompt="x", seed=0, ivs={"tier": "selection"}, expected_writes=[],
        expected_tool="search_users",
    )


def test_selection_wrong_tool() -> None:
    s = score([_evt(0, "search_accounts", {"query": "Jane"})], _run(), _selection_task())
    assert s.wrong_tool_count == 1 and not s.success
    assert ("search_users", "search_accounts") in s.confusion_pairs


def test_selection_correct_tool() -> None:
    s = score([_evt(0, "search_users", {"query": "Jane"})], _run(), _selection_task())
    assert s.wrong_tool_count == 0 and s.success


def test_read_runs_roundtrip(tmp_path: Path) -> None:
    task, needle, comp = _chain()
    logger = EventLogger(events_path=tmp_path / "e.jsonl", runs_path=tmp_path / "r.jsonl")
    for e in [
        _evt(0, "get_order", {"order_id": "O"}, extracted=[needle]),
        _evt(1, "send_message", {"account_id": needle}),
    ]:
        logger.log_event(e)
    logger.log_run(_run())
    by_run, runs = read_runs(tmp_path / "e.jsonl", tmp_path / "r.jsonl")
    s = score(by_run["r"], runs["r"], task)
    assert s.critical_outcome == "correct-use" and s.success
