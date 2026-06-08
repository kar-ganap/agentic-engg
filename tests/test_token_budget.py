"""Token-budget logger tests.

Covers the persistence contract only (shape, append-only, run-id continuity).
What counts as 'system' / 'tools' / 'history' / 'retrieved' is the caller's
responsibility and is exercised in the raw-loop test once the loop lands.
"""

from __future__ import annotations

import json
from pathlib import Path

from stance.instrumentation import BudgetLogger


def test_record_writes_jsonl_with_expected_shape(tmp_path: Path) -> None:
    logger = BudgetLogger(tmp_path / "budget.jsonl")
    run_id = logger.new_run("test-run")
    logger.record(turn=0, categories={"system": 412, "tools": 88, "history": 0}, model="m")

    lines = (tmp_path / "budget.jsonl").read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["run_id"] == run_id
    assert record["turn"] == 0
    assert record["categories"] == {"system": 412, "tools": 88, "history": 0}
    assert record["model"] == "m"
    assert "timestamp" in record


def test_record_is_append_only(tmp_path: Path) -> None:
    logger = BudgetLogger(tmp_path / "budget.jsonl")
    logger.new_run("run-a")
    logger.record(turn=0, categories={"system": 100})
    logger.record(turn=1, categories={"system": 100, "history": 50})

    lines = (tmp_path / "budget.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["turn"] == 0
    assert json.loads(lines[1])["turn"] == 1


def test_new_run_changes_run_id(tmp_path: Path) -> None:
    logger = BudgetLogger(tmp_path / "budget.jsonl")
    first = logger.new_run()
    second = logger.new_run()
    assert first != second


def test_records_usage_and_cost(tmp_path: Path) -> None:
    logger = BudgetLogger(tmp_path / "budget.jsonl")
    logger.new_run("run-u")
    usage = {
        "input_tokens": 800,
        "output_tokens": 12,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 14000,
    }
    logger.record(turn=5, categories={"history": 14800}, model="claude-haiku-4-5",
                  usage=usage, cost_usd=0.0024)
    rec = json.loads((tmp_path / "budget.jsonl").read_text().splitlines()[0])
    assert rec["usage"] == usage
    assert rec["cost_usd"] == 0.0024


def test_usage_and_cost_default_to_none(tmp_path: Path) -> None:
    # Back-compat: existing callers that record only categories still work.
    logger = BudgetLogger(tmp_path / "budget.jsonl")
    logger.new_run("run-n")
    logger.record(turn=0, categories={"system": 100})
    rec = json.loads((tmp_path / "budget.jsonl").read_text().splitlines()[0])
    assert rec["usage"] is None
    assert rec["cost_usd"] is None
