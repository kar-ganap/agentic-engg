"""Phase 1.0 context-rot run script.

Wires the real Anthropic client + the Pride & Prejudice corpus + the runner over
the run_config cells. Writes raw JSONL to runs/phase-1.0/ (gitignored). Prints a
per-cell accuracy curve + (ceiling, knee) summary after each run.

SAFE BY DEFAULT: prints the plan + cost estimate and exits unless --go is passed,
so it can't spend accidentally. Requires ANTHROPIC_API_KEY (loaded from .env).

Usage:
    uv run python experiments/phase-1.0/run.py                 # dry-run: plan + cost
    uv run python experiments/phase-1.0/run.py --item 2 --go   # run item-2 cells
    uv run python experiments/phase-1.0/run.py --go            # run all cells
    uv run python experiments/phase-1.0/run.py --summarize     # re-summarize existing runs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# run_config is a sibling module in this (non-package) experiments dir.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_config as cfg  # noqa: E402

from stance.rot.corpus import load_sentences  # noqa: E402
from stance.secrets import anthropic_api_key, deepseek_api_key  # noqa: E402
from stance.rot.runner import (  # noqa: E402
    accuracy_by_length,
    load_records,
    passband_knee,
    run_cell,
)

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "runs" / "phase-1.0"


def _model_tag(model: str) -> str:
    return model.removeprefix("claude-")


def _cell_path(cell: cfg.Cell, model: str, pool_tag: str = "") -> Path:
    tag = _model_tag(model)
    suffix = f"__{pool_tag}" if pool_tag else ""  # keeps realism runs in their own file
    return OUT_DIR / f"{cell.structure}__{cell.competition}__{cell.similarity}__{tag}{suffix}.jsonl"


def _summarize(cell: cfg.Cell, model: str, pool_tag: str = "") -> None:
    path = _cell_path(cell, model, pool_tag)
    if not path.exists():
        print(f"  (no results yet: {path.name})")
        return
    curve = accuracy_by_length(load_records(path))
    ceiling, knee = passband_knee(curve)
    pts = "  ".join(f"{t//1000}k:{a:.2f}" for t, a in curve)
    knee_s = f"{knee // 1000}k" if knee else "none (full passband)"
    print(f"  {cell.competition:10} sim={cell.similarity:4} ceiling={ceiling:.2f} knee={knee_s}")
    print(f"      {pts}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--item", help="only cells for this backlog item (e.g. 2)")
    p.add_argument("--competition", help="only cells with this competition (neutral/localized/diffuse)")
    p.add_argument("--similarity", help="only cells with this needle-question similarity (high/low)")
    p.add_argument("--go", action="store_true", help="actually run (else dry-run)")
    p.add_argument("--summarize", action="store_true", help="summarize existing runs and exit")
    p.add_argument("--max-seeds", type=int, default=None, help="use only the first N seeds")
    p.add_argument("--max-len", type=int, default=None, help="cap target length (tokens)")
    p.add_argument("--model", default=cfg.MODEL_PRIMARY)
    p.add_argument(
        "--provider", choices=["anthropic", "deepseek"], default="anthropic",
        help="completion provider; 'deepseek' uses the Anthropic-compatible endpoint "
        "(same message format) but counts tokens on Anthropic-Haiku for a consistent "
        "cross-provider x-axis. See docs/phases/phase-1.0-extension-plan.md.",
    )
    p.add_argument(
        "--competitor-pool",
        help="path to a pinned JSON pool of competitor lines (realism check); "
        "diffuse competitors are sampled from it instead of templated. Output goes "
        "to a pool-tagged file so it never overwrites the templated run.",
    )
    args = p.parse_args()

    # DeepSeek defaults to the v4-flash workhorse unless --model overrides.
    if args.provider == "deepseek" and args.model == cfg.MODEL_PRIMARY:
        args.model = "deepseek-v4-flash"

    pool: list[str] | None = None
    pool_tag = ""
    if args.competitor_pool:
        pool_path = Path(args.competitor_pool)
        pool = json.loads(pool_path.read_text())["competitors"]
        pool_tag = pool_path.stem  # e.g. realism_v1 → distinguishes the output file

    cells = [
        c
        for c in cfg.CELLS
        if (args.item is None or c.item == args.item)
        and (args.competition is None or c.competition == args.competition)
        and (args.similarity is None or c.similarity == args.similarity)
    ]
    seeds = list(cfg.SEEDS[: args.max_seeds]) if args.max_seeds else list(cfg.SEEDS)
    lengths = [n for n in cfg.LENGTHS if args.max_len is None or n <= args.max_len]

    if args.summarize:
        for c in cells:
            _summarize(c, args.model)
        return

    runs = len(cells) * len(lengths) * len(cfg.DEPTHS) * len(seeds)
    input_tokens = len(cells) * len(cfg.DEPTHS) * len(seeds) * sum(lengths)
    try:  # provider-accurate estimate from the pinned price table
        from stance.instrumentation.pricing import cost as _cost  # noqa: PLC0415

        est = _cost(args.model, input_tokens=input_tokens)
    except KeyError:  # unknown model → fall back to the flat Haiku-tier estimate
        est = input_tokens / 1_000_000 * cfg.INPUT_USD_PER_MTOK
    print(f"cells: {len(cells)}  runs: {runs}  seeds: {seeds}  model: {args.model}")
    for c in cells:
        print(f"  [item {c.item}] {c.structure:16} {c.competition:10} sim={c.similarity}")
    print(f"est. input cost: ${est:.2f}  (budget ${cfg.BUDGET_USD:.0f})")

    if not args.go:
        print("\n(dry-run — pass --go to execute)")
        return

    import anthropic

    # Keys strictly from .env (never the shell) — see stance.secrets / CLAUDE.md.
    if args.provider == "deepseek":
        # Complete on DeepSeek's Anthropic-compatible endpoint (same message format,
        # so the whole pipeline is reused). Count on Anthropic-Haiku so the x-axis is
        # one consistent tokenizer across providers (the DeepSeek endpoint has no
        # count_tokens). See docs/phases/phase-1.0-extension-plan.md.
        ds_client = anthropic.Anthropic(
            base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
        )
        count_client = anthropic.Anthropic(api_key=anthropic_api_key())

        def complete(**kw: object) -> object:
            return ds_client.messages.create(**kw)

        def count(**kw: object) -> int:
            ckw = {**kw, "model": cfg.MODEL_PRIMARY}  # count on Haiku, not the DeepSeek model
            return count_client.messages.count_tokens(**ckw).input_tokens
    else:
        client = anthropic.Anthropic(api_key=anthropic_api_key())

        def complete(**kw: object) -> object:
            return client.messages.create(**kw)

        def count(**kw: object) -> int:
            return client.messages.count_tokens(**kw).input_tokens

    filler = load_sentences()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for c in cells:
        path = _cell_path(c, args.model, pool_tag)
        if path.exists():
            path.unlink()  # fresh run per cell (avoid append-dup on re-run)
        n = run_cell(
            structure=c.structure,
            competition=c.competition,
            similarity=c.similarity,
            model=args.model,
            lengths=lengths,
            depths=cfg.DEPTHS,
            seeds=seeds,
            complete_fn=complete,
            count_fn=count,
            out_path=path,
            filler_sentences=filler if c.structure == "clean_essay" else None,
            competitor_pool=pool,
        )
        total += n
        print(f"\n[{c.structure} {c.competition} sim={c.similarity}] {n} runs -> {path.name}")
        _summarize(c, args.model, pool_tag)
    print(f"\ntotal runs: {total}")


if __name__ == "__main__":
    main()
