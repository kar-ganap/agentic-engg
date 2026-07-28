"""Held-out tool-eval set (Phase 2.1, Module 6 / B4) — delivers phase-1.1-plan L486's reserved set.

A corpus of selection tasks materialized from a RESERVED seed range, disjoint from the dev/training
seeds (phase-1.1 used 1-5; we reserve all of 1-50 for dev). B5's description-refinement is measured
HERE — on entities the rewrite never saw — so a gain is *generalization*, not overfitting to the
training seeds. The DV is the deterministic first-tool selection (`expected_tool`), no judge.
"""

from __future__ import annotations

from stance.tooluse.domain import World
from stance.tooluse.tasks.base import TaskInstance
from stance.tooluse.tasks.selection import build_selection_task

TRAINING_SEED_MAX = 50                      # dev/training seeds live in 1..50 (phase-1.1 used 1..5)
HELDOUT_SEEDS: tuple[int, ...] = tuple(range(101, 111))  # reserved; never used to drive a rename
# ≤5 (the sibling list caps at 5); the §1.10 attractor `lookup_user` enters at density ≥2, so 1 is a
# no-clash control cell (accuracy 1.00) while 3 and 5 are where pre-namespace selection collapses.
DENSITIES: tuple[int, ...] = (1, 3, 5)
NAMESPACED: tuple[bool, ...] = (False, True)


def is_heldout(seed: int) -> bool:
    """A seed is held-out iff it is outside the reserved dev range (so eval ≠ training)."""
    return seed > TRAINING_SEED_MAX


def heldout_selection_tasks() -> list[tuple[World, TaskInstance]]:
    """Materialize the held-out corpus (reserved seeds × densities × namespacing)."""
    return [
        build_selection_task(seed=s, density_n=d, namespaced=ns)
        for s in HELDOUT_SEEDS
        for d in DENSITIES
        for ns in NAMESPACED
    ]


def selection_hit(task: TaskInstance, first_tool: str | None) -> bool:
    """Deterministic DV: did the agent's first tool choice match the expected tool?"""
    return first_tool is not None and first_tool == task.expected_tool
