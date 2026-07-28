"""Held-out tool-eval set SURFACE (Phase 2.1, Module 6 / B4).

Describes the reserved-seed held-out selection corpus that B5 (description-refinement) and B7
(feedback-vs-model attribution) measure on — disjoint from the phase-1.1 dev seeds, so a gain is
generalization rather than overfitting to the training instances.

    uv run python experiments/phase-2.1/heldout.py
"""

from __future__ import annotations

from stance.eval.heldout import (
    DENSITIES,
    HELDOUT_SEEDS,
    NAMESPACED,
    TRAINING_SEED_MAX,
    heldout_selection_tasks,
)


def main() -> None:
    tasks = heldout_selection_tasks()
    print(f"held-out tool-eval set — {len(tasks)} selection tasks\n")
    print(f"  reserved seeds: {list(HELDOUT_SEEDS)}  (all > {TRAINING_SEED_MAX}; dev used 1-5)")
    print(f"  densities:      {list(DENSITIES)}")
    print(f"  namespaced:     {list(NAMESPACED)}")
    print(f"  grid:           {len(HELDOUT_SEEDS)} × {len(DENSITIES)} × {len(NAMESPACED)} "
          f"= {len(tasks)} tasks")
    print("\n  disjoint from training → a description-refinement gain here is generalization.\n")
    print("  sample tasks:")
    for _world, task in tasks[:3]:
        print(f"    seed={task.seed} density_n={task.ivs['density_n']} "
              f"namespaced={task.ivs['namespaced']} → expected={task.expected_tool!r} "
              f"| {task.prompt}")


if __name__ == "__main__":
    main()
