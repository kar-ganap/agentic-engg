"""Evaluation harness (Phase 2.1, Module 6).

The reserved placeholder Protocols (`TrajectoryLog`/`Rubric`/`LLMJudge`) are now **superseded** by
the concrete deterministic-vs-probabilistic verifier split in `verify` — the shapes their docstrings
deferred to Phase 2.1. `accuracy` is the deterministic normalized-containment slice (Phase 1.0).
"""

from __future__ import annotations

from stance.eval.accuracy import accuracy, is_hit, normalize
from stance.eval.verify import (
    CitesEvidence,
    Containment,
    DeterministicVerifier,
    EvalReport,
    HasRetraction,
    JudgeVerifier,
    Parseable,
    ProbabilisticVerifier,
    Verdict,
    evaluate,
)

__all__ = [
    "CitesEvidence",
    "Containment",
    "DeterministicVerifier",
    "EvalReport",
    "HasRetraction",
    "JudgeVerifier",
    "Parseable",
    "ProbabilisticVerifier",
    "Verdict",
    "accuracy",
    "evaluate",
    "is_hit",
    "normalize",
]
