"""Deterministic-vs-probabilistic verifier split (Phase 2.1, Module 6 L184) — the eval stack's core.

Two layers with one report. DETERMINISTIC verifiers are cheap, binary, and LLM-free (a malformed
output fails here for *free*); the PROBABILISTIC verifier is the LLM judge, reserved for genuinely
subjective criteria. `evaluate` runs deterministic FIRST and, by default, **gates**: it does not
pay the judge if a mechanical check already failed. Deterministic failures carry a `corrective` —
a signal to inject back into the agent's context (L184; the feedback loop B5/B7 build on), not a
raw stack trace.

Binds the reserved `stance.eval` shapes to the concrete verifiers already in the repo:
`reasoning.grader.grade` (probabilistic), `eval.accuracy` (deterministic containment). The formed
position (`ArmResult.position`) and a raw response string are the two demonstrated subjects.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from stance.eval.accuracy import is_hit
from stance.reasoning.arms import ArmResult, Client
from stance.reasoning.grader import CRITERIA, grade
from stance.reasoning.pool import Task


@dataclass(frozen=True)
class Verdict:
    """One verifier's result. Deterministic → passed + (on failure) corrective; probabilistic →
    a normalized 0-1 score + rationale."""

    name: str
    kind: str                 # "deterministic" | "probabilistic"
    passed: bool | None       # deterministic: True/False; probabilistic: None
    score: float | None       # probabilistic: 0-1; deterministic: None
    detail: str = ""
    corrective: str = ""      # a deterministic failure's signal, to inject back into context


class DeterministicVerifier[S](Protocol):
    @property
    def name(self) -> str: ...
    def check(self, subject: S) -> Verdict: ...


class ProbabilisticVerifier[S](Protocol):
    @property
    def name(self) -> str: ...
    def evaluate(self, subject: S) -> list[Verdict]: ...  # one Verdict per criterion


@dataclass(frozen=True)
class EvalReport:
    subject_id: str
    deterministic: list[Verdict]
    probabilistic: list[Verdict]

    @property
    def det_passed(self) -> bool:
        return all(v.passed is True for v in self.deterministic)

    @property
    def correctives(self) -> list[str]:
        """The corrective signals from failed deterministic checks (to inject back into context)."""
        return [v.corrective for v in self.deterministic if v.passed is False and v.corrective]

    @property
    def prob_total(self) -> float:
        return sum(v.score for v in self.probabilistic if v.score is not None)


def evaluate[S](
    subject: S, subject_id: str,
    deterministic: Sequence[DeterministicVerifier[S]],
    probabilistic: ProbabilisticVerifier[S] | None = None, *, gate: bool = True,
) -> EvalReport:
    """Deterministic-first: run the cheap sensors, then the (expensive) judge ONLY if no
    deterministic check failed — unless `gate=False`. The core Module-6 discipline."""
    dets = [v.check(subject) for v in deterministic]
    probs: list[Verdict] = []
    if probabilistic is not None and (not gate or all(v.passed is not False for v in dets)):
        probs = probabilistic.evaluate(subject)
    return EvalReport(subject_id=subject_id, deterministic=dets, probabilistic=probs)


def _det(name: str, passed: bool, detail: str, corrective: str = "") -> Verdict:
    return Verdict(name, "deterministic", passed, None, detail, "" if passed else corrective)


# --- deterministic verifiers over a formed position (an ArmResult) ---
@dataclass(frozen=True)
class Parseable:
    name: str = "parseable"

    def check(self, subject: ArmResult) -> Verdict:
        p = subject.position
        ok = p.confidence >= 0 and bool(p.stance.strip())
        return _det(self.name, ok, "stance+confidence parsed" if ok else "unparseable position",
                    "Malformed: end with the four labelled lines STANCE:/CONFIDENCE:/RETRACTION:/"
                    "EVIDENCE_USED: in plain text.")


@dataclass(frozen=True)
class CitesEvidence:
    name: str = "cites-evidence"

    def check(self, subject: ArmResult) -> Verdict:
        n = len(subject.position.evidence_used)
        return _det(self.name, n > 0, f"{n} evidence id(s)",
                    "You cited no evidence — list the ids you relied on in EVIDENCE_USED.")


@dataclass(frozen=True)
class HasRetraction:
    name: str = "has-retraction"

    def check(self, subject: ArmResult) -> Verdict:
        ok = bool(subject.position.retraction.strip())
        return _det(self.name, ok, "retraction present" if ok else "no retraction",
                    "State a concrete retraction criterion (what evidence would change your mind).")


# --- a deterministic verifier over a raw response string (rot / containment) ---
@dataclass(frozen=True)
class Containment:
    answer_key: str
    name: str = "containment"

    def check(self, subject: str) -> Verdict:
        ok = is_hit(subject, self.answer_key)
        return _det(self.name, ok, "needle found" if ok else "needle missing")


# --- the PROBABILISTIC verifier: the LLM judge (grader.grade) over an ArmResult ---
@dataclass(frozen=True)
class JudgeVerifier:
    task: Task
    judge: Client
    name: str = "llm-judge"

    def evaluate(self, subject: ArmResult) -> list[Verdict]:
        gr = grade(self.task, subject, self.judge)
        return [Verdict(f"judge:{c}", "probabilistic", None,
                        (gr.scores[c] / 4 if gr.scores[c] >= 0 else None), gr.rationale)
                for c in CRITERIA]
