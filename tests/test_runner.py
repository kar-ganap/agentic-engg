"""Context-rot runner tests (Phase 1.0).

Unit tests are offline (DI'd fakes — no API). One slow test exercises the real
Anthropic API to verify tool_call_stream messages are accepted (the tools-param
gotcha) and the needle is found in an easy case.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any

import pytest

from stance.rot.haystack import build_haystack
from stance.rot.runner import (
    _answer_text,
    _tools_for,
    accuracy_by_length,
    load_records,
    passband_knee,
    run_cell,
)

FILLER = [
    "The harbor was quiet that morning and the sky stayed a pale grey.",
    "She folded the worn map carefully and tucked it into her coat pocket.",
    "Rain had washed the cobbled streets clean overnight, leaving them slick.",
    "A lone gull circled the empty pier, crying into the salt wind.",
    "The little bakery opened its shutters at six, as it always did.",
]


def _hit_response(**_kw: Any) -> SimpleNamespace:
    return SimpleNamespace(content=[{"type": "text", "text": "The code is QX-7793-LK."}])


def _miss_response(**_kw: Any) -> SimpleNamespace:
    return SimpleNamespace(content=[{"type": "text", "text": "I could not locate it."}])


def _fake_count(**_kw: Any) -> int:
    return 1234


def test_run_cell_writes_one_record_per_run(tmp_path: Any) -> None:
    out = tmp_path / "r.jsonl"
    n = run_cell(
        structure="clean_essay", competition="neutral", similarity="high", model="m",
        lengths=[500, 1000], depths=[0.5], seeds=[1, 2],
        complete_fn=_hit_response, count_fn=_fake_count, out_path=out,
        filler_sentences=FILLER,
    )
    assert n == 4  # 2 lengths x 1 depth x 2 seeds
    recs = load_records(out)
    assert len(recs) == 4
    assert all(r["hit"] for r in recs)
    assert all(r["exact_tokens"] == 1234 for r in recs)
    assert {r["target_tokens"] for r in recs} == {500, 1000}


def test_run_cell_scores_misses(tmp_path: Any) -> None:
    out = tmp_path / "r.jsonl"
    run_cell(
        structure="clean_essay", competition="neutral", similarity="high", model="m",
        lengths=[500], depths=[0.5], seeds=[1],
        complete_fn=_miss_response, count_fn=_fake_count, out_path=out,
        filler_sentences=FILLER,
    )
    assert load_records(out)[0]["hit"] is False


def test_run_cell_skips_over_limit(tmp_path: Any) -> None:
    out = tmp_path / "r.jsonl"

    def _huge_count(**_kw: Any) -> int:
        return 999_999  # always over the limit

    n = run_cell(
        structure="clean_essay", competition="neutral", similarity="high", model="m",
        lengths=[500], depths=[0.5], seeds=[1],
        complete_fn=_hit_response, count_fn=_huge_count, out_path=out,
        filler_sentences=FILLER, max_input_tokens=190_000,
    )
    assert n == 0  # the single over-limit run was skipped, not sent
    assert not out.exists() or load_records(out) == []


def test_tools_for_clean_vs_stream() -> None:
    essay = build_haystack(
        structure="clean_essay", competition="neutral", similarity="high",
        target_tokens=500, depth=0.5, seed=1, filler_sentences=FILLER,
    )
    assert _tools_for(essay.messages) == []  # no tool_use in essay

    stream = build_haystack(
        structure="tool_call_stream", competition="neutral", similarity="high",
        target_tokens=800, depth=0.5, seed=1,
    )
    tools = _tools_for(stream.messages)
    assert tools and all("input_schema" in t for t in tools)


def test_answer_text_handles_object_and_dict_blocks() -> None:
    obj = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hello "), SimpleNamespace(type="tool_use")]
    )
    assert _answer_text(obj) == "hello "
    dct = SimpleNamespace(content=[{"type": "text", "text": "world"}])
    assert _answer_text(dct) == "world"


def test_accuracy_curve_and_knee() -> None:
    # Simulate rot: full accuracy through 10k, then it drops.
    by_length = {1000: 1.0, 5000: 1.0, 10000: 1.0, 50000: 0.4, 100000: 0.1}
    recs: list[dict[str, Any]] = []
    for length, acc in by_length.items():
        nhit = round(acc * 10)
        for i in range(10):
            recs.append({"target_tokens": length, "exact_tokens": length, "hit": i < nhit})
    curve = accuracy_by_length(recs)
    assert [t for t, _ in curve] == [1000, 5000, 10000, 50000, 100000]
    ceiling, knee = passband_knee(curve, drop=0.1)
    assert ceiling == 1.0
    assert knee == 50000  # first length >0.1 below the ceiling


def test_passband_knee_full_passband() -> None:
    curve = [(1000, 1.0), (10000, 0.98), (100000, 0.95)]
    ceiling, knee = passband_knee(curve, drop=0.1)
    assert ceiling == 1.0
    assert knee is None  # never drops >0.1 → full passband across the range


@pytest.mark.slow
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
def test_real_api_tool_stream_accepted(tmp_path: Any) -> None:
    """Verify the real API accepts tool_call_stream history (tools-param gotcha)
    and finds the needle in an easy case. Burns ~$0.001."""
    import anthropic

    client = anthropic.Anthropic()

    def complete(**kw: Any) -> Any:
        return client.messages.create(**kw)

    def count(**kw: Any) -> int:
        return client.messages.count_tokens(**kw).input_tokens

    out = tmp_path / "r.jsonl"
    n = run_cell(
        structure="tool_call_stream", competition="neutral", similarity="high",
        model="claude-haiku-4-5-20251001",
        lengths=[1500], depths=[0.5], seeds=[1],
        complete_fn=complete, count_fn=count, out_path=out, max_tokens=64,
    )
    assert n == 1
    rec = load_records(out)[0]
    assert rec["exact_tokens"] > 0
    assert rec["hit"] is True  # easy case: short, neutral, high-sim
