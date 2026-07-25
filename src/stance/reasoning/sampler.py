"""Sampler (Thread B): a Pool + the evidence graph -> a materialized Task at a chosen
(n_distractors, confusability). Deterministic per seed.

Targets are always included and fix the gradeable answer; distractors are drawn from the requested
confusability tier. The tier is the MULTIPLIER's output: authored slotted templates expanded into
similar-but-distinct variants (`_expand`) plus real singletons. n_distractors is sampled without
replacement from that variant pool, so the ceiling is the total variant count (widen a template's
slots to raise it), not the count of authored templates.
"""

from __future__ import annotations

import itertools
import random

from stance.graph.store import Graph
from stance.reasoning.pool import Distractor, EvidenceItem, Pool, Task


def _expand(d: Distractor) -> list[Distractor]:
    """A singleton (no slots) -> [d]; a slotted template -> one Distractor per slot-value combo
    (unique id `d.id#k`, filled text), deterministic order. Variants are similar-but-distinct on
    the SAME axis = the diffuse competition the §1.8 primary needs; real anchors stay singletons."""
    if not d.slots:
        return [d]
    keys = sorted(d.slots)
    variants: list[Distractor] = []
    for i, combo in enumerate(itertools.product(*(d.slots[k] for k in keys))):
        filled = d.text.format(**dict(zip(keys, combo, strict=True)))
        variants.append(Distractor(f"{d.id}#{i}", d.axis, d.confusability, d.realism, filled))
    return variants


def build_task(
    pool: Pool, graph: Graph, *, n_distractors: int, confusability: str, seed: int
) -> Task:
    targets: list[EvidenceItem] = []
    for tid in pool.target_ids:
        ev = graph.evidence.get(tid)
        if ev is None:
            raise KeyError(f"target evidence {tid!r} not in graph")
        targets.append(EvidenceItem(text=ev.summary, kind="target", ref=tid))

    tier = [
        v for d in pool.distractors if d.confusability == confusability for v in _expand(d)
    ]  # multiplier: authored templates + real singletons -> the variant pool
    if n_distractors > len(tier):
        raise ValueError(
            f"pool {pool.id!r} yields {len(tier)} {confusability!r} distractor variants; "
            f"n_distractors={n_distractors} exceeds it — widen the slots (multiplier ceiling)"
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
