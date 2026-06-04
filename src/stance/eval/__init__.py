"""Evaluation harness — placeholder interfaces only. Grows in Phase 2.1 (Module 6).

Shapes are deliberately empty: the design decisions about what a Rubric records,
what a TrajectoryLog stores, and how LLMJudge composes with deterministic
verifiers are load-bearing and belong to Phase 2.1.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TrajectoryLog(Protocol):
    """A record of an agent's turns + observations. Shape decided Phase 2.1."""

    def turns(self) -> list[dict[str, Any]]: ...


@runtime_checkable
class Rubric(Protocol):
    """A scoring rubric. Implementations arrive in Phase 2.1."""

    def score(self, trajectory: TrajectoryLog) -> dict[str, float]: ...


@runtime_checkable
class LLMJudge(Protocol):
    """LLM-as-judge interface. Wire-up in Phase 2.1."""

    def evaluate(self, trajectory: TrajectoryLog, rubric: Rubric) -> dict[str, float]: ...


__all__ = ["LLMJudge", "Rubric", "TrajectoryLog"]
