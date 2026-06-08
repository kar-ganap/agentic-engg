"""Exact token-cost model for Anthropic API usage (Exercise B instrumentation).

Pure, API-free, fully unit-tested. Cost is computed from the API's own `usage`
counts (the exact quantity, not a `count_tokens` estimate) × a pinned per-model
price table — so every cost number regenerates (Substrate Discipline #5).

Prices are USD per million tokens, verified against platform.claude.com/docs
pricing on 2026-06-05. Cache multipliers (write 1.25×/5m, 2×/1h; read 0.1×) are
documented; base prices are per-model. **Re-verify before a run if months pass.**
"""

from __future__ import annotations

from dataclasses import dataclass

_MTOK = 1_000_000


@dataclass(frozen=True)
class Price:
    """USD per million tokens for one model."""

    input: float
    output: float
    cache_write_5m: float
    cache_write_1h: float
    cache_read: float


# Pinned table (verified 2026-06-05). Keyed by base model id (no date suffix).
PRICES: dict[str, Price] = {
    "claude-haiku-4-5": Price(1.0, 5.0, 1.25, 2.0, 0.10),
    "claude-sonnet-4-6": Price(3.0, 15.0, 3.75, 6.0, 0.30),
    "claude-opus-4-8": Price(5.0, 25.0, 6.25, 10.0, 0.50),
}


def _price(model: str) -> Price:
    """Resolve a model id (with or without a date suffix) to its Price."""
    if model in PRICES:
        return PRICES[model]
    for base, price in PRICES.items():
        if model.startswith(base):  # e.g. "claude-haiku-4-5-20251001"
            return price
    raise KeyError(f"no pinned price for model {model!r} (known: {sorted(PRICES)})")


def cost(
    model: str,
    *,
    input_tokens: int,
    output_tokens: int = 0,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
    ttl: str = "5m",
) -> float:
    """Exact USD cost for one request, from its `usage` token counts.

    `ttl` selects the cache-write multiplier ("5m" default, or "1h"). The four
    token counts map 1:1 onto the Anthropic `usage` fields.
    """
    p = _price(model)
    write = p.cache_write_1h if ttl == "1h" else p.cache_write_5m
    total = (
        input_tokens * p.input
        + output_tokens * p.output
        + cache_creation_input_tokens * write
        + cache_read_input_tokens * p.cache_read
    )
    return total / _MTOK


def hit_rate(
    *,
    input_tokens: int,
    cache_creation_input_tokens: int,
    cache_read_input_tokens: int,
) -> float:
    """Fraction of input served from cache: read / (read + creation + input).

    0.0 when there are no input tokens at all (avoids div-by-zero).
    """
    total = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
    return cache_read_input_tokens / total if total else 0.0
