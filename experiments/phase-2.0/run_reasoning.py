"""Thread-B runner: sweep (pool x size x confusability x seed), PAIRED (all arms on the same task),
grade each with the Sonnet judge, append one row per run. Safe-by-default: prints the plan unless
--go. DeepSeek-primary arms, Sonnet-anchored judge (§0.8).

    uv run python experiments/phase-2.0/run_reasoning.py                       # dry-run plan
    uv run python experiments/phase-2.0/run_reasoning.py --arms react --seeds 1 --sizes 1 --go
    uv run python experiments/phase-2.0/run_reasoning.py --pools signal-density --sizes 1,4 --go
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from stance.graph.store import GraphStore
from stance.reasoning.arms import ARMS, ArmResult
from stance.reasoning.grader import GradeResult, grade
from stance.reasoning.sampler import build_task

sys.path.insert(0, str(Path(__file__).parent))
import pool_capability_failuremode as _cap  # noqa: E402
import pool_signal_density as _sig  # noqa: E402
import pool_tool_stability as _tool  # noqa: E402
from llm_client import LLMClient  # noqa: E402

POOLS = {m.POOL.id: m.POOL for m in (_sig, _tool, _cap)}
GRAPH_DIR = Path("data/graph")
OUT_DIR = Path("experiments/phase-2.0/results")
ARM_MODEL = "deepseek-v4-flash"      # substrate primary; v4-pro for capability-sensitive cells
JUDGE_MODEL = "claude-sonnet-5"       # anchor: grading noise feeds the DV (§0.8)


def cells(pools: list[str], sizes: list[int], confs: list[str],
          seeds: list[int]) -> Iterator[tuple[str, int, str, int]]:
    """One (pool, size, conf, seed) = one task; every arm runs on it (paired)."""
    for pid in pools:
        for size in sizes:
            for conf in confs:
                for seed in seeds:
                    yield pid, size, conf, seed


def row(pid: str, arm: str, size: int, conf: str, seed: int,
        result: ArmResult, gr: GradeResult, judge_meter: Any) -> dict[str, Any]:
    p = result.position
    return {
        "pool": pid, "arm": arm, "n_distractors": size, "confusability": conf, "seed": seed,
        "stance": p.stance, "confidence": p.confidence, "retraction": p.retraction,
        "evidence_used": list(p.evidence_used), "raw": p.raw,  # full final answer, for audit
        "trace": result.trace,  # intermediate reasoning (plan_execute's plan) — audit gap fix
        "arm_input_tokens": result.input_tokens, "arm_output_tokens": result.output_tokens,
        "arm_cache_read_tokens": result.cache_read_tokens, "n_calls": result.n_calls,
        "n_reads": result.n_reads, "n_turns": result.n_turns,
        "latency_s": round(result.latency_s, 2),
        "judge_input_tokens": judge_meter.input_tokens,
        "judge_output_tokens": judge_meter.output_tokens,
        "grade_total": gr.total, "grade_parsed_ok": gr.parsed_ok, "grade_rationale": gr.rationale,
        "judge_raw": gr.raw,  # full judge output, for audit
        **{f"grade_{k}": v for k, v in gr.scores.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", default="signal-density")
    ap.add_argument("--arms", default="baseline,react,plan_execute,reflection")
    ap.add_argument("--sizes", default="1,4")
    ap.add_argument("--confusability", default="high")
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--go", action="store_true", help="actually call the API (default: dry-run)")
    ap.add_argument("--arm-provider", default="deepseek")
    ap.add_argument("--arm-model", default=ARM_MODEL)
    ap.add_argument("--judge-model", default=JUDGE_MODEL)
    args = ap.parse_args()

    pools = args.pools.split(",")
    arms = args.arms.split(",")
    sizes = [int(x) for x in args.sizes.split(",")]
    confs = args.confusability.split(",")
    seeds = [int(x) for x in args.seeds.split(",")]
    plan = list(cells(pools, sizes, confs, seeds))
    n_runs = len(plan) * len(arms)

    print(f"pools={pools} arms={arms} sizes={sizes} conf={confs} seeds={seeds}")
    print(f"tasks={len(plan)}  runs (task x arm)={n_runs}  grades={n_runs}")
    print(f"arms: {args.arm_provider}/{args.arm_model}   judge: {args.judge_model}")
    if not args.go:
        print("DRY-RUN — pass --go to spend. (react/reflection are multi-call; baseline=1 call.)")
        return

    g = GraphStore(GRAPH_DIR).load()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"reasoning-{time.strftime('%Y%m%dT%H%M%S')}.jsonl"
    n = 0
    with out.open("w", encoding="utf-8") as f:
        for pid, size, conf, seed in plan:
            task = build_task(POOLS[pid], g, n_distractors=size, confusability=conf, seed=seed)
            for arm_name in arms:
                client = LLMClient(provider=args.arm_provider, model=args.arm_model)
                result = ARMS[arm_name](task, client)
                judge = LLMClient(provider="anthropic", model=args.judge_model)  # fresh per grade
                gr = grade(task, result, judge)
                f.write(json.dumps(row(pid, arm_name, size, conf, seed, result, gr, judge.meter)))
                f.write("\n")
                f.flush()
                n += 1
                print(f"[{n}/{n_runs}] {pid:<16} {arm_name:<12} size={size} seed={seed} "
                      f"-> {gr.total:>2}/20  conf={result.position.confidence} "
                      f"reads={result.n_reads} calls={result.n_calls}")
    print(f"wrote {n} rows -> {out}")


if __name__ == "__main__":
    main()
