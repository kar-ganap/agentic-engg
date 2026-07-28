"""Tests for the held-out tool-eval set (`stance.eval.heldout`, Phase 2.1, Module 6 / B4).

The load-bearing property: the eval seeds are DISJOINT from the dev/training seeds (so a
description-refinement gain in B5 is generalization, not overfitting), and the corpus regenerates
deterministically from the reserved seeds.
"""

from __future__ import annotations

from stance.eval.heldout import (
    DENSITIES,
    HELDOUT_SEEDS,
    NAMESPACED,
    TRAINING_SEED_MAX,
    heldout_selection_tasks,
    is_heldout,
    selection_hit,
)
from stance.tooluse.tasks.selection import build_selection_task


def test_heldout_seeds_disjoint_from_training() -> None:
    assert all(s > TRAINING_SEED_MAX for s in HELDOUT_SEEDS)
    assert all(is_heldout(s) for s in HELDOUT_SEEDS)
    assert not is_heldout(1) and not is_heldout(5)  # the phase-1.1 dev seeds are NOT held-out


def test_corpus_size_and_shape() -> None:
    tasks = heldout_selection_tasks()
    assert len(tasks) == len(HELDOUT_SEEDS) * len(DENSITIES) * len(NAMESPACED)
    assert all(t.expected_tool in ("search_users", "user_search") for _, t in tasks)


def test_corpus_is_deterministic() -> None:
    a = build_selection_task(seed=101, density_n=3, namespaced=False)[1]
    b = build_selection_task(seed=101, density_n=3, namespaced=False)[1]
    assert a.prompt == b.prompt  # same seed → same entity → same prompt


def test_heldout_entities_differ_from_training() -> None:
    held = {t.prompt for _, t in heldout_selection_tasks()}
    train = {build_selection_task(seed=s, density_n=3, namespaced=False)[1].prompt
             for s in range(1, 6)}
    assert held - train  # the held-out corpus contains entities never seen at a training seed


def test_selection_hit_is_a_deterministic_dv() -> None:
    _, task = build_selection_task(seed=101, density_n=3, namespaced=False)
    assert selection_hit(task, task.expected_tool) is True
    assert selection_hit(task, "wrong_tool") is False
    assert selection_hit(task, None) is False
