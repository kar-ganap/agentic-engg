"""Thread-B grader tests (Phase 2.0): the fuzzy 5-criterion rubric judge."""

from __future__ import annotations

from typing import Any

from stance.reasoning.arms import ArmResult, Meter
from stance.reasoning.grader import CRITERIA, grade
from stance.reasoning.pool import EvidenceItem, Task
from stance.reasoning.position import FormedPosition


def _task() -> Task:
    return Task(
        pool_id="test",
        debate="does competition (not length) drive collapse?",
        evidence=(
            EvidenceItem("at fixed length, adding competitors collapses retrieval", "target", "t1"),
            EvidenceItem("middle items are recovered worse (position)", "distractor", "d-1"),
        ),
        correct_position="Competition is the driver; confidence ~80; retract if a neutral knee "
                         "appears below a diffuse knee.",
        n_distractors=1,
        confusability="high",
        seed=1,
    )


def _result() -> ArmResult:
    pos = FormedPosition("competition drives it", 78, "a neutral knee below a diffuse knee",
                         ("ev-t1",), "raw")
    return ArmResult(
        arm="baseline", position=pos, input_tokens=0, output_tokens=0, cache_read_tokens=0,
        n_calls=1, n_reads=0, n_turns=1, latency_s=0.0, pool_id="test", n_distractors=1,
        confusability="high", seed=1,
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
        self.last_prompt = ""

    def complete(self, *, system: str, messages: list[dict[str, Any]],
                 tools: Any = None, max_tokens: int = 512) -> _Resp:
        self.last_prompt = str(messages[0]["content"])
        r = _Resp(self._text)
        self.meter.add(r.usage)
        return r


_FIVE = (
    "STANCE_CORRECTNESS: 4\nCALIBRATION: 3\nRETRACTION: 4\n"
    "EVIDENCE_USE: 3\nEPISTEMIC_HUMILITY: 2\nRATIONALE: solid, hedged unevenly"
)


def test_criteria_are_the_five() -> None:
    assert CRITERIA == (
        "stance_correctness", "calibration", "retraction", "evidence_use", "epistemic_humility"
    )


def test_grade_parses_all_five_and_totals() -> None:
    g = grade(_task(), _result(), _FakeJudge(_FIVE))
    assert g.scores == {
        "stance_correctness": 4, "calibration": 3, "retraction": 4,
        "evidence_use": 3, "epistemic_humility": 2,
    }
    assert g.total == 16  # 4+3+4+3+2, equal weight, 0-20
    assert g.parsed_ok
    assert "hedged" in g.rationale


def test_grade_clamps_out_of_range_and_flags_missing() -> None:
    canned = "STANCE_CORRECTNESS: 9\nCALIBRATION: 3\nRATIONALE: partial"  # 9 invalid; 3 missing
    g = grade(_task(), _result(), _FakeJudge(canned))
    assert g.scores["stance_correctness"] == -1  # out of 0-4 range
    assert g.scores["calibration"] == 3
    assert g.scores["retraction"] == -1          # missing entirely
    assert not g.parsed_ok


def test_grade_tolerates_markdown_scores() -> None:
    # Sonnet bolds the grade labels despite the format instruction (smoke 2026-07-25)
    canned = (
        "**STANCE_CORRECTNESS:** 4\n**CALIBRATION:** 3\n**RETRACTION:** 4\n"
        "**EVIDENCE_USE:** 3\n**EPISTEMIC_HUMILITY:** 2\n**RATIONALE:** solid"
    )
    g = grade(_task(), _result(), _FakeJudge(canned))
    assert g.total == 16 and g.parsed_ok
    assert g.rationale == "solid"


def test_judge_sees_the_key_and_labeled_evidence() -> None:
    j = _FakeJudge(_FIVE)
    grade(_task(), _result(), j)
    assert "CORRECT POSITION" in j.last_prompt          # the grading key
    assert "target" in j.last_prompt and "distractor" in j.last_prompt  # labels for evidence-use
