"""Offline tests for the Exercise B cache-measurement loop.

cache_run.py lives in experiments/ (like run.py), so we add it to the path. The
reusable logic (pricing, cache_control, usage capture) is tested in the stance
package; here we cover cache_run's own loop + policies with a fake complete_fn.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from stance.instrumentation import BudgetLogger

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "phase-1.0"))
import cache_run  # noqa: E402


def _resp(read: int, create: int, inp: int = 10, out: int = 5) -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=inp, output_tokens=out,
            cache_read_input_tokens=read, cache_creation_input_tokens=create,
        )
    )


def test_usage_dict_coerces_none_to_zero() -> None:
    r = SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=10, output_tokens=5,
            cache_read_input_tokens=None, cache_creation_input_tokens=20,
        )
    )
    assert cache_run.usage_dict(r) == {
        "input_tokens": 10, "output_tokens": 5,
        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 20,
    }


def test_pol_stable_is_identity() -> None:
    tools = [{"name": "a"}]
    hist = cache_run._history(2)
    assert cache_run.pol_stable(1, tools, "sys", hist) == ("sys", tools, hist)


def test_pol_tool_reorder_consecutive_turns_differ() -> None:
    tools = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
    _, t1, _ = cache_run.pol_tool_reorder(1, tools, "s", [])
    _, t2, _ = cache_run.pol_tool_reorder(2, tools, "s", [])
    assert t1 != tools and t2 != t1


def test_pol_shape_mix_changes_every_history_block() -> None:
    hist = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    _, _, h1 = cache_run.pol_shape_mix(1, [], "s", hist)
    _, _, h2 = cache_run.pol_shape_mix(2, [], "s", hist)
    assert all(m1["content"] != m2["content"] for m1, m2 in zip(h1, h2, strict=True))


def test_pol_timestamp_changes_system_each_turn() -> None:
    s1, _, _ = cache_run.pol_timestamp_system(1, [], "sys", [])
    s2, _, _ = cache_run.pol_timestamp_system(2, [], "sys", [])
    assert s1 != s2 and "sys" in s1


def test_run_policy_logs_one_record_per_turn(tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []

    def fake_complete(**kw: Any) -> SimpleNamespace:
        calls.append(kw)
        return _resp(read=1000, create=0)

    logger = BudgetLogger(tmp_path / "c.jsonl")
    logger.new_run("t")
    recs = cache_run.run_policy(
        "stable", turns=3, model="claude-haiku-4-5", tools=[{"name": "a"}],
        system="sys", complete_fn=fake_complete, logger=logger,
    )
    assert len(recs) == 3 and len(calls) == 3
    lines = (tmp_path / "c.jsonl").read_text().splitlines()
    assert len(lines) == 3
    rec = json.loads(lines[0])
    assert rec["usage"]["cache_read_input_tokens"] == 1000
    assert rec["cost_usd"] > 0


def test_run_policy_restore_switches_to_stable(tmp_path: Path) -> None:
    def fake_complete(**kw: Any) -> SimpleNamespace:
        return _resp(read=1000, create=0)

    logger = BudgetLogger(tmp_path / "c.jsonl")
    logger.new_run("t")
    recs = cache_run.run_policy(
        "tool_reorder", turns=4, model="claude-haiku-4-5",
        tools=[{"name": "a"}, {"name": "b"}], system="sys",
        complete_fn=fake_complete, logger=logger, restore_at=2,
    )
    assert [r["active"] for r in recs] == ["tool_reorder", "tool_reorder", "stable", "stable"]
