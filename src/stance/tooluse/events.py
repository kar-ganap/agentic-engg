"""Per-call event + run-record loggers for the Phase 1.1 tool-use harness.

Append-only JSONL, **persistence-only** — mirrors the `BudgetLogger` idiom. The
loop writes a `CallEvent` per loop turn (raw fact of what happened, incl. its own
`guard_action`) and a crash-robust `RunRecord` in a finally-block. NO metric is
derived here — that is the scorer's job over these raw events (re-pointable, §0.7).
Schema: docs/phases/phase-1.1-plan.md § "Eval record schemas (v1)".
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CallEvent:
    """One loop turn (per-loop-turn unit, `is_tool_call` flags whether it called a
    tool). Raw observations only — everything evaluative is scorer-derived."""

    run_id: str
    turn_index: int
    is_tool_call: bool
    # identity / cell
    cell_id: str | None = None
    task_id: str | None = None
    seed: int | None = None
    model: str | None = None
    # selection
    tool_called: str | None = None
    tool_expected: str | None = None  # populated for the selection tier; None otherwise
    arguments: dict[str, Any] | None = None
    args_valid: bool | None = None
    # reasoning / feedback (refs to a side transcript — big payloads not inlined)
    reasoning_ref: str | None = None
    feedback_ref: str | None = None
    # response
    response_ref: str | None = None
    response_size_tokens: int | None = None
    response_format: str | None = None
    is_error: bool | None = None
    error_type: str | None = None
    truncated: bool | None = None
    extracted_ids: list[str] = field(default_factory=list)  # ALL ids the call rendered
    # accounting (response.usage.input_tokens IS context_size_at_call / fill-at-use)
    usage: dict[str, int] | None = None
    context_size_at_call: int | None = None
    latency_ms: float | None = None
    # loop
    stop_reason: str | None = None
    is_final: bool = False
    guard_action: str | None = None  # e.g. "warn"/"break" — trajectory-mutating, raw
    timestamp: float = field(default_factory=time.time)

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


@dataclass
class RunRecord:
    """Crash-robust per-run footer (written in a finally-block). `terminal_status`
    can't be reconstructed from events (a crash skips the `is_final` turn)."""

    run_id: str
    terminal_status: str  # complete | max_turns | loop_guard | crash | timeout
    cell_id: str | None = None
    task_id: str | None = None
    seed: int | None = None
    model: str | None = None
    started: float | None = None
    ended: float | None = None
    final_answer_ref: str | None = None
    note: str | None = None  # free-text (e.g. the exception repr on a crash) — auditability

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


class EventLogger:
    """Append-only JSONL logger: per-call events to one file, run records to another.

    Usage:
        logger = EventLogger(events_path=Path("runs/events.jsonl"),
                             runs_path=Path("runs/runs.jsonl"))
        logger.log_event(CallEvent(run_id, turn_index=0, is_tool_call=True))
        logger.log_run(RunRecord(run_id, terminal_status="complete"))
    """

    def __init__(self, *, events_path: Path, runs_path: Path) -> None:
        self.events_path = events_path
        self.runs_path = runs_path
        for p in (events_path, runs_path):
            p.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: CallEvent) -> None:
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(event.to_jsonl() + "\n")

    def log_run(self, record: RunRecord) -> None:
        with self.runs_path.open("a", encoding="utf-8") as f:
            f.write(record.to_jsonl() + "\n")


class RefStore:
    """Content-addressed side store for big payloads (final answers, tool results,
    reasoning). The event holds a `sha256:...` ref; the text lives in
    `<root>/<sha>.txt`. Same text → same ref (natural dedup). This is
    return-a-reference (#4) applied to our own logging — keeps the JSONL light."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def store(self, text: str) -> str:
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        (self.root / f"{sha}.txt").write_text(text, encoding="utf-8")
        return f"sha256:{sha}"
