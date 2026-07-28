"""Eval-driven-dev ISOLATION (Phase 2.1, B5 follow-up) — resolve the free-rewrite confound.

Free-rewrite recovered held-out selection but edited BOTH the correct tool (`search_users`) AND the
attractor (`lookup_user`). This isolates the lever with DETERMINISTIC single-clause edits (no LLM
improver → fully reproducible), appended controlled-style to the original description:

    correct_only    — add the verb "look up" to search_users' DESCRIPTION (keep its name)
    attractor_only  — disambiguate lookup_user AWAY from customers
    both            — both clauses

If `correct_only` recovers → the name-bias is beaten by describing the CORRECT tool better (the
strongest §1.10 qualification). If only `attractor_only` recovers → you must nerf the competitor.

    uv run python experiments/phase-2.1/eval_driven_isolate.py            # dry-run
    uv run python experiments/phase-2.1/eval_driven_isolate.py --go
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

from stance.eval.heldout import HELDOUT_SEEDS, selection_hit
from stance.tooluse.tasks.selection import build_selection_task
from stance.tooluse.tools import make_selection_tools

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase-2.0"))
from llm_client import LLMClient  # noqa: E402

OUT_DIR = Path("experiments/phase-2.1/results")
SYSTEM = "You are a customer-support agent. Use the available tools to handle the request."
DENSITIES = [1, 3, 5]
CORRECT_CLAUSE = " Use this to LOOK UP a customer by name."
ATTRACTOR_CLAUSE = " For internal user records only — NOT customer lookup."
ARMS: dict[str, dict[str, str]] = {
    "baseline": {},
    "correct_only": {"search_users": CORRECT_CLAUSE},
    "attractor_only": {"lookup_user": ATTRACTOR_CLAUSE},
    "both": {"search_users": CORRECT_CLAUSE, "lookup_user": ATTRACTOR_CLAUSE},
}


def first_tool(content: list[Any]) -> str | None:
    for b in content:
        if getattr(b, "type", None) == "tool_use":
            return str(b.name)
    return None


def specs_with(tools: tuple[Any, ...], appended: dict[str, str]) -> list[dict[str, Any]]:
    specs = []
    for t in tools:
        s = t.api_spec()
        if t.name in appended:
            s["description"] = t.description + appended[t.name]
        specs.append(s)
    return specs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--provider", default="deepseek")
    ap.add_argument("--model", default="deepseek-v4-flash")
    ap.add_argument("--seeds", type=int, default=len(HELDOUT_SEEDS))
    args = ap.parse_args()

    seeds = list(HELDOUT_SEEDS)[: args.seeds]
    n = len(DENSITIES) * len(seeds) * len(ARMS)
    print(f"isolate — {args.provider}/{args.model}: {n} calls "
          f"({len(DENSITIES)} densities × {len(seeds)} seeds × {len(ARMS)} arms, deterministic)")
    if not args.go:
        print("DRY-RUN — pass --go. Arms:", list(ARMS))
        return

    client = LLMClient(provider=args.provider, model=args.model)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"eval-driven-isolate-{time.strftime('%Y%m%dT%H%M%S')}.jsonl"
    acc: dict[tuple[str, int], list[int]] = defaultdict(list)
    with out.open("w", encoding="utf-8") as f:
        for d in DENSITIES:
            for s in seeds:
                world, task = build_selection_task(seed=s, density_n=d, namespaced=False)
                tools = make_selection_tools(world, d, False)
                for arm, appended in ARMS.items():
                    resp = client.complete(system=SYSTEM,
                                           messages=[{"role": "user", "content": task.prompt}],
                                           tools=specs_with(tools, appended), max_tokens=512)
                    hit = int(selection_hit(task, first_tool(resp.content)))
                    acc[(arm, d)].append(hit)
                    f.write(json.dumps({"arm": arm, "density_n": d, "seed": s, "hit": hit}) + "\n")
            print(f"  density {d} done")

    print(f"\nheld-out selection accuracy (pre-namespace) -> {out.name}")
    header = f"{'N':>3}  " + " ".join(f"{a:>14}" for a in ARMS)
    print(header)
    for d in DENSITIES:
        row = f"{d:>3}  " + " ".join(f"{mean(acc[(a, d)]):>14.2f}" for a in ARMS)
        print(row)
    print(f"\ntokens: in={client.meter.input_tokens} out={client.meter.output_tokens}")


if __name__ == "__main__":
    main()
