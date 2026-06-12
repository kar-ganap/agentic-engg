"""Tests for the per-call event + run-record loggers (Phase 1.1).

Append-only JSONL, persistence-only (no derived metrics). Mirrors the
BudgetLogger idiom.
"""

from __future__ import annotations

import json
from pathlib import Path

from stance.tooluse.events import CallEvent, EventLogger, RunRecord


def test_call_event_minimal_and_roundtrip() -> None:
    ev = CallEvent(run_id="r1", turn_index=0, is_tool_call=True, tool_called="get_order")
    d = json.loads(ev.to_jsonl())
    assert d["run_id"] == "r1" and d["turn_index"] == 0
    assert d["is_tool_call"] is True and d["tool_called"] == "get_order"
    assert d["extracted_ids"] == []  # default


def test_run_record_carries_terminal_status() -> None:
    rr = RunRecord(run_id="r1", terminal_status="complete", final_answer_ref="sha:abc")
    d = json.loads(rr.to_jsonl())
    assert d["terminal_status"] == "complete" and d["final_answer_ref"] == "sha:abc"


def test_logger_is_append_only(tmp_path: Path) -> None:
    ev_path = tmp_path / "events.jsonl"
    run_path = tmp_path / "runs.jsonl"
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    logger.log_event(CallEvent(run_id="r1", turn_index=0, is_tool_call=True))
    logger.log_event(CallEvent(run_id="r1", turn_index=1, is_tool_call=False, is_final=True))
    logger.log_run(RunRecord(run_id="r1", terminal_status="complete"))

    event_lines = ev_path.read_text().strip().splitlines()
    run_lines = run_path.read_text().strip().splitlines()
    assert len(event_lines) == 2
    assert len(run_lines) == 1
    assert json.loads(event_lines[1])["is_final"] is True


def test_logger_records_usage_and_extracted_ids(tmp_path: Path) -> None:
    logger = EventLogger(events_path=tmp_path / "e.jsonl", runs_path=tmp_path / "r.jsonl")
    logger.log_event(
        CallEvent(
            run_id="r1",
            turn_index=2,
            is_tool_call=True,
            tool_called="get_order",
            usage={"input_tokens": 1234, "cache_read_input_tokens": 1000},
            context_size_at_call=1234,
            extracted_ids=["A-7731"],
        )
    )
    d = json.loads((tmp_path / "e.jsonl").read_text().strip())
    assert d["usage"]["input_tokens"] == 1234
    assert d["context_size_at_call"] == 1234
    assert d["extracted_ids"] == ["A-7731"]
