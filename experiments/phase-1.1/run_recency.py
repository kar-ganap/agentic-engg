"""Phase 1.1 #4-v2 (recency) — self-generated proactive-interference over a running total.

The agent applies N successive adjustments (apply_adjustment, self-generated running totals),
then must issue the FINAL total; stale totals are the interference. PRIMARY axis **N** (scales
for free); SECONDARY **semantic_similar** (blurry reasons). The instrument check: does
self-generated recency collapse at large N, or does message-recency rescue it?

SAFE BY DEFAULT: prints the grid + cost estimate and exits unless --go is passed.

    uv run python experiments/phase-1.1/run_recency.py --grid pilot              # dry-run
    uv run python experiments/phase-1.1/run_recency.py --grid pilot --go         # N=5 / 40 / 40-sim
    uv run python experiments/phase-1.1/run_recency.py --grid sweep --go         # N×similar
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_config as cfg  # noqa: E402

from stance.secrets import anthropic_api_key, deepseek_api_key  # noqa: E402
from stance.tooluse.events import EventLogger, RefStore  # noqa: E402
from stance.tooluse.loop import run_tool_loop  # noqa: E402
from stance.tooluse.score import read_runs, score  # noqa: E402
from stance.tooluse.tasks.recency import build_recency_task  # noqa: E402
from stance.tooluse.tools import make_recency_tools  # noqa: E402

OUT = Path("runs/phase-1.1/recency")
FILL = {"low": 0, "mid": 8_000}
SYSTEM = (
    "You are a customer-support agent. Use the available tools to complete the request. Apply "
    "every adjustment in order, then issue the refund for the final running total. When done, "
    "reply with a one-sentence confirmation and do NOT call another tool."
)


@dataclass(frozen=True)
class Cell:
    n: int  # number of successive adjustments (the interference count)
    similar: bool  # secondary: semantically-similar reasons (blurry anchors)
    fill: str  # low | mid

    @property
    def cell_id(self) -> str:
        return f"recency-n{self.n}-{'sim' if self.similar else 'dis'}-f{self.fill}"


def _grid(name: str) -> list[Cell]:
    if name == "pilot":  # must-hold (small N) / collapse? (large N) / + blurry reasons
        return [Cell(5, False, "low"), Cell(40, False, "low"), Cell(40, True, "low")]
    if name == "sweep":  # the N axis × the semantic modifier
        return [Cell(n, s, "low") for n in (5, 10, 20, 40) for s in (False, True)]
    if name == "fill":  # fill crossing at large N
        return [Cell(40, False, f) for f in FILL]
    if name == "all":
        return _grid("sweep") + _grid("fill")
    raise SystemExit(f"unknown --grid: {name!r}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--grid", default="pilot", help="pilot | sweep | fill | all")
    p.add_argument("--go", action="store_true", help="actually run (else dry-run: grid + cost)")
    p.add_argument("--limit-seeds", type=int, default=len(cfg.SEEDS))
    p.add_argument("--provider", choices=["deepseek", "anthropic"], default="deepseek")
    p.add_argument("--model", default=cfg.MODEL)
    args = p.parse_args()

    model = args.model
    if args.provider == "anthropic" and model == cfg.MODEL:
        model = "claude-sonnet-4-6"
    cells = _grid(args.grid)
    seeds = cfg.SEEDS[: args.limit_seeds]
    plan = [(c, s) for c in cells for s in seeds]

    if not args.go:
        print(f"=== recency #4-v2: grid={args.grid} ({args.provider} {model}) — DRY RUN ===")
        for c in cells:
            print(f"  {c.cell_id}")
        # rough: ~N turns, context accretes the N small results; base ~ fill
        est = sum((FILL[c.fill] + 30 * c.n) * (c.n + 2) for c, _ in plan)
        rate = 0.14 if args.provider == "deepseek" else 3.0
        print(f"{len(plan)} runs.  est input ≲ {est / 1e6:.1f}M tok → ≲ ${est / 1e6 * rate:.2f} "
              f"(no-cache upper bound). Pass --go.")
        return

    import anthropic

    if args.provider == "deepseek":
        client = anthropic.Anthropic(
            base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
        )
    else:
        client = anthropic.Anthropic(api_key=anthropic_api_key())
    OUT.mkdir(parents=True, exist_ok=True)
    tag = model.removeprefix("claude-")
    stem = f"{args.grid}_{tag}"
    ev_path, run_path = OUT / f"{stem}_events.jsonl", OUT / f"{stem}_runs.jsonl"
    for fp in (ev_path, run_path):
        fp.unlink(missing_ok=True)
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    refs = RefStore(OUT / "refs")

    tasks_by_run = {}
    for i, (cell, seed) in enumerate(plan, 1):
        world, task = build_recency_task(
            seed=seed, n_updates=cell.n, fill_tokens=FILL[cell.fill], semantic_similar=cell.similar
        )
        tools = make_recency_tools(world)
        run_id = f"{cell.cell_id}-s{seed}"
        tasks_by_run[run_id] = task
        print(f"[{i}/{len(plan)}] {run_id} ...", end=" ", flush=True)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=model,
            complete_fn=lambda **kw: client.messages.create(**kw),
            logger=logger, refs=refs, run_id=run_id, cell_id=cell.cell_id,
            task_id="recency", seed=seed, terminal_style="crisp",
            # loop-guard OFF: apply_adjustment is STATEFUL — repeated identical (tool,args) calls
            # are progress (each advances the cursor), not a loop. The guard's idempotent-tool
            # premise is invalid here (it killed every run at the 2nd adjustment).
            loop_guard=False,
            max_turns=cell.n + 6, max_tokens=1024, raise_on_crash=False,
        )
        print(out.terminal_status)

    by_run, runs = read_runs(ev_path, run_path)
    summaries = {
        rid: score(by_run.get(rid, []), runs[rid], tasks_by_run[rid])
        for rid in runs
        if rid in tasks_by_run
    }
    sum_path = OUT / f"{stem}_summaries.jsonl"
    with sum_path.open("w", encoding="utf-8") as f:
        for s in summaries.values():
            f.write(s.to_jsonl() + "\n")

    print("\n=== recency #4-v2: critical_outcome by cell (mis-bind = retrieved a stale total) ===")
    by_cell: dict[str, list] = {}
    for s in summaries.values():
        by_cell.setdefault(s.cell_id or "?", []).append(s)
    for cid in sorted(by_cell, key=lambda c: (len(c), c)):
        ss = by_cell[cid]
        oc = Counter(s.critical_outcome for s in ss)
        correct = oc.get("correct-use", 0) + oc.get("re-fetch", 0)
        print(f"  {cid:26} n={len(ss)} correct={correct} mis-bind={oc.get('mis-bind', 0)} "
              f"{dict(oc)}")

    total_cost = sum(s.total_cost_usd for s in summaries.values())
    print(f"\ntotal cost: ${total_cost:.3f}  ({len(summaries)} runs)  → {sum_path}")


if __name__ == "__main__":
    main()
