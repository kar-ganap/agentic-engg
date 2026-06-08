"""Phase 1.0 Exercise B — KV-cache anti-pattern measurement.

Measures cache hit-rate + $/turn under prefix-stability anti-patterns, testing
§1.1 (tool/prefix stability) and §3.3 (the positional cost gradient). The
pre-registration is LOCKED in docs/phases/phase-1.0-exercise-B-plan.md. DVs are
exact (from `response.usage`): cache_read fraction + cost/turn. Latency is NOT
measured (non-reproducible).

Mechanism (docs-confirmed): caching follows tools→system→messages; a change at a
level invalidates that level + all after. So a tool change is worst (root). The
prefix is padded so tools alone clears the 4,096-token Haiku minimum, with 3
breakpoints (tools/system/end-history) — required to resolve the gradient.

SAFE: prints the plan + spans + cost estimate and exits unless --go.

    uv run python experiments/phase-1.0/cache_run.py                 # dry-run
    uv run python experiments/phase-1.0/cache_run.py --pilot --go    # calibration
    uv run python experiments/phase-1.0/cache_run.py --go            # all policies
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_config as cfg  # noqa: E402

from stance.context import with_cache_breakpoints  # noqa: E402
from stance.instrumentation import BudgetLogger  # noqa: E402
from stance.instrumentation.pricing import cost, hit_rate  # noqa: E402
from stance.secrets import anthropic_api_key  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "runs" / "phase-1.0" / "cache"
_STUB: list[dict[str, Any]] = [{"role": "user", "content": "."}]
# Stable, repeatable filler — same text every run so the prefix caches.
_PAD = (
    "This archival note pads the prompt with stable repeatable filler so the "
    "cacheable prefix clears the model minimum and stays byte-identical across "
    "turns. It carries no needle and no competition; only its length matters. "
)
TOOLS_TARGET = 4500  # > 4096 Haiku min, so the after-tools breakpoint caches alone
SYSTEM_TARGET = 1500


# --- padded prefix (verified via count_fn, per data-grounding) --------------


def _section_tokens(count_fn: Callable[..., int], model: str, **kw: Any) -> int:
    base = count_fn(model=model, messages=_STUB)
    return count_fn(model=model, messages=_STUB, **kw) - base


def build_system(count_fn: Callable[..., int], model: str, target: int = SYSTEM_TARGET) -> str:
    text = _PAD
    while _section_tokens(count_fn, model, system=text) < target:
        text += _PAD
    return text


def build_tools(count_fn: Callable[..., int], model: str, target: int = TOOLS_TARGET) -> list[dict[str, Any]]:
    """A few tool defs whose padded descriptions push tools ≥ target tokens."""
    def make(n_pad: int) -> list[dict[str, Any]]:
        return [
            {
                "name": f"archive_op_{i}",
                "description": f"Archive operation {i}. " + _PAD * n_pad,
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
            for i in range(8)  # ≥ turns, so tool-rotation never cycles within a run
        ]

    n_pad = 4
    while _section_tokens(count_fn, model, tools=make(n_pad)) < target:
        n_pad += 2
    return make(n_pad)


def _history(turn: int) -> list[dict[str, Any]]:
    """Append-only conversation up to `turn`: fixed prior exchanges + current query.

    Deterministic, so history(t-1) is a byte-prefix of history(t) → the moving
    end-history breakpoint caches the grown prefix across turns.
    """
    msgs: list[dict[str, Any]] = []
    for i in range(turn):
        msgs.append({"role": "user", "content": f"Turn {i} request. {_PAD * 6}"})
        msgs.append({"role": "assistant", "content": f"Turn {i} reply. {_PAD * 6}"})
    msgs.append({"role": "user", "content": f"Turn {turn} request. {_PAD * 6}"})
    return msgs


# --- prefix policies (the locked anti-patterns) -----------------------------

Policy = Callable[[int, list[dict[str, Any]], str, list[dict[str, Any]]], tuple[str, list[dict[str, Any]], list[dict[str, Any]]]]


def pol_stable(t: int, tools: list[dict[str, Any]], system: str, history: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    return system, tools, history


def pol_timestamp_system(t: int, tools: list[dict[str, Any]], system: str, history: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    return f"{system}\n[clock tick {t}]", tools, history  # system changes each turn


def pol_tool_reorder(t: int, tools: list[dict[str, Any]], system: str, history: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    k = t % len(tools)  # rotate so consecutive turns differ → tools invalidate
    return system, tools[k:] + tools[:k], history


def pol_shape_mix(t: int, tools: list[dict[str, Any]], system: str, history: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    # Re-serialize ALL prior content (locked C1 def) → invalidate from first block.
    h = [{**m, "content": f"{m['content']} [fmt{t}]"} for m in history]
    return system, tools, h


POLICIES: dict[str, Policy] = {
    "stable": pol_stable,
    "timestamp_system": pol_timestamp_system,
    "tool_reorder": pol_tool_reorder,
    "shape_mix": pol_shape_mix,
}


# --- usage + loop -----------------------------------------------------------


def usage_dict(response: Any) -> dict[str, int]:
    """Extract the four caching-relevant counts from a response's `usage`."""
    u = response.usage

    def g(name: str) -> int:
        v = getattr(u, name, 0)
        return int(v) if v is not None else 0

    return {
        "input_tokens": g("input_tokens"),
        "output_tokens": g("output_tokens"),
        "cache_creation_input_tokens": g("cache_creation_input_tokens"),
        "cache_read_input_tokens": g("cache_read_input_tokens"),
    }


