"""#3 step-1 gate — does DeepSeek prefix-caching engage via /anthropic, and does mutating the
tool block bust it? (The cost-model mechanism #3 depends on; the doc leaves tool-def caching
undocumented.) Sequence: warm A → repeat A (expect cache hit) → mutate B (expect hit drop) →
A again (expect re-hit). Result 2026-06-14: cache_read 15,488 on repeat → 0 on mutate → 15,488
on re-hit. CONFIRMED: tools are in the cached prefix; mutating them invalidates the whole suffix.
Reported as Anthropic-style `cache_read_input_tokens` (so the scorer/pricing read it directly).

    uv run python experiments/phase-1.1/smoke_cache.py    # ~$0.01
"""

from __future__ import annotations

import random

import anthropic

from stance.secrets import deepseek_api_key
from stance.tooluse.domain import build_world
from stance.tooluse.tools import Tool, make_tools


def _api(tools: tuple[Tool, ...]) -> list[dict[str, object]]:
    return [{"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in tools]


def main() -> None:
    client = anthropic.Anthropic(
        base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
    )
    world = build_world(random.Random(1), n_accounts=2, orders_per_account=1)
    tobj = make_tools(world, "A")
    tools_a, tools_b = _api(tobj), _api(tobj[:-1])  # B drops the last tool → mutates the block
    filler = "Context note: routine account review, nothing actionable. " * 1500  # big prefix
    msgs = [{"role": "user", "content": filler + "\n\nReply with OK."}]

    def call(tools: list[dict[str, object]], label: str) -> None:
        r = client.messages.create(
            model="deepseek-v4-flash", system="You are a customer-support agent.",
            tools=tools, max_tokens=8, messages=msgs,
        )
        u = r.usage
        print(f"{label:14} input={u.input_tokens:>6} "
              f"cache_read={getattr(u, 'cache_read_input_tokens', 0) or 0:>6}")

    call(tools_a, "warm (A)")
    call(tools_a, "repeat (A)")  # expect cache_read ≈ full prefix
    call(tools_b, "mutate (B)")  # expect cache_read ≈ 0 (suffix after tools re-computes)
    call(tools_a, "A again")     # expect cache_read ≈ full prefix again


if __name__ == "__main__":
    main()
