"""Append-only token-budget logger.

Records per-turn tokens by category to a JSONL file. The caller decides what
counts as each category (system / tools / history / retrieved); this module
only persists what it's given. Category semantics are a load-bearing design
decision the user owns when wiring this into the raw loop.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TurnBudget:
    """One turn's token allocation by category, plus optional API usage.

    `usage` holds the raw Anthropic `usage` counts (input/output/cache_creation/
    cache_read) — stored raw so cost re-derives if prices change. `cost_usd` is
    what the pinned price table said at run time (what we actually paid). The
    caller computes cost; this module stays persistence-only (no pricing import).
    """

    run_id: str
    turn: int
    categories: dict[str, int]
    model: str | None = None
    usage: dict[str, int] | None = None
    cost_usd: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_jsonl(self) -> str:
        return json.dumps(
            {
                "run_id": self.run_id,
                "turn": self.turn,
                "timestamp": self.timestamp,
                "model": self.model,
                "categories": self.categories,
                "usage": self.usage,
                "cost_usd": self.cost_usd,
                "extra": self.extra,
            },
            sort_keys=True,
        )


class BudgetLogger:
    """Append-only JSONL logger for per-turn token budgets.

    Usage:
        logger = BudgetLogger(Path("runs/budget.jsonl"))
        run_id = logger.new_run()
        logger.record(turn=0, categories={"system": 412, "tools": 88, "history": 0})
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._run_id: str | None = None

    def new_run(self, run_id: str | None = None) -> str:
        self._run_id = run_id or uuid.uuid4().hex[:12]
        return self._run_id

    def record(
        self,
        turn: int,
        categories: dict[str, int],
        model: str | None = None,
        usage: dict[str, int] | None = None,
        cost_usd: float | None = None,
        **extra: Any,
    ) -> None:
        if self._run_id is None:
            self.new_run()
        assert self._run_id is not None
        budget = TurnBudget(
            run_id=self._run_id,
            turn=turn,
            categories=dict(categories),
            model=model,
            usage=dict(usage) if usage is not None else None,
            cost_usd=cost_usd,
            extra=extra,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(budget.to_jsonl() + "\n")
