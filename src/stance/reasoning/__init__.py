"""Thread-B reasoning harness (Phase 2.0): position-forming loops over the evidence graph.

Pools (debate + graph-targets + distractors) live in experiments/phase-2.0/pool_*.py; the sampler
turns a Pool + the graph into a materialized Task at a chosen size x confusability.
"""

from stance.reasoning.pool import Distractor, EvidenceItem, Pool, Task
from stance.reasoning.sampler import build_task

__all__ = ["Distractor", "EvidenceItem", "Pool", "Task", "build_task"]