def run_policy(
    label: str,
    *,
    turns: int,
    model: str,
    tools: list[dict[str, Any]],
    system: str,
    complete_fn: Callable[..., Any],
    logger: BudgetLogger,
    anti: str | None = None,
    restore_at: int | None = None,
    max_tokens: int = 16,
) -> list[dict[str, Any]]:
    """Run one policy for `turns` back-to-back calls; log per-turn usage + cost.

    `label` names the run in the log (e.g. "restore"); `anti` is the anti-pattern
    policy actually applied (defaults to `label`). `restore_at`: if set, turns ≥ it
    switch to `stable` (the restore arm uses label="restore", anti="tool_reorder").
    """
    anti = anti or label
    # Per-policy nonce in the system prefix isolates each condition's server-side
    # cache: without it the shared 5-min cache bleeds across policies (identical
    # canonical tools / rotations / history collide), spuriously inflating hits.
    nonced_system = f"[run:{label}] {system}"
    records: list[dict[str, Any]] = []
    for t in range(turns):
        active = "stable" if (restore_at is not None and t >= restore_at) else anti
        sys_, tools_, msgs_ = POLICIES[active](t, tools, nonced_system, _history(t))
        payload = with_cache_breakpoints(system=sys_, tools=tools_, messages=msgs_)
        resp = complete_fn(model=model, max_tokens=max_tokens, **payload)
        u = usage_dict(resp)
        c = cost(model, **u)
        hr = hit_rate(
            input_tokens=u["input_tokens"],
            cache_creation_input_tokens=u["cache_creation_input_tokens"],
            cache_read_input_tokens=u["cache_read_input_tokens"],
        )
        logger.record(
            turn=t, categories={}, model=model, usage=u, cost_usd=c,
            policy=label, active=active, hit_rate=hr,
        )
        records.append({"turn": t, "active": active, "hit_rate": hr, "cost_usd": c, **u})
        print(f"  [{label:16} t={t} {active:8}] read={u['cache_read_input_tokens']:>6} "
              f"create={u['cache_creation_input_tokens']:>6} hit={hr:.2f} ${c:.5f}")
    return records


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--pilot", action="store_true", help="stable-only calibration (3 turns)")
    p.add_argument("--turns", type=int, default=6)
    p.add_argument("--model", default=cfg.MODEL_PRIMARY)
    p.add_argument("--go", action="store_true", help="actually run (else dry-run)")
    args = p.parse_args()

    import anthropic

    client = anthropic.Anthropic(api_key=anthropic_api_key())

    def complete(**kw: Any) -> Any:
        return client.messages.create(**kw)

    def count(**kw: Any) -> int:
        return client.messages.count_tokens(**kw).input_tokens

    system = build_system(count, args.model)
    tools = build_tools(count, args.model)
    sys_tok = _section_tokens(count, args.model, system=system)
    tools_tok = _section_tokens(count, args.model, tools=tools)
    print(f"model: {args.model}")
    print(f"padded spans:  tools={tools_tok}  system={sys_tok}  (tools must be ≥4096)")
    if tools_tok < 4096:
        print("  WARNING: tools below the 4096 Haiku min — caching will NOT engage.")

    plan = (["stable"] if args.pilot
            else ["stable", "tool_reorder", "timestamp_system", "shape_mix", "restore"])
    print(f"policies: {plan}  turns/policy: {3 if args.pilot else args.turns} "
          f"(restore: {2 * args.turns})")
    if not args.go:
        print("\n(dry-run — pass --go to execute)")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / ("pilot.jsonl" if args.pilot else "cache_run.jsonl")
    if out_path.exists():
        out_path.unlink()  # fresh per run (BudgetLogger appends) → file stays canonical
    logger = BudgetLogger(out_path)
    if args.pilot:
        logger.new_run("pilot")
        run_policy("stable", turns=3, model=args.model, tools=tools, system=system,
                   complete_fn=complete, logger=logger)
        return
    for name in plan:
        logger.new_run(name)
        if name == "restore":
            run_policy("restore", turns=2 * args.turns, model=args.model, tools=tools,
                       system=system, complete_fn=complete, logger=logger,
                       anti="tool_reorder", restore_at=args.turns)
        else:
            run_policy(name, turns=args.turns, model=args.model, tools=tools, system=system,
                       complete_fn=complete, logger=logger)


if __name__ == "__main__":
    main()
