"""Thread-B reasoning harness (Phase 2.0): position-forming loops over the evidence graph.

Pools (debate + graph-targets + distractors) live in experiments/phase-2.0/pool_*.py; the sampler
turns a Pool + the graph into a materialized Task at a chosen size x confusability.
"""

from stance.reasoning.arms import ARMS, Arm, ArmResult, Client, Meter, baseline, render_stuffed
from stance.reasoning.environment import EvidenceEnv
from stance.reasoning.grader import CRITERIA, GradeResult, grade
from stance.reasoning.pool import Distractor, EvidenceItem, Pool, Task
from stance.reasoning.position import FormedPosition, parse_formed_position
from stance.reasoning.sampler import build_task

__all__ = [
    "ARMS",
    "CRITERIA",
    "Arm",
    "ArmResult",
    "Client",
    "Distractor",
    "EvidenceEnv",
    "EvidenceItem",
    "FormedPosition",
    "GradeResult",
    "Meter",
    "Pool",
    "Task",
    "baseline",
    "build_task",
    "grade",
    "parse_formed_position",
    "render_stuffed",
]
