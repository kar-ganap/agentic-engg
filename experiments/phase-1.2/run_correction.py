"""§1.2 BEHAVIORAL-supervision test (Phase 1.2 Thread C) — the reviewers' path-to-active.

Tests §1.2's ACTUAL claim (failures as behavioral supervision, not payload survival). The agent
learns a format RULE from an early failure, a distractor audit compacts it away, then it must APPLY
the rule to late submits. **PRIMARY DV = behavioral success** = fraction of late records whose FIRST
submit uses the correct format (task success). `preserve` keeps the rule → success; `summarize`
drops it → the agent submits the raw code → INVALID.

Providers: **Haiku** (reasoning-capable — needs `strip` to reach ephemeral CoT) + **deepseek-chat**
(NON-reasoning, validated — reaches the bite; restores cross-provider). Safe-by-default; --go.

    uv run python experiments/phase-1.2/run_correction.py  # …
    uv run python experiments/phase-1.2/run_correction.py --go --seeds 1 --arm-provider anthropic \
        --arm-model claude-haiku-4-5-20251001  # …
    uv run python experiments/phase-1.2/run_correction.py --go --arm-provider deepseek-native \
        --arm-model deepseek-chat --bust-cache  # …
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import anthropic
from deepseek_native import make_native_complete_fn

from stance.secrets import anthropic_api_key, deepseek_api_key
from stance.tooluse.compaction import Compaction, Policy
from stance.tooluse.events import CallEvent, EventLogger, RefStore
from stance.tooluse.loop import run_tool_loop
from stance.tooluse.score import read_runs, score
from stance.tooluse.tasks.base import TaskInstance
from stance.tooluse.tasks.correction import build_correction_task
from stance.tooluse.tools import make_correction_tools

OUT_DIR = Path("experiments/phase-1.2/results")
RAW_DIR = Path("runs/phase-1.2")
SYSTEM = (
    "You are a records-processing agent. Follow the user's numbered steps exactly and in order, "
    "using the tools. Pay attention to any feedback a tool gives you and apply it."
)
_POLICIES: tuple[Policy, ...] = ("preserve_failures", "summarize_uniform")


def _make_complete(provider: str, bust_cache: bool) -> Any:
    if provider == "deepseek-native":
        return make_native_complete_fn(api_key=deepseek_api_key(), bust_cache=bust_cache)
    client = anthropic.Anthropic(api_key=anthropic_api_key())
    n = {"i": 0}

    def complete(**kw: Any) -> Any:
        if bust_cache:
            n["i"] += 1
            kw = {**kw, "system": f"[req {n['i']:05d}-nc] {kw['system']}"}
        return client.messages.create(**kw)

    return complete


def _behavioral_success(events: list[CallEvent], task: TaskInstance) -> float:
    """Fraction of measured records whose FIRST submit applied the learned format (task success)."""
    true_codes = task.notes["true_codes"]
    measured = task.notes["measured_ids"]
    correct = 0
    for rid in measured:
        first = next((e for e in events if e.is_tool_call and e.tool_called == "submit_record"
                      and (e.arguments or {}).get("record_id") == rid), None)
        if first is not None and (first.arguments or {}).get("code") == true_codes[rid]:
            correct += 1
    return correct / len(measured)


def _probe_failed(events: list[CallEvent]) -> bool:
    """Sanity: the R1-TEST probe actually failed (the teaching signal fired)."""
    return any(e.is_tool_call and e.tool_called == "submit_record" and e.is_error
               and (e.arguments or {}).get("record_id") == "R1-TEST" for e in events)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policies", default=",".join(_POLICIES))
    ap.add_argument("--reasoning", default="persist,strip")
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--budget-tokens", type=int, default=700)
    ap.add_argument("--keep-last", type=int, default=2)
    ap.add_argument("--max-turns", type=int, default=20)
    ap.add_argument("--n-distractor", type=int, default=7)
    ap.add_argument("--n-measured", type=int, default=2)
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--bust-cache", action="store_true")
    ap.add_argument("--arm-provider", default="anthropic")
    ap.add_argument("--arm-model", default="claude-haiku-4-5-20251001")
    args = ap.parse_args()

    policies = [p.strip() for p in args.policies.split(",")]
    reasonings = [r.strip() for r in args.reasoning.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    cells = [(p, r, s) for p in policies for r in reasonings for s in seeds]
    print(f"policies={policies} reasoning={reasonings} seeds={seeds} "
          f"cells={len(cells)}  {args.arm_provider}/{args.arm_model}")
    print(f"budget={args.budget_tokens} keep_last={args.keep_last} "
          f"n_distractor={args.n_distractor} n_measured={args.n_measured} "
          f"bust_cache={args.bust_cache}  loop_guard=OFF")
    if not args.go:
        print("DRY-RUN — pass --go. PRIMARY DV = behavioral success (late-submit first-attempt).")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    ev_path = RAW_DIR / f"correction-ev-{stamp}.jsonl"
    run_path = RAW_DIR / f"correction-run-{stamp}.jsonl"
    for p in (ev_path, run_path):
        p.unlink(missing_ok=True)
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    refs = RefStore(RAW_DIR / "refs")
    complete_fn = _make_complete(args.arm_provider, args.bust_cache)

    tasks: dict[str, TaskInstance] = {}
    meta: dict[str, tuple[str, str, int, int]] = {}
    for i, (policy, reasoning, seed) in enumerate(cells, 1):
        _, task = build_correction_task(seed=seed, n_distractor=args.n_distractor,
                                        n_measured=args.n_measured)
        tools = make_correction_tools(task.notes["records"], task.notes["chain_bodies"],
                                      task.notes["chain"])
        run_id = f"{policy}-{reasoning}-s{seed}"
        tasks[run_id] = task
        comp = Compaction(policy=policy, budget_tokens=args.budget_tokens,
                          keep_last_turns=args.keep_last)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=args.arm_model,
            complete_fn=complete_fn, logger=logger, refs=refs, run_id=run_id,
            cell_id=f"{policy}-{reasoning}", task_id=run_id, seed=seed, terminal_style="crisp",
            loop_guard=False, max_turns=args.max_turns, max_tokens=1024, compaction=comp,
            strip_reasoning=(reasoning == "strip"), raise_on_crash=True,
        )
        meta[run_id] = (policy, reasoning, seed, out.n_compactions)
        print(f"[{i}/{len(cells)}] {policy} {reasoning} s{seed}: {out.terminal_status} "
              f"compactions={out.n_compactions}")

    by_run, runs = read_runs(ev_path, run_path)
    rows: list[dict[str, Any]] = []
    for run_id, task in tasks.items():
        ev = by_run.get(run_id, [])
        summ = score(ev, runs[run_id], task)
        policy, reasoning, seed, n_comp = meta[run_id]
        rows.append({
            "policy": policy, "reasoning": reasoning, "seed": seed,
            "behavioral_success": _behavioral_success(ev, task), "probe_failed": _probe_failed(ev),
            "all_correct_eventually": int(summ.success), "n_compactions": n_comp,
            "terminal_status": summ.terminal_status, "cost_usd": summ.total_cost_usd,
            "arm_provider": args.arm_provider, "arm_model": args.arm_model,
        })

    out_path = OUT_DIR / f"correction-{stamp}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cell[(r["reasoning"], r["policy"])].append(r)
    print(f"\n§1.2 behavioral: late-submit success by reasoning × policy -> {out_path.name}")
    print(f"{'reasoning':<10} {'policy':<20} {'behav-succ':>10} {'probe-fail':>10} "
          f"{'compact':>8} {'$':>8}")
    for reasoning in reasonings:
        for policy in policies:
            rs = by_cell.get((reasoning, policy), [])
            if not rs:
                continue
            print(f"{reasoning:<10} {policy:<20} "
                  f"{mean(r['behavioral_success'] for r in rs):>10.2f} "
                  f"{mean(r['probe_failed'] for r in rs):>10.2f} "
                  f"{mean(r['n_compactions'] for r in rs):>8.1f} "
                  f"${sum(r['cost_usd'] for r in rs):>7.4f}")


if __name__ == "__main__":
    main()
