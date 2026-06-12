"""Tests for the Module 2 agentic loop (`run_tool_loop`) with a fake complete_fn.

Covers: happy path (complete) + event/run-record logging; loop-guard warn-then-break;
guard-off → max_turns; max_turns with distinct calls; crash handling (both
raise_on_crash modes, always recorded). No API — `complete_fn` is injected.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from anthropic.types import TextBlock, ToolUseBlock

from stance.tooluse.domain import Account, Order, World
from stance.tooluse.events import EventLogger, RefStore
from stance.tooluse.loop import run_tool_loop
from stance.tooluse.tools import make_tools


def _usage(n: int = 100) -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=n, output_tokens=10, cache_read_input_tokens=0, cache_creation_input_tokens=0
    )


def _msg(content: list[Any], stop_reason: str) -> SimpleNamespace:
    return SimpleNamespace(content=content, stop_reason=stop_reason, usage=_usage())


def _tu(tid: str, name: str, inp: dict[str, Any]) -> ToolUseBlock:
    return ToolUseBlock(type="tool_use", id=tid, name=name, input=inp)


def _txt(s: str) -> TextBlock:
    return TextBlock(type="text", text=s, citations=None)


def _tools() -> Any:
    world = World()
    world.accounts["A-7731"] = Account("A-7731", "Jane Doe")
    world.orders["O-1042"] = Order("O-1042", "A-7731", 12)
    return make_tools(world, "A")


def _harness(tmp_path: Path) -> tuple[EventLogger, RefStore]:
    logger = EventLogger(events_path=tmp_path / "events.jsonl", runs_path=tmp_path / "runs.jsonl")
    return logger, RefStore(tmp_path / "refs")


def _read(p: Path) -> list[dict[str, Any]]:
    if not p.exists():
        return []
    text = p.read_text().strip()
    return [json.loads(line) for line in text.splitlines()] if text else []


def test_happy_path_completes_and_logs(tmp_path: Path) -> None:
    logger, refs = _harness(tmp_path)
    responses = iter([
        _msg([_tu("t1", "get_order", {"order_id": "O-1042"})], "tool_use"),
        _msg([_txt("All set — the order is eligible.")], "end_turn"),
    ])
    out = run_tool_loop(
        task="Check order O-1042.", system="You are support.", tools=_tools(), model="m",
        complete_fn=lambda **_: next(responses), logger=logger, refs=refs, run_id="r1", max_turns=5,
    )
    assert out.terminal_status == "complete"
    assert "All set" in out.final_answer
    events = _read(tmp_path / "events.jsonl")
    assert len(events) == 2
    assert events[0]["is_tool_call"] and events[0]["tool_called"] == "get_order"
    assert events[1]["is_final"] is True
    runs = _read(tmp_path / "runs.jsonl")
    assert runs[0]["terminal_status"] == "complete" and runs[0]["final_answer_ref"]


def test_loop_guard_warn_then_break(tmp_path: Path) -> None:
    logger, refs = _harness(tmp_path)
    same = _msg([_tu("t1", "get_order", {"order_id": "O-1042"})], "tool_use")
    out = run_tool_loop(
        task="x", system="s", tools=_tools(), model="m",
        complete_fn=lambda **_: same, logger=logger, refs=refs, run_id="r2",
        loop_guard=True, max_turns=10,
    )
    assert out.terminal_status == "loop_guard"
    actions = [e.get("guard_action") for e in _read(tmp_path / "events.jsonl")]
    assert actions == [None, "warn", "break"]


def test_guard_off_runs_to_max_turns(tmp_path: Path) -> None:
    logger, refs = _harness(tmp_path)
    same = _msg([_tu("t1", "get_order", {"order_id": "O-1042"})], "tool_use")
    out = run_tool_loop(
        task="x", system="s", tools=_tools(), model="m",
        complete_fn=lambda **_: same, logger=logger, refs=refs, run_id="r3",
        loop_guard=False, max_turns=4,
    )
    assert out.terminal_status == "max_turns"
    assert len(_read(tmp_path / "events.jsonl")) == 4  # one per turn, guard off


def test_max_turns_with_distinct_calls(tmp_path: Path) -> None:
    logger, refs = _harness(tmp_path)
    n = {"i": 0}

    def fn(**_: Any) -> SimpleNamespace:
        n["i"] += 1
        return _msg([_tu(f"t{n['i']}", "get_order", {"order_id": f"O-{n['i']}"})], "tool_use")

    out = run_tool_loop(
        task="x", system="s", tools=_tools(), model="m",
        complete_fn=fn, logger=logger, refs=refs, run_id="r4", loop_guard=True, max_turns=3,
    )
    assert out.terminal_status == "max_turns"  # distinct args → guard never triggers


def test_crash_recorded_not_raised_when_flag_off(tmp_path: Path) -> None:
    logger, refs = _harness(tmp_path)

    def boom(**_: Any) -> SimpleNamespace:
        raise RuntimeError("kaboom")

    out = run_tool_loop(
        task="x", system="s", tools=_tools(), model="m",
        complete_fn=boom, logger=logger, refs=refs, run_id="r5", raise_on_crash=False,
    )
    assert out.terminal_status == "crash"
    rec = _read(tmp_path / "runs.jsonl")[0]
    assert rec["terminal_status"] == "crash" and "kaboom" in rec["note"]


def test_crash_raises_when_flag_on_but_still_records(tmp_path: Path) -> None:
    logger, refs = _harness(tmp_path)

    def boom(**_: Any) -> SimpleNamespace:
        raise RuntimeError("kaboom")

    with pytest.raises(RuntimeError):
        run_tool_loop(
            task="x", system="s", tools=_tools(), model="m",
            complete_fn=boom, logger=logger, refs=refs, run_id="r6", raise_on_crash=True,
        )
    rec = _read(tmp_path / "runs.jsonl")[0]
    assert rec["terminal_status"] == "crash"  # finally still wrote it
