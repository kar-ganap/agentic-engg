"""Eval-driven tool-development (Phase 2.1, B5; Module 6 L88 × §1.10 follow-up).

Can DESCRIPTION-refinement overcome the §1.10 name-bias? §1.10: for "Look up the customer NAME"
requests the agent picks `lookup_user` (name matches the verb) over the correct `search_users`
(whose DESCRIPTION is the best match). The verb-swap control recovered by RENAMING; here we instead
improve the DESCRIPTION (keep the name) and measure on the HELD-OUT set.

Loop: training baseline (confirm the collapse + observe failures) → an improver LLM rewrites the
descriptions (free arm) / appends a disambiguating clause (controlled arm) → re-eval on held-out.
DV = deterministic first-tool selection. DeepSeek-primary. Pre-reg: prereg-eval-driven-dev.md.

    uv run python experiments/phase-2.1/eval_driven_dev.py            # dry-run
    uv run python experiments/phase-2.1/eval_driven_dev.py --go
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from stance.eval.heldout import HELDOUT_SEEDS, selection_hit
from stance.tools import Tool
from stance.tooluse.tasks.base import TaskInstance
from stance.tooluse.tasks.selection import build_selection_task
from stance.tooluse.tools import make_selection_tools

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase-2.0"))
from llm_client import LLMClient  # noqa: E402

OUT_DIR = Path("experiments/phase-2.1/results")
SYSTEM = "You are a customer-support agent. Use the available tools to handle the request."
CORRECT, ATTRACTOR = "search_users", "lookup_user"
TRAIN_SEEDS = [1, 2, 3, 4, 5]
CLASH_DENSITIES = [3, 5]        # where §1.10 collapses (the improver's failure signal)
HELDOUT_DENSITIES = [1, 3, 5]   # 1 = no-clash control (must stay ≥0.80)

IMPROVER_SYS = {
    "free": ("You optimize tool descriptions so an agent selects the correct tool. Rewrite each "
             "description freely, one line each. Do NOT rename tools."),
    "controlled": ("You may ONLY append one short disambiguating clause to each description; "
                   "do not change the existing text. Output NONE for tools that need no clause."),
}


def first_tool(content: list[Any]) -> str | None:
    for b in content:
        if getattr(b, "type", None) == "tool_use":
            return str(b.name)
    return None


def pick(client: LLMClient, task: TaskInstance, specs: list[dict[str, Any]]) -> str | None:
    resp = client.complete(system=SYSTEM, messages=[{"role": "user", "content": task.prompt}],
                           tools=specs, max_tokens=512)
    return first_tool(resp.content)


def _parse_overrides(text: str, names: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^[\s*>#-]*([A-Za-z_]+)\s*:\s*(.+)", line)
        if m and m.group(1) in names:
            out[m.group(1)] = m.group(2).strip(" *")
    return out


def improve(
    client: LLMClient, tools: tuple[Tool, ...], mode: str, k: int, n: int
) -> tuple[dict[str, str], str]:
    names = {t.name for t in tools}
    toolset = "\n".join(f"{t.name}: {t.description}" for t in tools)
    instr = (
        f"Rewrite the descriptions so the agent picks `{CORRECT}` for customer lookups. Output "
        "one line per tool:\nTOOLNAME: <new description>"
        if mode == "free"
        else "For each tool, output one line and NOTHING else — a short clause to append that "
             "disambiguates it, or the word NONE:\nTOOLNAME: <clause or NONE>"
    )
    user = (
        f"Toolset (name: current description):\n{toolset}\n\n"
        f"EVAL FAILURE: for 'Look up the customer NAME' requests, the correct tool is `{CORRECT}` "
        f"but the agent called `{ATTRACTOR}` in {k}/{n} cases — it matches the tool NAME to "
        f"the request verb ('look up') and ignores the description.\n\n{instr}"
    )
    resp = client.complete(system=IMPROVER_SYS[mode],
                           messages=[{"role": "user", "content": user}], max_tokens=1024)
    text = "".join(getattr(b, "text", "") for b in resp.content
                   if getattr(b, "type", None) == "text")
    return _parse_overrides(text, names), text


def specs_with(
    tools: tuple[Tool, ...], overrides: dict[str, str], mode: str
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for t in tools:
        s = t.api_spec()
        clause = overrides.get(t.name, "")
        if clause and clause.upper() != "NONE":
            s["description"] = clause if mode == "free" else f"{t.description} {clause}"
        specs.append(s)
    return specs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="actually call the API (default: dry-run)")
    ap.add_argument("--provider", default="deepseek")
    ap.add_argument("--model", default="deepseek-v4-flash")
    ap.add_argument("--heldout-seeds", type=int, default=len(HELDOUT_SEEDS))
    args = ap.parse_args()

    hseeds = list(HELDOUT_SEEDS)[: args.heldout_seeds]
    n_train = len(CLASH_DENSITIES) * len(TRAIN_SEEDS)
    n_eval = len(HELDOUT_DENSITIES) * len(hseeds) * 3
    print(f"eval-driven-dev — {args.provider}/{args.model}   (pre-reg: prereg-eval-driven-dev.md)")
    print(f"  training: {n_train} calls (seeds {TRAIN_SEEDS} × densities {CLASH_DENSITIES})")
    print("  improver:          2 calls (free + controlled)")
    print(f"  held-out eval:     {n_eval} calls "
          f"({len(HELDOUT_DENSITIES)} densities × {len(hseeds)} seeds × 3 arms)")
    if not args.go:
        print("DRY-RUN — pass --go. DV = first tool == search_users (deterministic).")
        return

    client = LLMClient(provider=args.provider, model=args.model)

    # 1. training baseline — confirm collapse + count the attractor captures
    captured, total = 0, 0
    for d in CLASH_DENSITIES:
        for s in TRAIN_SEEDS:
            world, task = build_selection_task(seed=s, density_n=d, namespaced=False)
            specs = [x.api_spec() for x in make_selection_tools(world, d, False)]
            picked = pick(client, task, specs)
            total += 1
            captured += int(picked == ATTRACTOR)
    print(f"\ntraining: `{ATTRACTOR}` captured {captured}/{total} (confirms §1.10 collapse)")

    # 2. improver on the full (density-5) pre-namespace toolset
    world5, _ = build_selection_task(seed=TRAIN_SEEDS[0], density_n=5, namespaced=False)
    full_tools = make_selection_tools(world5, 5, False)
    overrides: dict[str, dict[str, str]] = {}
    raw: dict[str, str] = {}
    for m in ("free", "controlled"):
        overrides[m], raw[m] = improve(client, full_tools, m, captured, total)
        print(f"\n[{m}] overrides ({len(overrides[m])} tools):")
        for name, txt in overrides[m].items():
            print(f"    {name}: {txt}")
        if not overrides[m]:
            print(f"    (no parseable overrides; raw head: {raw[m][:100]!r})")

    # 3. held-out eval — baseline vs free vs controlled (DV = selection_hit)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"eval-driven-dev-{time.strftime('%Y%m%dT%H%M%S')}.jsonl"
    acc: dict[tuple[str, int], list[int]] = defaultdict(list)
    with out.open("w", encoding="utf-8") as f:
        meta = {"meta": "overrides", "training_capture": f"{captured}/{total}",
                "free": overrides["free"], "controlled": overrides["controlled"],
                "raw_free": raw["free"], "raw_controlled": raw["controlled"]}
        f.write(json.dumps(meta) + "\n")
        for d in HELDOUT_DENSITIES:
            for s in hseeds:
                world, task = build_selection_task(seed=s, density_n=d, namespaced=False)
                tools = make_selection_tools(world, d, False)
                arms = {
                    "baseline": [x.api_spec() for x in tools],
                    "free": specs_with(tools, overrides["free"], "free"),
                    "controlled": specs_with(tools, overrides["controlled"], "controlled"),
                }
                for arm, specs in arms.items():
                    picked = pick(client, task, specs)
                    hit = int(selection_hit(task, picked))
                    acc[(arm, d)].append(hit)
                    f.write(json.dumps({"arm": arm, "density_n": d, "seed": s, "picked": picked,
                                        "expected": task.expected_tool, "hit": hit}) + "\n")
            print(f"  density {d} done")

    print(f"\nheld-out selection accuracy (pre-namespace) -> {out.name}")
    print(f"{'N':>3}  {'baseline':>9} {'free':>9} {'controlled':>11}")
    for d in HELDOUT_DENSITIES:
        row = tuple(mean(acc[(a, d)]) for a in ("baseline", "free", "controlled"))
        print(f"{d:>3}  {row[0]:>9.2f} {row[1]:>9.2f} {row[2]:>11.2f}")
    print(f"\ntokens: in={client.meter.input_tokens} out={client.meter.output_tokens}")


if __name__ == "__main__":
    main()
