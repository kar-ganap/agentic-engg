"""Phase 1.1 #4-v2 (diffuse) — the §1.8 LOW-discriminability test, active vs passive.

Does a weak/indirect cue (surface-luring toward same-type competitors) collapse retrieval, and
does it collapse the SAME whether the values are self-generated (active) or dumped (passive)?
Prediction: high-disc holds (control); low-disc collapses in BOTH regimes → #4 ⊆ §1.8, no
agentic immunity.

    uv run python experiments/phase-1.1/run_diffuse.py --grid pilot           # dry-run
    uv run python experiments/phase-1.1/run_diffuse.py --grid pilot --go       # control + 2 low
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
from stance.tooluse.tasks.diffuse import build_diffuse_task  # noqa: E402
from stance.tooluse.tools import make_rolebind_tools  # noqa: E402

OUT = Path("runs/phase-1.1/diffuse")
N_ITEMS = 10
SYSTEM = (
    "You are a customer-support agent. Use the available tools to complete the request exactly as "
    "instructed. When done, reply with a one-sentence confirmation and do NOT call another tool."
)


@dataclass(frozen=True)
class Cell:
    cue_disc: str  # high (distinctive, control) | low (§1.8 weak cue, treatment)
    regime: str  # active (self-fetch) | passive (dumped)

    @property
    def cell_id(self) -> str:
        return f"diffuse-{self.cue_disc}-{self.regime}-n{N_ITEMS}"


def _grid(name: str) -> list[Cell]:
    if name == "pilot":  # control / treatment(active) / treatment(passive)
        return [Cell("high", "active"), Cell("low", "active"), Cell("low", "passive")]
    if name == "full":  # add the high-disc passive cell for symmetry
        return _grid("pilot") + [Cell("high", "passive")]
    raise SystemExit(f"unknown --grid: {name!r}")


def _tools_for(world: object, cue: str, regime: str) -> tuple:
    all_tools = make_rolebind_tools(world, cue=cue)  # type: ignore[arg-type]
    if regime == "passive":  # bindings are in the prompt → only the write tool is offered
        return tuple(t for t in all_tools if t.name == "issue_refund")
    return all_tools


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--grid", default="pilot", help="pilot | full")
    p.add_argument("--go", action="store_true", help="actually run (else dry-run)")
    p.add_argument("--limit-seeds", type=int, default=len(cfg.SEEDS))
    p.add_argument("--n-seeds", type=int, default=None, help="use seeds 1..N (overrides cfg.SEEDS)")
    p.add_argument("--provider", choices=["deepseek", "anthropic"], default="deepseek")
    p.add_argument("--model", default=cfg.MODEL)
    args = p.parse_args()

    model = args.model
    if args.provider == "anthropic" and model == cfg.MODEL:
        model = "claude-sonnet-4-6"
    cells = _grid(args.grid)
    seeds = list(range(1, args.n_seeds + 1)) if args.n_seeds else cfg.SEEDS[: args.limit_seeds]
    plan = [(c, s) for c in cells for s in seeds]

    if not args.go:
        print(f"=== diffuse #4-v2: grid={args.grid} ({args.provider} {model}) — DRY RUN ===")
        for c in cells:
            print(f"  {c.cell_id}")
        est = sum((40 * N_ITEMS) * (N_ITEMS + 2) for _ in plan)
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
        world, task = build_diffuse_task(
            seed=seed, cue_disc=cell.cue_disc, regime=cell.regime,
            n_items=N_ITEMS, fill_tokens=0,
        )
        tools = _tools_for(world, task.notes["cue"], cell.regime)
        run_id = f"{cell.cell_id}-s{seed}"
        tasks_by_run[run_id] = task
        print(f"[{i}/{len(plan)}] {run_id} ...", end=" ", flush=True)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=model,
            complete_fn=lambda **kw: client.messages.create(**kw),
            logger=logger, refs=refs, run_id=run_id, cell_id=cell.cell_id,
            task_id="diffuse", seed=seed, terminal_style="crisp", loop_guard=True,
            max_turns=N_ITEMS + 8, max_tokens=1024, raise_on_crash=False,
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

    print("\n=== diffuse #4-v2: critical_outcome by cell (mis-bind = fell for a surface lure) ===")
    by_cell: dict[str, list] = {}
    for s in summaries.values():
        by_cell.setdefault(s.cell_id or "?", []).append(s)
    for cid in sorted(by_cell):
        ss = by_cell[cid]
        oc = Counter(s.critical_outcome for s in ss)
        correct = oc.get("correct-use", 0) + oc.get("re-fetch", 0)
        print(f"  {cid:30} n={len(ss)} correct={correct} mis-bind={oc.get('mis-bind', 0)} "
              f"{dict(oc)}")

    total_cost = sum(s.total_cost_usd for s in summaries.values())
    print(f"\ntotal cost: ${total_cost:.3f}  ({len(summaries)} runs)  → {sum_path}")


if __name__ == "__main__":
    main()
