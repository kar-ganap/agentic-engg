"""The uniform task contract every per-tier builder emits (Phase 1.1).

Predicates are **write-boundary** (decision: verifiability) — assert at the
state-changing actions with the correct consumed values + cardinality; the read
path is free. The builder emits them from the ground truth it created, so grading
is consistent by construction. See docs/phases/phase-1.1-plan.md § "Verifiability".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Write:
    """A write-boundary predicate: `action` called `cardinality` times with args
    that include (⊇) `args`. cardinality=1 → exactly once; cardinality=0 → must NOT
    happen (a negative assertion, e.g. no ticket for an ineligible order)."""

    action: str
    args: dict[str, Any]
    cardinality: int = 1


@dataclass(frozen=True)
class DependencyEdge:
    """The needle's produce→use edge. `needle_id` is the concrete per-seed value;
    `needle_arg` is the consumer arg that must equal it (e.g. send_message.account_id)."""

    producer: str
    consumer: str
    needle_id: str
    needle_arg: str


@dataclass
class TaskInstance:
    """What a builder returns alongside the staged `World`. The loop runs `prompt`;
    the scorer grades `expected_writes` + classifies the `dependency_edge`."""

    prompt: str
    expected_writes: list[Write]
    ivs: dict[str, Any]  # cell coordinates (tier, depth, fill, position, competition, arm, …)
    seed: int
    dependency_edge: DependencyEdge | None = None
    expected_tool: str | None = None  # selection tier only
    notes: dict[str, Any] = field(default_factory=dict)
