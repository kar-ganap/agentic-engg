"""Phase 1.1 #4-v2 (rolebind) — the DECISIVE two-phase large-N semantic role-binding test.

Compute ALL refunds → a gated get_refund_request reveals which to issue → issue it. Defeats all
three rescues the earlier nulls exposed (no shortcut/recency, large-N recall, no lexical/re-fetch
shortcut at high overlap). kind=low (distinct) is the negative control; kind=high (confusable
houseplants) is the treatment. The question: does high-overlap large-N finally collapse?

SAFE BY DEFAULT: prints the grid + cost estimate and exits unless --go is passed.

    uv run python experiments/phase-1.1/run_rolebind.py --grid pilot            # dry-run
    uv run python experiments/phase-1.1/run_rolebind.py --grid pilot --go       # control + decisive
    uv run python experiments/phase-1.1/run_rolebind.py --grid sweep --go       # kind × N
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
from stance.tooluse.tasks.rolebind import build_rolebind_task  # noqa: E402
from stance.tooluse.tools import make_rolebind_tools  # noqa: E402

OUT = Path("runs/phase-1.1/rolebind")
FILL = {"low": 0, "mid": 8_000, "high": 40_000}
SYSTEM = (
    "You are a customer-support agent. Use the available tools to complete the request exactly "
    "as instructed. When done, reply with a one-sentence confirmation and do NOT call another tool."
)


@dataclass(frozen=True)
class Cell:
    kind: str  # low (distinct, control) | high (confusable, treatment)
    n: int  # number of items (the interference count)
    fill: str

    @property
    def cell_id(self) -> str:
        return f"rolebind-k{self.kind}-n{self.n}-f{self.fill}"


def _grid(name: str) -> list[Cell]:
    if name == "pilot":  # control (low,16) / small (high,6) / DECISIVE (high,16)
        return [Cell("low", 16, "low"), Cell("high", 6, "low"), Cell("high", 16, "low")]
    if name == "sweep":  # kind × N
        return [Cell(k, n, "low") for k in ("low", "high") for n in (6, 10, 16)]
    if name == "fill":  # fill crossing at the decisive cell
        return [Cell("high", 16, f) for f in FILL]
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
        print(f"=== rolebind #4-v2: grid={args.grid} ({args.provider} {model}) — DRY RUN ===")
        for c in cells:
            print(f"  {c.cell_id}")
        est = sum((FILL[c.fill] + 40 * c.n) * (c.n + 3) for c, _ in plan)
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
        world, task = build_rolebind_task(
            seed=seed, kind=cell.kind, n_items=cell.n, fill_tokens=FILL[cell.fill]
        )
        tools = make_rolebind_tools(world, cue=task.notes["cue"])
        run_id = f"{cell.cell_id}-s{seed}"
        tasks_by_run[run_id] = task
        print(f"[{i}/{len(plan)}] {run_id} ...", end=" ", flush=True)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=model,
            complete_fn=lambda **kw: client.messages.create(**kw),
            logger=logger, refs=refs, run_id=run_id, cell_id=cell.cell_id,
            task_id="rolebind", seed=seed, terminal_style="crisp", loop_guard=True,
            max_turns=cell.n + 8, max_tokens=1024, raise_on_crash=False,
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

    print("\n=== rolebind #4-v2: critical_outcome by cell (mis-bind = wrong item's amount) ===")
    by_cell: dict[str, list] = {}
    for s in summaries.values():
        by_cell.setdefault(s.cell_id or "?", []).append(s)
    for cid in sorted(by_cell):
        ss = by_cell[cid]
        oc = Counter(s.critical_outcome for s in ss)
        correct = oc.get("correct-use", 0) + oc.get("re-fetch", 0)
        print(f"  {cid:28} n={len(ss)} correct={correct} mis-bind={oc.get('mis-bind', 0)} "
              f"{dict(oc)}")

    total_cost = sum(s.total_cost_usd for s in summaries.values())
    print(f"\ntotal cost: ${total_cost:.3f}  ({len(summaries)} runs)  → {sum_path}")


if __name__ == "__main__":
    main()
