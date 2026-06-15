"""Phase 1.1 — minimal end-to-end smoke: one #4 chain cell on real DeepSeek.

Wires the whole pipeline — build_chain_task → make_tools → run_tool_loop(real
DeepSeek compat endpoint) → score — on a single cheap cell (~$0.01). Validates the
loop/staging/scorer against a FREE agent (not a fake). Key strictly from .env.
raise_on_crash=True so any pipeline bug surfaces. Writes raw logs to runs/phase-1.1/
(gitignored). See docs/phases/phase-1.1-plan.md.

    uv run python experiments/phase-1.1/smoke_e2e.py
"""

from __future__ import annotations

from pathlib import Path

import anthropic

from stance.secrets import deepseek_api_key
from stance.tooluse.events import EventLogger, RefStore
from stance.tooluse.loop import run_tool_loop
from stance.tooluse.score import read_runs, score
from stance.tooluse.tasks.chain import build_chain_task
from stance.tooluse.tools import make_tools

MODEL = "deepseek-v4-flash"
OUT = Path("runs/phase-1.1")
SYSTEM = (
    "You are a customer-support agent. Complete the user's request using the available tools. "
    "The order id is given in the request. When the task is done, reply with a one-sentence "
    "confirmation and do NOT call another tool."
)


def main() -> None:
    seed, depth, fill_tokens, competition_n, arm = 1, 4, 3000, 3, "A"
    world, task = build_chain_task(
        seed=seed, depth=depth, fill_tokens=fill_tokens, competition_n=competition_n, arm=arm
    )
    tools = make_tools(world, arm)
    edge = task.dependency_edge
    assert edge is not None

    client = anthropic.Anthropic(
        base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
    )
    OUT.mkdir(parents=True, exist_ok=True)
    ev_path, run_path = OUT / "smoke_events.jsonl", OUT / "smoke_runs.jsonl"
    for p in (ev_path, run_path):
        p.unlink(missing_ok=True)
    logger = EventLogger(events_path=ev_path, runs_path=run_path)
    refs = RefStore(OUT / "refs")

    print(f"cell: depth={depth} fill~{fill_tokens} competition_n={competition_n} arm={arm}")
    print(f"prompt: {task.prompt}")
    print(f"needle (ground-truth account) = {edge.needle_id}; {len(world.tickets)} tickets staged")

    run_id = "smoke-1"
    out = run_tool_loop(
        task=task.prompt,
        system=SYSTEM,
        tools=tools,
        model=MODEL,
        complete_fn=lambda **kw: client.messages.create(**kw),
        logger=logger,
        refs=refs,
        run_id=run_id,
        cell_id="smoke",
        task_id="chain-1",
        seed=seed,
        terminal_style="crisp",
        loop_guard=True,
        max_turns=20,
        max_tokens=2048,
        raise_on_crash=True,
    )

    by_run, runs = read_runs(ev_path, run_path)
    summary = score(by_run[run_id], runs[run_id], task)

    print("--- trajectory ---")
    for e in by_run[run_id]:
        line = f"  turn {e.turn_index}: "
        line += f"{e.tool_called}({e.arguments})" if e.is_tool_call else "FINAL"
        if e.guard_action:
            line += f" [guard:{e.guard_action}]"
        if e.is_error:
            line += f" [error:{e.error_type}]"
        print(line)

    print("--- summary ---")
    print(f"  terminal_status   = {summary.terminal_status}")
    print(f"  critical_outcome  = {summary.critical_outcome}")
    print(f"  success           = {summary.success}")
    print(f"  achieved_depth    = {summary.achieved_depth}")
    print(f"  fill_at_use       = {summary.fill_at_use}")
    print(f"  competitors_seen  = {summary.competitors_surfaced}")
    print(f"  redundant_calls   = {summary.redundant_call_count}")
    print(f"  handle avail/used = {summary.handle_available}/{summary.handle_used}")
    print(f"  cost_usd          = ${summary.total_cost_usd:.4f}  (tokens={summary.total_tokens})")
    print(f"  final_answer      = {out.final_answer[:200]!r}")


if __name__ == "__main__":
    main()
