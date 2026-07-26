"""Shared types for the Thread-B reasoning harness.

A `Pool` is a debate + the graph target-evidence that fixes its correct position + a bank of
`Distractor`s (same-topic, NON-decisive records; HIGH = orthogonal rival mechanism, MID = wrong
question type — design criteria in docs/phases/phase-2.0-plan.md). The sampler materializes a
`Pool` into a `Task` (a shuffled evidence set at a chosen size x confusability) that a
position-forming loop then reasons over.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Distractor:
    id: str
    axis: str           # pool-specific rival axis
    confusability: str  # high | mid
    realism: str        # synthetic | real (verify §0.16 before use)
    text: str           # the evidence-like claim: same topic, non-decisive
    # Optional {slot} template values. Empty -> a singleton (real anchors stay singletons).
    # Non-empty -> `text` is a template the multiplier fills into similar-but-distinct variants
    # (diffuse competition). Slot keys must match the {placeholders} in `text`.
    slots: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Pool:
    id: str
    debate: str
    correct_position: str          # the answer the rubric grades toward (fixed by the targets)
    target_ids: tuple[str, ...]    # graph Evidence ids that fix the answer
    distractors: tuple[Distractor, ...]


@dataclass(frozen=True)
class EvidenceItem:
    """One item in a materialized Task's evidence set (a target or a distractor)."""

    text: str
    kind: str          # target | distractor  — internal (judge-only), never shown to the arm
    ref: str           # evidence id (target) or distractor id (distractor) — internal
    display_id: str = ""  # anonymized shuffled id shown to the arm (item-NN); defeats triage


@dataclass(frozen=True)
class Task:
    """A materialized position-forming task: a debate + a shuffled evidence set + the gradeable
    correct position + the cell coordinates (for the sweep)."""

    pool_id: str
    debate: str
    evidence: tuple[EvidenceItem, ...]
    correct_position: str
    n_distractors: int
    confusability: str
    seed: int
