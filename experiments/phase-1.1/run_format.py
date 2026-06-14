"""Phase 1.1 #6 — return-format policy: expose the choice (C) vs fix it (A/B/D)?

Task: get_order → (review ticket history if high-fill) → send_message(account_id). The downstream
send NEEDS the account handle that get_order returns, so the return-format arm gates success:
  A detailed (ids inline) · B concise (ids omitted → floor) · C agent-chooses · D handle-block.
DV = success-vs-tokens frontier per arm; for C also the format-choice accuracy + re-fetch rate.

SAFE BY DEFAULT: prints the grid + cost estimate and exits unless --go is passed.

    uv run python experiments/phase-1.1/run_format.py --limit-seeds 1            # dry-run
    uv run python experiments/phase-1.1/run_format.py --limit-seeds 1 --go       # 8-run pilot
    uv run python experiments/phase-1.1/run_format.py --arms A,C,D --go          # full (5 seeds)
    # Claude anchor: --arms C,D --fill high --provider anthropic --limit-seeds 3 --go
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
from stance.tooluse.tasks.format import build_format_task  # noqa: E402
from stance.tooluse.tools import make_tools  # noqa: E402

OUT = Path("runs/phase-1.1/format")
FILL = {"low": 0, "mid": 3_000, "high": 9_000}  # low=bare; mid/high=3-ticket review sized to this
SYSTEM = (
    "You are a customer-support agent. Complete the user's request using the available tools. "
    "The order id is given in the request. When the task is done, reply with a one-sentence "
    "confirmation and do NOT call another tool."
)


@dataclass(frozen=True)
class Cell:
    arm: str  # A detailed | B concise (floor) | C agent-choice | D handle-block
    fill: str  # low | high

    @property
    def cell_id(self) -> str:
        return f"format-{self.arm}-f{self.fill}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arms", default="A,B,C,D", help="comma list of arms to run")
    p.add_argument("--fill", default="low,mid,high", help="comma list of fill levels")
    p.add_argument("--go", action="store_true", help="actually run (else dry-run)")
    p.add_argument("--limit-seeds", type=int, default=len(cfg.SEEDS))
    p.add_argument("--provider", choices=["deepseek", "anthropic"], default="deepseek")
    p.add_argument("--model", default=cfg.MODEL)
    args = p.parse_args()

    model = args.model
    if args.provider == "anthropic" and model == cfg.MODEL:
        model = "claude-sonnet-4-6"
    arms = [a for a in args.arms.split(",") if a]
    fills = [f for f in args.fill.split(",") if f]
    cells = [Cell(a, f) for a in arms for f in fills]
    seeds = cfg.SEEDS[: args.limit_seeds]
    plan = [(c, s) for c in cells for s in seeds]

    if not args.go:
        print(f"=== #6 return-format: ({args.provider} {model}) — DRY RUN ===")
        for c in cells:
            print(f"  {c.cell_id}")
        est = sum((FILL[c.fill] + 2_000) * 8 for c, _ in plan)  # ~8 turns, rough
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
    ev_path, run_path = OUT / f"{tag}_events.jsonl", OUT / f"{tag}_runs.jsonl"
    for fp in (ev_path, run_path):
        fp.unlink(missing_ok=True)
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    refs = RefStore(OUT / "refs")

    tasks_by_run = {}
    for i, (cell, seed) in enumerate(plan, 1):
        world, task = build_format_task(seed=seed, arm=cell.arm, fill_tokens=FILL[cell.fill])
        tools = make_tools(world, cell.arm, terminal_style="crisp")
        run_id = f"{cell.cell_id}-s{seed}"
        tasks_by_run[run_id] = task
        print(f"[{i}/{len(plan)}] {run_id} ...", end=" ", flush=True)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=model,
            complete_fn=lambda **kw: client.messages.create(**kw),
            logger=logger, refs=refs, run_id=run_id, cell_id=cell.cell_id,
            task_id="format", seed=seed, terminal_style="crisp", loop_guard=True,
            max_turns=12, max_tokens=1024, raise_on_crash=False,
        )
        print(out.terminal_status)

    by_run, runs = read_runs(ev_path, run_path)
    summaries = {
        rid: score(by_run.get(rid, []), runs[rid], tasks_by_run[rid])
        for rid in runs
        if rid in tasks_by_run
    }
    sum_path = OUT / f"{tag}_summaries.jsonl"
    with sum_path.open("w", encoding="utf-8") as f:
        for s in summaries.values():
            f.write(s.to_jsonl() + "\n")

    print("\n=== #6 return-format: success-vs-tokens by arm ===")
    print(f"  {'cell':16} {'n':>2} {'success':>8} {'~tokens':>8}  outcomes")
    by_cell: dict[str, list] = {}
    for s in summaries.values():
        by_cell.setdefault(s.cell_id or "?", []).append(s)
    for cid in sorted(by_cell):
        ss = by_cell[cid]
        succ = sum(1 for s in ss if s.success)
        toks = sum(s.total_tokens for s in ss) / len(ss)
        oc = Counter(s.critical_outcome for s in ss)
        print(f"  {cid:16} {len(ss):>2} {succ}/{len(ss):<6} {toks / 1e3:>6.1f}k  {dict(oc)}")

    # C-arm mechanism: format-choice accuracy + re-fetch (from the get_order calls)
    print("\n=== C arm: get_order format choices (the choice-quality mechanism) ===")
    for cid in sorted(c for c in by_cell if c.startswith("format-C-")):
        rids = [r for r in by_run if r.startswith(cid)]
        choices: Counter[str] = Counter()
        getorders = 0
        for rid in rids:
            for e in by_run[rid]:
                if e.is_tool_call and e.tool_called == "get_order":
                    getorders += 1
                    choices[(e.arguments or {}).get("response_format") or "(unset)"] += 1
        n = len(rids)
        print(f"  {cid:16} get_order calls={getorders} (~{getorders / max(n, 1):.1f}/run) "
              f"choices={dict(choices)}")

    total_cost = sum(s.total_cost_usd for s in summaries.values())
    print(f"\ntotal cost: ${total_cost:.3f}  ({len(summaries)} runs)  → {sum_path}")


if __name__ == "__main__":
    main()
