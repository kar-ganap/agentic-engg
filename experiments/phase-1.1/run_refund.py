"""Phase 1.1 #4-v2 — self-generated semantic role-binding interference (refund tier).

The agent computes a distinct refund per item (apply_adjustment), then must route the right
amount to a referent named by a PARAPHRASE cue. Co-primary axes: referent **overlap** × **N**,
crossed with **fill**; the **return-shape** lever (R0/R1/R2) and a **doc-quality** arm test the
#4ii fix-vs-description ordering. DV = correct-use / re-fetch / mis-bind / fabricate / error.

SAFE BY DEFAULT: prints the grid + cost estimate and exits unless --go is passed.

    uv run python experiments/phase-1.1/run_refund.py --grid pilot                 # dry-run
    uv run python experiments/phase-1.1/run_refund.py --grid pilot --go            # control corners
    uv run python experiments/phase-1.1/run_refund.py --grid plane --go            # overlap×N
    uv run python experiments/phase-1.1/run_refund.py --grid shape --go            # shape×doc
    uv run python experiments/phase-1.1/run_refund.py --grid plane --provider anthropic \
        --model claude-sonnet-4-6 --limit-seeds 2 --go                             # Claude anchor
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
from stance.tooluse.tasks.refund import build_refund_task  # noqa: E402
from stance.tooluse.tools import make_refund_tools  # noqa: E402

OUT = Path("runs/phase-1.1/refund")
N_LEVELS = {"small": 3, "med": 5, "large": 6}  # pools have 6 (extend them for larger N)
FILL = {"low": 0, "mid": 8_000, "high": 40_000}
SYSTEM = (
    "You are a customer-support agent. Use the available tools to complete the request. "
    "Compute each item's refund with apply_adjustment before issuing the one requested. When "
    "done, reply with a one-sentence confirmation and do NOT call another tool."
)


@dataclass(frozen=True)
class Cell:
    kind: str  # low | mid | high (semantic magnitude) | lure | mixed (lexical×semantic 2×2)
    n: str  # small | med | large
    fill: str  # low | mid | high
    return_shape: str  # flat | tagged | structured
    doc: str  # terse | verbose

    @property
    def cell_id(self) -> str:
        return f"refund-k{self.kind}-n{self.n}-f{self.fill}-{self.return_shape}-{self.doc}"


def _grid(name: str) -> list[Cell]:
    """Scoped cells (NOT full factorial). The knee cell (high kind, med N, mid fill) anchors the
    deconfound/shape/fill slices; the control corners gate interpretation (§0.20/§0.21)."""
    if name == "pilot":  # negative control (must hold) / positive (must collapse) / lure probe
        return [
            Cell("low", "small", "mid", "flat", "terse"),
            Cell("high", "large", "mid", "flat", "terse"),
            Cell("lure", "large", "mid", "flat", "terse"),
        ]
    if name == "plane":  # semantic magnitude × N at fixed fill/shape/doc
        return [
            Cell(k, n, "mid", "flat", "terse")
            for k in ("low", "mid", "high")
            for n in N_LEVELS
        ]
    if name == "deconfound":  # lexical × semantic at the knee: is the collapse meaning or surface?
        return [Cell(k, "med", "mid", "flat", "terse") for k in ("high", "lure", "mixed")]
    if name == "shape":  # return-shape × doc-quality at the knee cell (#4ii ordering)
        return [
            Cell("high", "med", "mid", rs, dq)
            for rs in ("flat", "tagged", "structured")
            for dq in ("terse", "verbose")
        ]
    if name == "fill":  # fill crossing at one kind×N
        return [Cell("high", "med", f, "flat", "terse") for f in FILL]
    if name == "all":
        return _grid("plane") + _grid("deconfound") + _grid("shape") + _grid("fill")
    raise SystemExit(f"unknown --grid: {name!r}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--grid", default="pilot", help="pilot|plane|deconfound|shape|fill|all")
    p.add_argument("--go", action="store_true", help="actually run (else dry-run: grid + cost)")
    p.add_argument("--limit-seeds", type=int, default=len(cfg.SEEDS))
    p.add_argument("--provider", choices=["deepseek", "anthropic"], default="deepseek")
    p.add_argument("--model", default=cfg.MODEL)
    args = p.parse_args()

    model = args.model
    if args.provider == "anthropic" and model == cfg.MODEL:
        model = "claude-sonnet-4-6"  # the cross-provider anchor default
    cells = _grid(args.grid)
    seeds = cfg.SEEDS[: args.limit_seeds]
    plan = [(c, s) for c in cells for s in seeds]

    if not args.go:
        print(f"=== refund #4-v2: grid={args.grid} ({args.provider} {model}) — DRY RUN ===")
        for c in cells:
            print(f"  {c.cell_id}  (N={N_LEVELS[c.n]}, fill={FILL[c.fill]})")
        # rough upper bound: prompt (~fill) re-sent per turn (~N+2), no cache
        est = sum((FILL[c.fill] + 200 * N_LEVELS[c.n]) * (N_LEVELS[c.n] + 2) for c, _ in plan)
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
        world, task = build_refund_task(
            seed=seed, kind=cell.kind, n_items=N_LEVELS[cell.n], fill_tokens=FILL[cell.fill]
        )
        tools = make_refund_tools(world, return_shape=cell.return_shape, doc_quality=cell.doc)
        run_id = f"{cell.cell_id}-s{seed}"
        tasks_by_run[run_id] = task
        print(f"[{i}/{len(plan)}] {run_id} ...", end=" ", flush=True)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=model,
            complete_fn=lambda **kw: client.messages.create(**kw),
            logger=logger, refs=refs, run_id=run_id, cell_id=cell.cell_id,
            task_id="refund", seed=seed, terminal_style="crisp", loop_guard=True,
            max_turns=24, max_tokens=1024, raise_on_crash=False,
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

    print("\n=== refund #4-v2: critical_outcome by cell ===")
    by_cell: dict[str, list] = {}
    for s in summaries.values():
        by_cell.setdefault(s.cell_id or "?", []).append(s)
    for cid in sorted(by_cell):
        ss = by_cell[cid]
        oc = Counter(s.critical_outcome for s in ss)
        correct = oc.get("correct-use", 0) + oc.get("re-fetch", 0)
        print(f"  {cid:42} n={len(ss)} correct={correct} mis-bind={oc.get('mis-bind', 0)} "
              f"{dict(oc)}")

    total_cost = sum(s.total_cost_usd for s in summaries.values())
    print(f"\ntotal cost: ${total_cost:.3f}  ({len(summaries)} runs)  → {sum_path}")


if __name__ == "__main__":
    main()
