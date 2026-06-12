"""Phase 1.1 #4 chain sweep runner.

SAFE BY DEFAULT: prints the plan + cost estimate and exits unless --go is passed.
Runs each cell×seed through build_chain_task → make_tools → run_tool_loop (DeepSeek
compat endpoint; raise_on_crash=False for batch robustness), then scores +
aggregates per cell. Raw logs → runs/phase-1.1/ (gitignored). Key strictly from .env.

    uv run python experiments/phase-1.1/run.py                                  # dry-run
    uv run python experiments/phase-1.1/run.py --go                             # all cells, 5 seeds
    uv run python experiments/phase-1.1/run.py --sweep competition --limit-seeds 2 --go  # pilot
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_config as cfg  # noqa: E402

from stance.secrets import deepseek_api_key  # noqa: E402
from stance.tooluse.events import EventLogger, RefStore  # noqa: E402
from stance.tooluse.loop import run_tool_loop  # noqa: E402
from stance.tooluse.score import read_runs, score  # noqa: E402
from stance.tooluse.tasks.chain import build_chain_task  # noqa: E402
from stance.tooluse.tools import make_tools  # noqa: E402

OUT = Path("runs/phase-1.1")
SYSTEM = (
    "You are a customer-support agent. Complete the user's request using the available tools. "
    "The order id is given in the request. When the task is done, reply with a one-sentence "
    "confirmation and do NOT call another tool."
)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--go", action="store_true", help="actually run (else dry-run: plan + cost)")
    p.add_argument("--sweep", default="all", help="one sweep, or 'all' (see run_config CELLS)")
    p.add_argument("--limit-seeds", type=int, default=len(cfg.SEEDS))
    p.add_argument("--model", default=cfg.MODEL)
    args = p.parse_args()

    cells = [c for c in cfg.CELLS if args.sweep == "all" or c.sweep == args.sweep]
    seeds = cfg.SEEDS[: args.limit_seeds]

    if not args.go:
        cfg._main()
        print(
            f"\n(dry-run) would run {len(cells)} cells × {len(seeds)} seeds "
            f"= {len(cells) * len(seeds)} runs [--sweep={args.sweep}]. Pass --go to execute."
        )
        return

    import anthropic

    client = anthropic.Anthropic(
        base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
    )
    OUT.mkdir(parents=True, exist_ok=True)
    ev_path, run_path = OUT / "sweep_events.jsonl", OUT / "sweep_runs.jsonl"
    for fp in (ev_path, run_path):
        fp.unlink(missing_ok=True)
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    refs = RefStore(OUT / "refs")

    tasks_by_run = {}
    n, total = 0, len(cells) * len(seeds)
    for cell in cells:
        fill_tokens = cfg.FILL_TOKENS[cell.fill]
        comp_n = cfg.COMPETITION_N[cell.competition]
        for seed in seeds:
            world, task = build_chain_task(
                seed=seed, depth=cell.depth, fill_tokens=fill_tokens,
                competition_n=comp_n, position=cell.position, arm=cell.arm,
            )
            tools = make_tools(world, cell.arm, terminal_style="crisp")
            run_id = f"{cell.cell_id}-s{seed}"
            tasks_by_run[run_id] = task
            n += 1
            print(f"[{n}/{total}] {run_id} ...", end=" ", flush=True)
            out = run_tool_loop(
                task=task.prompt, system=SYSTEM, tools=tools, model=args.model,
                complete_fn=lambda **kw: client.messages.create(**kw),
                logger=logger, refs=refs, run_id=run_id, cell_id=cell.cell_id,
                task_id=cell.tier, seed=seed, terminal_style="crisp", loop_guard=True,
                max_turns=20, max_tokens=2048, raise_on_crash=False,
            )
            print(out.terminal_status)

    by_run, runs = read_runs(ev_path, run_path)
    summaries = {
        rid: score(by_run.get(rid, []), runs[rid], tasks_by_run[rid])
        for rid in runs
        if rid in tasks_by_run
    }
    sum_path = OUT / "summaries.jsonl"
    with sum_path.open("w", encoding="utf-8") as f:
        for s in summaries.values():
            f.write(s.to_jsonl() + "\n")

    print("\n=== per-cell summary (critical_outcome distribution) ===")
    by_cell: dict[str, list] = {}
    for s in summaries.values():
        by_cell.setdefault(s.cell_id or "?", []).append(s)
    for cid in sorted(by_cell):
        ss = by_cell[cid]
        oc = Counter(s.critical_outcome for s in ss)
        succ = sum(1 for s in ss if s.success)
        mean_tok = sum(s.total_tokens for s in ss) / len(ss)
        print(
            f"  {cid:40} n={len(ss)} success={succ}/{len(ss)} "
            f"mis-bind={oc.get('mis-bind', 0)} {dict(oc)}  ~{mean_tok / 1e3:.0f}k tok"
        )

    total_cost = sum(s.total_cost_usd for s in summaries.values())
    print(f"\ntotal cost: ${total_cost:.3f}  ({len(summaries)} runs)  → {sum_path}")


if __name__ == "__main__":
    main()
