"""B3 — OTel/Langfuse observability (Phase 2.1, Module 6 L187). Exports a committed tool-loop run to
Langfuse as a nested trace: a root `agent` observation → one child per loop turn (`tool` for a tool
call, `generation` otherwise) carrying token usage + outcome attributes. The client is built from
`stance.secrets` (explicit `.env` keys, never `os.environ`). Re-pointable (§0.7): replays committed
JSONL — no re-running the experiment.

    uv run python experiments/phase-2.1/trace_to_langfuse.py --runs runs/phase-1.1/binding --limit 3
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from stance import secrets
from stance.tooluse.events import CallEvent, RunRecord
from stance.tooluse.score import read_runs


def _usage(u: dict[str, int] | None) -> dict[str, int]:
    u = u or {}
    return {
        "input": u.get("input_tokens", 0),
        "output": u.get("output_tokens", 0),
        "cache_read": u.get("cache_read_input_tokens", 0),
        "cache_creation": u.get("cache_creation_input_tokens", 0),
    }


def export_run(client: Any, run_id: str, events: list[CallEvent], run: RunRecord) -> str | None:
    with client.start_as_current_observation(name=f"run:{run_id}", as_type="agent") as root:
        trace_id = client.get_current_trace_id()
        root.update(
            input={"task_id": run.task_id, "cell_id": run.cell_id, "seed": run.seed},
            output={"terminal_status": run.terminal_status},
            metadata={"model": run.model, "n_turns": len(events)},
        )
        for e in events:
            is_tool = bool(e.is_tool_call and e.tool_called)
            child = root.start_observation(
                name=e.tool_called or f"turn-{e.turn_index}",
                as_type="tool" if is_tool else "generation",
                metadata={"turn": e.turn_index, "stop_reason": e.stop_reason,
                          "guard_action": e.guard_action, "is_error": e.is_error},
                usage_details=_usage(e.usage),
                level="ERROR" if e.is_error else "DEFAULT",
            )
            child.end()
    client.flush()
    return client.get_trace_url(trace_id=trace_id)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/phase-1.1/binding")
    ap.add_argument("--limit", type=int, default=3)
    args = ap.parse_args()

    if not secrets.has_langfuse_keys():
        raise SystemExit("Langfuse keys missing from .env (PUBLIC_KEY / SECRET_KEY / BASE_URL).")
    from langfuse import Langfuse

    client = Langfuse(public_key=secrets.langfuse_public_key(),
                      secret_key=secrets.langfuse_secret_key(),
                      host=secrets.langfuse_base_url())
    d = Path(args.runs)
    by_run, runs = read_runs(d / "events.jsonl", d / "runs.jsonl")
    chosen = list(runs)[: args.limit]
    if not chosen:
        raise SystemExit(f"no runs found under {d}")
    for rid in chosen:
        url = export_run(client, rid, by_run.get(rid, []), runs[rid])
        print(f"exported {rid} ({len(by_run.get(rid, []))} turns) -> {url}")
    print(f"\n{len(chosen)} runs traced to Langfuse ({secrets.langfuse_base_url()}).")


if __name__ == "__main__":
    main()
