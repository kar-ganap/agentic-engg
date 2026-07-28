"""Selection back-fill CONTROL (Phase 1.2, Thread A) — separate *count* from *lexical
verb-capture* in the pre-namespace collapse.

The main sweep (run_selection.py) showed pre-namespace selection collapses at N≥3, and
*every* wrong pick was one sibling — `lookup_user` — whose NAME lexically matches the prompt
verb ("Look up the customer …"), while the correct `search_users` carries the best-matching
*description* ("Find a customer by name") yet loses. `find_user` (shares the entity token
"user" but not the verb) never captured. So the collapse looks lexical, not count.

This control **swaps the verb-token**: the correct tool becomes `lookup_users` (now the name
matches the prompt verb) and the ex-attractor becomes `search_user`. Everything else — the
prompt, the entity-focused correct-tool description, the sibling set, the densities — is held
fixed. One conceptual factor moves: which tool NAME carries "lookup".

    PREDICTION (pre-registered): accuracy RECOVERS to >=0.8 at N=3 and N=5 (lexical hypothesis).
      recover  -> collapse is lexical verb-capture, not sibling count (a naming artifact);
      stays low -> not simple lexical matching (structural).

DV = first tool == the (swapped) expected tool. Pre-namespace only (the swap is about the
pre-namespace verb collision; namespacing already recovers to 1.00). DeepSeek-primary.

    uv run python experiments/phase-1.2/run_selection_control.py            # dry-run
    uv run python experiments/phase-1.2/run_selection_control.py --go
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

# Move the "lookup" verb-token from the ex-attractor to the correct tool. Descriptions are
# regenerated from the new name for siblings (their descs are name-derived in make_selection_tools);
# the correct tool keeps its hand-written entity-focused description (the point: only its NAME verb
# changes, its description still says "Find a customer by name").
_VERB_SWAP = {"search_users": "lookup_users", "lookup_user": "search_user"}
_CORRECT_SWAPPED = "lookup_users"


def _swap_specs(tools: Any) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for t in tools:
        s = dict(t.api_spec())
        new = _VERB_SWAP.get(s["name"])
        if new is not None:
            s["name"] = new
            if new != _CORRECT_SWAPPED:  # a sibling: keep its name-derived description shape
                s["description"] = f"Search {new.replace('_', ' ')}."
        specs.append(s)
    return specs


def first_tool(content: list[Any]) -> str | None:
    for b in content:
        if getattr(b, "type", None) == "tool_use":
            return str(b.name)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--densities", default="3,5")  # the collapse region only
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--arm-provider", default="deepseek")
    ap.add_argument("--arm-model", default="deepseek-v4-flash")
    args = ap.parse_args()

    densities = [int(x) for x in args.densities.split(",")]
    seeds = [int(x) for x in args.seeds.split(",")]
    cells = [(n, s) for n in densities for s in seeds]
    print("VERB-SWAP control (pre-namespace): correct tool -> 'lookup_users', "
          "ex-attractor -> 'search_user'")
    print(f"densities={densities} seeds={seeds} cells={len(cells)}  "
          f"{args.arm_provider}/{args.arm_model}")
    if not args.go:
        print("DRY-RUN — pass --go. Predict: recovers >=0.80 (lexical) vs baseline 0.00/0.20.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"selection-control-{time.strftime('%Y%m%dT%H%M%S')}.jsonl"
    acc: dict[int, list[int]] = defaultdict(list)
    with out.open("w", encoding="utf-8") as f:
        for i, (n, seed) in enumerate(cells, 1):
            world, task = build_selection_task(seed=seed, density_n=n, namespaced=False)
            specs = _swap_specs(make_selection_tools(world, n, False))
            client = LLMClient(provider=args.arm_provider, model=args.arm_model)
            resp = client.complete(
                system=SYSTEM, messages=[{"role": "user", "content": task.prompt}],
                tools=specs, max_tokens=512)
            picked = first_tool(resp.content)
            correct = int(picked == _CORRECT_SWAPPED)
            acc[n].append(correct)
            f.write(json.dumps({
                "density_n": n, "namespaced": False, "verb_swap": True, "seed": seed,
                "picked": picked, "expected": _CORRECT_SWAPPED, "correct": correct,
                "arm_provider": args.arm_provider, "arm_model": args.arm_model,
                "input_tokens": client.meter.input_tokens,
                "output_tokens": client.meter.output_tokens,
            }) + "\n")
            f.flush()
            print(f"[{i}/{len(cells)}] N={n} seed={seed} -> picked {picked} "
                  f"(want {_CORRECT_SWAPPED}) {'✓' if correct else '✗'}")

    print(f"\nverb-swap selection accuracy (pre-namespace) -> {out.name}")
    print(f"{'N':>3}  {'verb-swap':>10}  (baseline was N=3:0.00 N=5:0.20)")
    for n in densities:
        print(f"{n:>3}  {mean(acc[n]):>10.2f}")


if __name__ == "__main__":
    main()
