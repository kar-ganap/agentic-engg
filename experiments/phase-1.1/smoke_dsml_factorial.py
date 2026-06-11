"""Phase 1.1 — confirm the DSML leak needs BOTH ingredients (2x2, paired).

The §0.17 claim: DeepSeek leaks its internal tool-call markup ("DSML") as text only
when a tool-call HISTORY (priming) meets a MISSING tools channel (no `tools` param).
Neither factor alone should leak. The leak is *probabilistic* (~10-15% in the
cross-family run), so n=1 proves nothing — we run n seeds per cell.

Design (paired on content — same haystack per seed, vary only the two factors):
    structure ∈ {tool_call_stream, flat}  ×  tools ∈ {declared, none}
Predicts a leak ONLY in (tool_call_stream × none). Reuses the real rot haystack so
cell (stream × none) is guaranteed to reproduce the original trigger; if it does NOT
reproduce, the probe is INCONCLUSIVE (say so — don't claim).

Makes N*4 real DeepSeek calls. Key strictly from .env via stance.secrets.

    uv run python experiments/phase-1.1/smoke_dsml_factorial.py
"""

from __future__ import annotations

from typing import Any

import anthropic

from stance.rot.haystack import build_haystack
from stance.secrets import deepseek_api_key

MODEL = "deepseek-v4-flash"
N_SEEDS = 30
TARGET_TOKENS = 10_000  # diffuse stream; long enough to prime, cheap enough to sweep
LEAK_MARKERS = ("DSML", "｜", "<tool_call", "tool_calls", "invoke name", "<function")


def _flatten(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Same content as a tool_call_stream, but as ONE plain user message (no
    tool_use/tool_result structure) — removes the priming, keeps the information."""
    task = messages[0]["content"]
    question = messages[-1]["content"]
    results = [
        b["content"]
        for m in messages
        if m["role"] == "user" and isinstance(m["content"], list)
        for b in m["content"]
        if b.get("type") == "tool_result"
    ]
    return [{"role": "user", "content": f"{task}\n" + "\n".join(results) + f"\n\n{question}"}]


def _toolset(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Declare exactly the tools that appear in the history (each takes a query)."""
    names = sorted(
        {
            b["name"]
            for m in messages
            if m["role"] == "assistant" and isinstance(m["content"], list)
            for b in m["content"]
            if b.get("type") == "tool_use"
        }
    )
    return [
        {
            "name": n,
            "description": f"Archive operation: {n}.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        }
        for n in names
    ]


def _leak_hits(resp: object) -> list[str]:
    hits: list[str] = []
    for block in resp.content:  # type: ignore[attr-defined]
        if getattr(block, "type", None) == "text":
            txt = getattr(block, "text", "")
            hits += [m for m in LEAK_MARKERS if m in txt]
    return hits


def main() -> None:
    client = anthropic.Anthropic(
        base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
    )
    # cell key -> leak count
    cells = {
        ("stream", "none"): 0,
        ("stream", "tools"): 0,
        ("flat", "none"): 0,
        ("flat", "tools"): 0,
    }
    print(f"model={MODEL}  n_seeds={N_SEEDS}  target_tokens={TARGET_TOKENS}  (= {N_SEEDS*4} calls)")
    for seed in range(N_SEEDS):
        h = build_haystack(
            structure="tool_call_stream",
            competition="diffuse",
            similarity="low",
            target_tokens=TARGET_TOKENS,
            depth=0.5,
            seed=seed,
        )
        stream_msgs = h.messages
        flat_msgs = _flatten(stream_msgs)
        tools = _toolset(stream_msgs)
        variants = {
            ("stream", "none"): (stream_msgs, None),
            ("stream", "tools"): (stream_msgs, tools),
            ("flat", "none"): (flat_msgs, None),
            ("flat", "tools"): (flat_msgs, tools),
        }
        for key, (msgs, tl) in variants.items():
            kw: dict[str, Any] = {"model": MODEL, "max_tokens": 512, "messages": msgs}
            if tl is not None:
                kw["tools"] = tl
            resp = client.messages.create(**kw)
            if _leak_hits(resp):
                cells[key] += 1
        print(f"  seed {seed:2d} done", end="\r")

    print(f"\n--- DSML leak rate (leaks / {N_SEEDS}) ---")
    print(f"{'':18}{'tools=none':>14}{'tools=declared':>16}")
    for struct in ("stream", "flat"):
        none_r = cells[(struct, 'none')]
        tools_r = cells[(struct, 'tools')]
        print(f"{struct:18}{none_r:>10}/{N_SEEDS:<3}{tools_r:>12}/{N_SEEDS:<3}")

    print("--- VERDICT ---")
    sn = cells[("stream", "none")]
    others = cells[("stream", "tools")] + cells[("flat", "none")] + cells[("flat", "tools")]
    if sn == 0:
        print("INCONCLUSIVE ⚠️ — (stream × none) did NOT reproduce the leak at this "
              "length/n; bump TARGET_TOKENS / N_SEEDS before claiming.")
    elif sn > 0 and others == 0:
        print(f"CONFIRMED ✅ — leak ONLY in (stream × none): {sn}/{N_SEEDS}; all other "
              "cells 0. Both ingredients (tool-call priming AND missing tools channel) "
              "are necessary; declaring tools eliminates it.")
    else:
        print(f"PARTIAL ⚠️ — (stream × none)={sn}/{N_SEEDS} but other cells nonzero "
              f"({others}); the leak is not cleanly conjunctive — inspect.")


if __name__ == "__main__":
    main()
