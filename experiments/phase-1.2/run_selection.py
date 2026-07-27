"""§2/#2 tool-selection back-fill (Phase 1.2, Thread A) — the Module-2 named central exercise
(built as `tasks/selection.py` in Phase 1.1, pre-registered as position #2, never run).

DV = the model's FIRST tool choice vs `expected_tool` (selection accuracy) — a single model call per
task, no loop needed. Sweep density_n × {pre-, post-namespace} × seeds. Pre-registered design
(phase-1.1-plan §293): N∈{0,1,3,5}. Safe-by-default; --go to spend. DeepSeek-primary.

    uv run python experiments/phase-1.2/run_selection.py            # dry-run plan
    uv run python experiments/phase-1.2/run_selection.py --go
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from stance.tooluse.tasks.selection import build_selection_task
from stance.tooluse.tools import make_selection_tools

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase-2.0"))
from llm_client import LLMClient  # noqa: E402

OUT_DIR = Path("experiments/phase-1.2/results")
SYSTEM = "You are a customer-support agent. Use the available tools to handle the request."


def first_tool(content: list[Any]) -> str | None:
    for b in content:
        if getattr(b, "type", None) == "tool_use":
            return str(b.name)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--densities", default="0,1,3,5")  # pre-registered N (max 5 = sibling list)
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--go", action="store_true", help="actually call the API (default: dry-run)")
    ap.add_argument("--arm-provider", default="deepseek")
    ap.add_argument("--arm-model", default="deepseek-v4-flash")
    args = ap.parse_args()

    densities = [int(x) for x in args.densities.split(",")]
    seeds = [int(x) for x in args.seeds.split(",")]
    cells = [(n, ns, s) for n in densities for ns in (False, True) for s in seeds]
    print(f"densities={densities} namespaced={{False,True}} seeds={seeds}")
    print(f"cells={len(cells)} (density × namespace × seed), 1 call each   "
          f"{args.arm_provider}/{args.arm_model}")
    if not args.go:
        print("DRY-RUN — pass --go. DV = first tool == expected_tool (selection accuracy).")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"selection-{time.strftime('%Y%m%dT%H%M%S')}.jsonl"
    acc: dict[tuple[int, bool], list[int]] = defaultdict(list)
    with out.open("w", encoding="utf-8") as f:
        for i, (n, ns, seed) in enumerate(cells, 1):
            world, task = build_selection_task(seed=seed, density_n=n, namespaced=ns)
            specs = [t.api_spec() for t in make_selection_tools(world, n, ns)]
            client = LLMClient(provider=args.arm_provider, model=args.arm_model)
            resp = client.complete(
                system=SYSTEM, messages=[{"role": "user", "content": task.prompt}],
                tools=specs, max_tokens=512)
            picked = first_tool(resp.content)
            correct = int(picked == task.expected_tool)
            acc[(n, ns)].append(correct)
            f.write(json.dumps({
                "density_n": n, "namespaced": ns, "seed": seed, "picked": picked,
                "expected": task.expected_tool, "correct": correct,
                "arm_provider": args.arm_provider, "arm_model": args.arm_model,
                "input_tokens": client.meter.input_tokens,
                "output_tokens": client.meter.output_tokens,
            }) + "\n")
            f.flush()
            print(f"[{i}/{len(cells)}] N={n} ns={ns} seed={seed} -> picked {picked} "
                  f"(want {task.expected_tool}) {'✓' if correct else '✗'}")

    print(f"\nselection accuracy (DV) by density × namespace -> {out.name}")
    print(f"{'N':>3}  {'pre-namespace':>14}  {'post-namespace':>15}")
    for n in densities:
        pre = mean(acc[(n, False)]) if acc[(n, False)] else float("nan")
        post = mean(acc[(n, True)]) if acc[(n, True)] else float("nan")
        print(f"{n:>3}  {pre:>14.2f}  {post:>15.2f}")


if __name__ == "__main__":
    main()
