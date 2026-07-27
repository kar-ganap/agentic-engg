"""§1.2 compaction back-fill (Phase 1.2, Thread B) — does preserving FAILURES under a mid-loop
budget squeeze beat summarizing them away?

Breadcrumb-chain audit (build_compaction_task): the agent walks a chain of orders (each check
names the next → sequential, so context accumulates for the trigger); ~1-in-3 are BLOCKED, each
is_error carrying a release `ref` the final `file_report` must include. The ref lives ONLY in the
failure content (flavor-2 §1.2: forward-info, not just don't-repeat) — so summarizing the failure
away loses it. Swept across 3 policies × seeds; `loop_guard=False`.

  - ref-recall (PRIMARY DV): fraction of true release refs the agent puts in file_report — how much
    failure-info survived compaction. Mechanical (parsed from the call args; no judge).
  - filed (secondary): scorer.success — did it file a report at all
  - + n_compactions (did the trigger fire), failure-recurrence, terminal_status, cost

Policies (differ only in FAILURE treatment; all drop success payloads; last turns verbatim):
preserve_failures / summarize_but_flag / summarize_uniform. Safe-by-default; --go to spend.

    uv run python experiments/phase-1.2/run_compaction.py                    # dry-run plan
    uv run python experiments/phase-1.2/run_compaction.py --go --seeds 1      # smoke
    uv run python experiments/phase-1.2/run_compaction.py --go
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

from stance.secrets import anthropic_api_key, deepseek_api_key
from stance.tooluse.compaction import Compaction, Policy
from stance.tooluse.events import CallEvent, EventLogger, RefStore
from stance.tooluse.loop import run_tool_loop
from stance.tooluse.score import read_runs, score
from stance.tooluse.tasks.base import TaskInstance
from stance.tooluse.tasks.compaction import build_compaction_task
from stance.tooluse.tools import make_compaction_tools

OUT_DIR = Path("experiments/phase-1.2/results")
RAW_DIR = Path("runs/phase-1.2")  # raw events/runs (regenerable); summary rows are the committed DV
SYSTEM = (
    "You are a logistics agent. Use the tools to complete the audit. Follow the chain of orders "
    "(each check_shipment result names the next order to check), collect every release ref from "
    "BLOCKED orders, and when you reach the last order call file_report with ALL collected refs. "
    "Then reply with a one-sentence confirmation and do NOT call another tool."
)
_POLICIES: tuple[Policy, ...] = ("preserve_failures", "summarize_but_flag", "summarize_uniform")
_DEEPSEEK = "https://api.deepseek.com/anthropic"


def _client(provider: str) -> anthropic.Anthropic:
    if provider == "deepseek":
        return anthropic.Anthropic(base_url=_DEEPSEEK, api_key=deepseek_api_key())
    return anthropic.Anthropic(api_key=anthropic_api_key())


def _sig(e: CallEvent) -> str:
    return f"{e.tool_called}|{json.dumps(e.arguments or {}, sort_keys=True)}"


def _failure_recurrence(events: list[CallEvent]) -> int:
    """Repeated FAILED (tool,args) calls — the agent re-issued a check it already saw fail."""
    err = [_sig(e) for e in events if e.is_tool_call and e.is_error]
    return len(err) - len(set(err))


def _ref_recall(events: list[CallEvent], task: TaskInstance) -> float:
    """Fraction of true release refs the agent submitted to file_report (the PRIMARY DV — how much
    failure-carried info survived compaction). 0 if no report was filed."""
    true_refs = set(task.notes["true_refs"])
    if not true_refs:
        return 1.0
    filed = [e for e in events if e.is_tool_call and e.tool_called == "file_report"]
    if not filed:
        return 0.0
    submitted = {str(r) for r in (filed[0].arguments or {}).get("refs", [])}
    return len(submitted & true_refs) / len(true_refs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policies", default=",".join(_POLICIES))
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--budget-tokens", type=int, default=500)  # forced trigger (tuned from smoke)
    ap.add_argument("--keep-last", type=int, default=2)
    ap.add_argument("--max-turns", type=int, default=16)
    ap.add_argument("--n-orders", type=int, default=9)
    ap.add_argument("--n-blocked", type=int, default=3)  # ~1-in-3 blocked (each carries a ref)
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--arm-provider", default="deepseek")
    ap.add_argument("--arm-model", default="deepseek-v4-flash")
    args = ap.parse_args()

    policies = [p.strip() for p in args.policies.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    cells = [(p, s) for p in policies for s in seeds]
    print(f"policies={policies} seeds={seeds} cells={len(cells)}  "
          f"{args.arm_provider}/{args.arm_model}")
    print(f"budget={args.budget_tokens} keep_last={args.keep_last} max_turns={args.max_turns} "
          f"n_orders={args.n_orders} n_blocked={args.n_blocked}  loop_guard=OFF")
    if not args.go:
        print("DRY-RUN — pass --go. PRIMARY DV = ref-recall (failure-info survival, mechanical).")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    ev_path = RAW_DIR / f"compaction-events-{stamp}.jsonl"
    run_path = RAW_DIR / f"compaction-runs-{stamp}.jsonl"
    for p in (ev_path, run_path):
        p.unlink(missing_ok=True)
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    refs = RefStore(RAW_DIR / "refs")
    client = _client(args.arm_provider)

    tasks: dict[str, TaskInstance] = {}
    compactions: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    for i, (policy, seed) in enumerate(cells, 1):
        _, task = build_compaction_task(seed=seed, n_orders=args.n_orders, n_blocked=args.n_blocked)
        tools = make_compaction_tools(task.notes["chain"], task.notes["blocked"])
        run_id = f"{policy}-s{seed}"
        tasks[run_id] = task
        comp = Compaction(policy=policy, budget_tokens=args.budget_tokens,
                          keep_last_turns=args.keep_last)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=args.arm_model,
            complete_fn=lambda **kw: client.messages.create(**kw), logger=logger, refs=refs,
            run_id=run_id, cell_id=policy, task_id=run_id, seed=seed, terminal_style="crisp",
            loop_guard=False, max_turns=args.max_turns, max_tokens=1024, compaction=comp,
            raise_on_crash=True,
        )
        compactions[run_id] = out.n_compactions
        print(f"[{i}/{len(cells)}] {policy} s{seed}: {out.terminal_status} "
              f"compactions={out.n_compactions}")

    by_run, runs = read_runs(ev_path, run_path)
    for run_id, task in tasks.items():
        ev = by_run.get(run_id, [])
        summ = score(ev, runs[run_id], task)
        policy, seed = run_id.rsplit("-s", 1)
        rows.append({
            "policy": policy, "seed": int(seed), "ref_recall": _ref_recall(ev, task),
            "filed": int(summ.success), "failure_recurrence": _failure_recurrence(ev),
            "n_errors": sum(1 for e in ev if e.is_error), "achieved_depth": summ.achieved_depth,
            "n_compactions": compactions[run_id],
            "terminal_status": summ.terminal_status, "cost_usd": summ.total_cost_usd,
            "arm_provider": args.arm_provider, "arm_model": args.arm_model,
        })

    out_path = OUT_DIR / f"compaction-{stamp}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_policy[r["policy"]].append(r)
    print(f"\n§1.2 compaction by policy -> {out_path.name}")
    print(f"{'policy':<20} {'ref-recall':>10} {'filed':>6} {'compact':>8} {'errs':>5} {'$':>8}")
    for policy in policies:
        rs = by_policy.get(policy, [])
        if not rs:
            continue
        print(f"{policy:<20} {mean(r['ref_recall'] for r in rs):>10.2f} "
              f"{mean(r['filed'] for r in rs):>6.2f} "
              f"{mean(r['n_compactions'] for r in rs):>8.1f} "
              f"{mean(r['n_errors'] for r in rs):>5.1f} "
              f"${sum(r['cost_usd'] for r in rs):>7.4f}")


if __name__ == "__main__":
    main()
