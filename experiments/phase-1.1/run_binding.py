"""Phase 1.1 active-vs-passive binding A/B (the isolating test for results.md).

The #4 chain sweep returned a clean null (55/55 correct-use): under 132k burial the
agent still recalled its OWN fetched needle, because the competitors were never same-frame
rivals (presence ≠ rivalry, §0.20). This A/B isolates the mechanism by holding the needle +
the same-frame rivals fixed and varying ONLY how the needle is reached:

  passive — needle mapping is in the dumped directory; agent must FIND it (content-addressed).
  active  — needle is fetched via get_order; the SAME rival directory is burial (action-addressed).

It's a DIFFICULTY RAMP, not a single cell. The passive arm is the POSITIVE CONTROL: it must
mis-bind at some rung (else the stimulus is too easy and "active holds" means nothing, §0.20).
The finding is the DIVERGENCE — the rung where passive collapses while active still holds.

SAFE BY DEFAULT: prints the ramp + cost estimate and exits unless --go is passed.

    uv run python experiments/phase-1.1/run_binding.py                       # dry-run
    uv run python experiments/phase-1.1/run_binding.py --go --limit-seeds 2  # pilot
    uv run python experiments/phase-1.1/run_binding.py --go                  # full ramp
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
from stance.tooluse.tasks.binding import build_binding_task  # noqa: E402
from stance.tooluse.tools import make_tools  # noqa: E402

OUT = Path("runs/phase-1.1/binding")
REGIMES = ("passive", "active")
# standard ramp: (n_rivals, fill_tokens) — escalating same-frame competition + burial
LEVELS = [(5, 2_000), (15, 10_000), (30, 30_000), (60, 80_000), (100, 150_000)]
# high-length ramp: FIX rivals, vary only fill → isolates raw length/position dilution (NOT
# §1.8 competition — adjacent to §1.1). fill_tokens is my len//4 estimate; actual ≈ 0.62× it,
# so these target actual ≈ {125k, 250k, 500k, 750k, 950k} on deepseek-v4-flash (~1M window).
HIGH_LEVELS = [
    (100, 200_000), (100, 400_000), (100, 800_000), (100, 1_200_000), (100, 1_530_000)
]
SEEDS = cfg.SEEDS  # reuse the registered seeds for cross-experiment comparability
SYSTEM = (
    "You are a customer-support agent. Complete the user's request using the available "
    "tools and the information provided in the request. When the task is done, reply with a "
    "one-sentence confirmation and do NOT call another tool."
)


def _cell_id(regime: str, n_rivals: int, fill: int) -> str:
    return f"binding-{regime}-r{n_rivals}-f{fill // 1000}k"


def _tools_for(world: object, regime: str) -> list:
    all_tools = make_tools(world, "A", terminal_style="crisp")  # type: ignore[arg-type]
    keep = {"send_message"} if regime == "passive" else {"get_order", "send_message"}
    return [t for t in all_tools if t.name in keep]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--go", action="store_true", help="actually run (else dry-run: ramp + cost)")
    p.add_argument("--limit-seeds", type=int, default=len(SEEDS))
    p.add_argument("--model", default=cfg.MODEL)
    p.add_argument("--max-fill", type=int, default=10**9, help="cap fill_tokens (skip big rungs)")
    p.add_argument("--ramp", choices=["standard", "high"], default="standard")
    p.add_argument("--regimes", default="passive,active", help="comma list; passive-first: passive")
    args = p.parse_args()

    seeds = SEEDS[: args.limit_seeds]
    regimes = tuple(r for r in REGIMES if r in args.regimes.split(","))
    levels_src = HIGH_LEVELS if args.ramp == "high" else LEVELS
    levels = [(nr, f) for nr, f in levels_src if f <= args.max_fill]
    plan = [(rg, nr, f, s) for rg in regimes for (nr, f) in levels for s in seeds]

    if not args.go:
        print(f"=== binding A/B {args.ramp} ramp — DRY RUN ===")
        print(f"regimes={regimes}  levels={levels}  seeds={seeds}")
        # rough upper-bound: prompt (~fill) re-sent per turn, no cache; passive 1 turn, active 2
        est = sum(f * (1 if rg == "passive" else 2) for rg, _, f, _ in plan)
        print(f"{len(plan)} runs.  est input ≲ {est / 1e6:.1f}M tok "
              f"→ ≲ ${est / 1e6 * 0.14:.2f} (v4-flash, no-cache upper bound). Pass --go.")
        return

    import anthropic

    client = anthropic.Anthropic(
        base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
    )
    OUT.mkdir(parents=True, exist_ok=True)
    ev_path, run_path = OUT / f"{args.ramp}_events.jsonl", OUT / f"{args.ramp}_runs.jsonl"
    for fp in (ev_path, run_path):
        fp.unlink(missing_ok=True)
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    refs = RefStore(OUT / "refs")

    tasks_by_run = {}
    for n, (regime, n_rivals, fill, seed) in enumerate(plan, 1):
        world, task = build_binding_task(
            seed=seed, regime=regime, n_rivals=n_rivals, fill_tokens=fill
        )
        tools = _tools_for(world, regime)
        cell_id = _cell_id(regime, n_rivals, fill)
        run_id = f"{cell_id}-s{seed}"
        tasks_by_run[run_id] = task
        print(f"[{n}/{len(plan)}] {run_id} ...", end=" ", flush=True)
        out = run_tool_loop(
            task=task.prompt, system=SYSTEM, tools=tools, model=args.model,
            complete_fn=lambda **kw: client.messages.create(**kw),
            logger=logger, refs=refs, run_id=run_id, cell_id=cell_id,
            task_id="binding", seed=seed, terminal_style="crisp", loop_guard=True,
            max_turns=12, max_tokens=1024, raise_on_crash=False,
        )
        print(out.terminal_status)

    by_run, runs = read_runs(ev_path, run_path)
    summaries = {
        rid: score(by_run.get(rid, []), runs[rid], tasks_by_run[rid])
        for rid in runs
        if rid in tasks_by_run
    }
    sum_path = OUT / f"{args.ramp}_summaries.jsonl"
    with sum_path.open("w", encoding="utf-8") as f:
        for s in summaries.values():
            f.write(s.to_jsonl() + "\n")

    # aggregate by (regime, level), sorted by the ramp → read the divergence down the rungs
    print("\n=== binding A/B: critical_outcome by rung (passive = positive control) ===")
    by_cell: dict[tuple[str, int, int], list] = {}
    for s in summaries.values():
        iv = s.intended_ivs
        by_cell.setdefault((iv["regime"], iv["n_rivals"], iv["fill_tokens"]), []).append(s)
    print(f"  {'rung (rivals×fill)':22} {'regime':8} {'n':>3} {'correct':>8} "
          f"{'mis-bind':>9} {'other':>6}")
    for (nr, fill) in levels:
        for regime in regimes:
            ss = by_cell.get((regime, nr, fill), [])
            if not ss:
                continue
            oc = Counter(s.critical_outcome for s in ss)
            correct = oc.get("correct-use", 0) + oc.get("re-fetch", 0)
            other = len(ss) - correct - oc.get("mis-bind", 0)
            print(f"  {f'r{nr}×f{fill // 1000}k':22} {regime:8} {len(ss):>3} "
                  f"{correct:>8} {oc.get('mis-bind', 0):>9} {other:>6}")

    total_cost = sum(s.total_cost_usd for s in summaries.values())
    print(f"\ntotal cost: ${total_cost:.3f}  ({len(summaries)} runs)  → {sum_path}")


if __name__ == "__main__":
    main()
