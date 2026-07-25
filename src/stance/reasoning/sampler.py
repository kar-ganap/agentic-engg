"""Sampler (Thread B): a Pool + the evidence graph -> a materialized Task at a chosen
(n_distractors, confusability). Deterministic per seed.

Targets are always included and fix the gradeable answer; distractors are drawn from the requested
confusability tier. v0 samples WITHOUT replacement from the pool's authored distractors, so
n_distractors is capped at the tier size — large-N cells need the slotted parametric MULTIPLIER
(the "(c) hybrid" half; a documented follow-on). For the pilot, modest N from the authored banks
suffices (§0.21: prove the control fires before scaling the sweep).
"""

from __future__ import annotations

import random

from stance.graph.store import Graph
from stance.reasoning.pool import EvidenceItem, Pool, Task


def build_task(
    pool: Pool, graph: Graph, *, n_distractors: int, confusability: str, seed: int
) -> Task:
    targets: list[EvidenceItem] = []
    for tid in pool.target_ids:
        ev = graph.evidence.get(tid)
        if ev is None:
            raise KeyError(f"target evidence {tid!r} not in graph")
        targets.append(EvidenceItem(text=ev.summary, kind="target", ref=tid))

    tier = [d for d in pool.distractors if d.confusability == confusability]
    if n_distractors > len(tier):
        raise ValueError(
            f"pool {pool.id!r} has {len(tier)} {confusability!r} distractor(s); "
            f"n_distractors={n_distractors} exceeds the authored bank — needs the slotted "
            f"multiplier (follow-on)"
        )
    rng = random.Random(seed)
    chosen = rng.sample(tier, n_distractors)
    distractors = [EvidenceItem(text=d.text, kind="distractor", ref=d.id) for d in chosen]

    evidence = targets + distractors
    rng.shuffle(evidence)
    return Task(
        pool_id=pool.id,
        debate=pool.debate,
        evidence=tuple(evidence),
        correct_position=pool.correct_position,
        n_distractors=n_distractors,
        confusability=confusability,
        seed=seed,
    )
