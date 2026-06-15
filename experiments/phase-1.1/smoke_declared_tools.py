"""Phase 1.1 entry gate — declared-tools smoke test (DeepSeek Anthropic-compat).

THE build-path gate (see docs/phases/phase-1.1-plan.md § Open gates). Phase 1.0-ext
found that with *no* tools declared + a tool-call history, DeepSeek leaks its internal
"DSML" markup as text (lessons §0.17). Module 2 *declares* tools, so the question is:
when a tool is DECLARED, does DeepSeek's Anthropic-compatible endpoint return a clean,
structured `tool_use` block our harness can dispatch — or does it leak markup-as-text?

- CLEAN  → build the tool harness on the Anthropic-compatible endpoint (reuse pipeline).
- LEAK   → fall back to DeepSeek's native OpenAI-format client for tool calls.

Makes ONE real DeepSeek call (~$0.001). Key strictly from .env via stance.secrets.

    uv run python experiments/phase-1.1/smoke_declared_tools.py
"""

from __future__ import annotations

import anthropic

from stance.secrets import deepseek_api_key
from stance.tools import ADD

MODEL = "deepseek-v4-flash"
PROMPT = "What is 47 plus 58? Use the add tool to compute it; do not answer directly."

# Markers of the §0.17 DSML leak (internal tool-call markup surfaced as text).
LEAK_MARKERS = ("DSML", "｜", "<tool_call", "tool_calls", "invoke name", "<function")


def _has_leak(text: str) -> list[str]:
    return [m for m in LEAK_MARKERS if m in text]


def main() -> None:
    client = anthropic.Anthropic(
        base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[ADD.api_spec()],  # type: ignore[list-item]
        messages=[{"role": "user", "content": PROMPT}],
    )

    print(f"model={MODEL}  stop_reason={resp.stop_reason!r}")
    print("--- content blocks ---")
    tool_use_blocks = []
    leak_hits: list[str] = []
    for i, block in enumerate(resp.content):
        btype = getattr(block, "type", "?")
        if btype == "tool_use":
            tool_use_blocks.append(block)
            name, inp = getattr(block, "name", None), getattr(block, "input", None)
            print(f"  [{i}] tool_use  name={name!r}  input={inp!r}")
        elif btype == "text":
            txt = getattr(block, "text", "")
            hits = _has_leak(txt)
            leak_hits += hits
            print(f"  [{i}] text ({len(txt)} chars){'  LEAK:' + str(hits) if hits else ''}")
            print(f"        {txt[:300]!r}")
        else:
            print(f"  [{i}] {btype}: {block!r}")

    print("--- VERDICT ---")
    if tool_use_blocks and not leak_hits:
        print("CLEAN ✅ — structured tool_use returned; no markup leak.")
        print("→ Build the Phase 1.1 harness on the Anthropic-compatible endpoint.")
    elif leak_hits:
        print(f"LEAK ❌ — markup surfaced as text {sorted(set(leak_hits))}.")
        print("→ Fall back to DeepSeek's native OpenAI-format client for tool calls.")
    else:
        print("INCONCLUSIVE ⚠️ — no tool_use block and no leak (model answered in text).")
        print("→ Re-probe with a stronger trigger / tool_choice before deciding.")


if __name__ == "__main__":
    main()
