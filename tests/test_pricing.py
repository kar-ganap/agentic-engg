"""Tests for the exact cost model (Exercise B instrumentation).

Prices verified against platform.claude.com/docs pricing 2026-06-05. The cost
function is pure (no API) so these are exact hand-computed checks.
"""

from __future__ import annotations

import pytest

from stance.instrumentation.pricing import cost, hit_rate


def test_haiku_cost_5m_hand_computed() -> None:
    # (1000*1.0 + 500*5.0 + 2000*1.25 + 8000*0.10) / 1e6 = 6800/1e6
    c = cost(
        "claude-haiku-4-5",
        input_tokens=1000,
        output_tokens=500,
        cache_creation_input_tokens=2000,
        cache_read_input_tokens=8000,
    )
    assert c == pytest.approx(0.0068)


def test_one_hour_write_costs_more() -> None:
    # 1h write multiplier is 2x base (2.0 for Haiku) vs 1.25 for 5m.
    # (1000 + 2500 + 2000*2.0 + 800)/1e6 = 8300/1e6
    c = cost(
        "claude-haiku-4-5",
        input_tokens=1000,
        output_tokens=500,
        cache_creation_input_tokens=2000,
        cache_read_input_tokens=8000,
        ttl="1h",
    )
    assert c == pytest.approx(0.0083)


def test_model_id_with_date_suffix_resolves() -> None:
    # The real model id carries a date suffix; it must resolve to the base price.
    a = cost("claude-haiku-4-5-20251001", input_tokens=1_000_000)
    b = cost("claude-haiku-4-5", input_tokens=1_000_000)
    assert a == b == pytest.approx(1.0)  # $1 / MTok input


def test_sonnet_and_opus_base_input() -> None:
    assert cost("claude-sonnet-4-6", input_tokens=1_000_000) == pytest.approx(3.0)
    assert cost("claude-opus-4-8", input_tokens=1_000_000) == pytest.approx(5.0)


def test_deepseek_base_prices() -> None:
    # cross-provider workhorse + stronger tier (verified vs api-docs.deepseek.com 2026-06-05)
    assert cost("deepseek-v4-flash", input_tokens=1_000_000) == pytest.approx(0.14)
    assert cost("deepseek-v4-flash", input_tokens=0, output_tokens=1_000_000) == pytest.approx(0.28)
    assert cost("deepseek-v4-pro", input_tokens=1_000_000) == pytest.approx(0.435)


def test_unknown_model_raises() -> None:
    with pytest.raises(KeyError):
        cost("gpt-4", input_tokens=10)


def test_hit_rate() -> None:
    # cache_read / (cache_read + cache_creation + input)
    assert hit_rate(
        input_tokens=1000, cache_creation_input_tokens=2000, cache_read_input_tokens=8000
    ) == pytest.approx(8000 / 11000)


def test_hit_rate_zero_when_no_tokens() -> None:
    assert hit_rate(
        input_tokens=0, cache_creation_input_tokens=0, cache_read_input_tokens=0
    ) == 0.0
