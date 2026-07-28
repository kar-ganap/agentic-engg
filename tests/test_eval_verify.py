"""Tests for the deterministic-vs-probabilistic verifier split (`stance.eval.verify`, Phase 2.1).

The load-bearing behavior is the **gate**: `evaluate` must NOT pay the probabilistic judge when a
cheap deterministic check already failed (Module 6 L184). Also: deterministic failures carry a
`corrective` signal; the judge's 0-4 scores normalize to 0-1.
"""

from __future__ import annotations

from typing import Any

from stance.eval.verify import (
    CitesEvidence,
    Containment,
    HasRetraction,
    JudgeVerifier,
    Parseable,
    Verdict,
    evaluate,
)
from stance.reasoning.arms import ArmResult, Meter
from stance.reasoning.pool import EvidenceItem, Task
from stance.reasoning.position import FormedPosition


def _result(pos: FormedPosition) -> ArmResult:
    return ArmResult(
        arm="baseline", position=pos, input_tokens=0, output_tokens=0, cache_read_tokens=0,
        n_calls=1, n_reads=0, n_turns=1, latency_s=0.0, pool_id="test", n_distractors=1,
        confusability="high", seed=1,
    )


_GOOD = _result(FormedPosition("competition drives it", 78, "a neutral knee below diffuse",
                               ("ev-t1",), "raw"))
_BAD = _result(FormedPosition("", -1, "", (), "garbled output with no labelled lines"))


def _task() -> Task:
    return Task(
        pool_id="test", debate="competition vs length?",
        evidence=(EvidenceItem("adding competitors collapses retrieval", "target", "t1"),),
        correct_position="Competition drives it; ~80.", n_distractors=1, confusability="high",
        seed=1,
    )


# --- fake judge (mirrors tests/test_reasoning_grader.py) ---
_FIVE = (
    "STANCE_CORRECTNESS: 4\nCALIBRATION: 3\nRETRACTION: 4\n"
    "EVIDENCE_USE: 3\nEPISTEMIC_HUMILITY: 2\nRATIONALE: solid"
)


class _Usage:
    input_tokens = 200
    output_tokens = 30
    cache_read_input_tokens = 0


class _Block:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text: str) -> None:
        self.content = [_Block(text)]
        self.stop_reason = "end_turn"
        self.usage = _Usage()


class _FakeJudge:
    def __init__(self, text: str) -> None:
        self._text = text
        self.meter = Meter()

    def complete(self, *, system: str, messages: list[dict[str, Any]],
                 tools: Any = None, max_tokens: int = 512) -> _Resp:
        r = _Resp(self._text)
        self.meter.add(r.usage)
        return r


class _SpyProb:
    """A probabilistic verifier that records whether it was invoked (to observe the gate)."""

    name = "spy"

    def __init__(self) -> None:
        self.calls = 0

    def evaluate(self, subject: Any) -> list[Verdict]:
        self.calls += 1
        return [Verdict("spy:x", "probabilistic", None, 0.5, "ok")]


def test_deterministic_pass_on_good_position() -> None:
    for v in (Parseable(), CitesEvidence(), HasRetraction()):
        verdict = v.check(_GOOD)
        assert verdict.passed is True
        assert verdict.kind == "deterministic"
        assert verdict.corrective == ""  # no corrective on a pass


def test_deterministic_fail_carries_corrective() -> None:
    for v in (Parseable(), CitesEvidence(), HasRetraction()):
        verdict = v.check(_BAD)
        assert verdict.passed is False
        assert verdict.corrective  # a failure formats a signal to inject back into context


def test_gate_skips_probabilistic_on_deterministic_failure() -> None:
    spy = _SpyProb()
    report = evaluate(_BAD, "bad", [Parseable(), CitesEvidence()], spy)  # gate=True default
    assert spy.calls == 0                      # the judge is NOT paid when a cheap check failed
    assert report.probabilistic == []
    assert report.det_passed is False
    assert len(report.correctives) == 2        # both failures surfaced as corrective signals


def test_gate_false_runs_probabilistic_despite_failure() -> None:
    spy = _SpyProb()
    report = evaluate(_BAD, "bad", [Parseable()], spy, gate=False)
    assert spy.calls == 1
    assert len(report.probabilistic) == 1


def test_all_deterministic_pass_runs_probabilistic() -> None:
    spy = _SpyProb()
    report = evaluate(_GOOD, "good", [Parseable(), CitesEvidence(), HasRetraction()], spy)
    assert spy.calls == 1
    assert report.det_passed is True
    assert report.prob_total == 0.5


def test_judge_verifier_normalizes_scores() -> None:
    jv = JudgeVerifier(_task(), _FakeJudge(_FIVE))  # type: ignore[arg-type]
    verdicts = jv.evaluate(_GOOD)
    by = {v.name: v.score for v in verdicts}
    assert by["judge:stance_correctness"] == 1.0   # 4/4
    assert by["judge:epistemic_humility"] == 0.5    # 2/4
    assert all(v.kind == "probabilistic" and v.passed is None for v in verdicts)


def test_containment_verifier_over_response_string() -> None:
    v = Containment("QX-7793")
    assert v.check("the answer is qx 7793 buried here").passed is True
    assert v.check("no needle at all").passed is False
