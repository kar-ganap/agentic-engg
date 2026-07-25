"""The fuzzy 5-criterion rubric grader (the DV). A Sonnet-anchored LLM judge (wired in the runner;
grade() takes any Client) scores a formed position 0-4 on each criterion -> aggregate 0-20, equal
weight. Fuzzy by design: qualitative criteria, no oracle/exact-match (a crisp grader would smuggle
in reflection's home edge — prereg precondition).

The judge sees the debate + the correct_position (the key) + the target/distractor LABELS (so it can
score evidence-use = weighed targets, resisted distractors) + the position under grade.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from stance.reasoning.arms import ArmResult, Client
from stance.reasoning.pool import Task
from stance.reasoning.position import LABEL_LINE_RE

CRITERIA = ("stance_correctness", "calibration", "retraction", "evidence_use", "epistemic_humility")

# Generous cap: Sonnet 5 spends reasoning tokens before the visible scores, so 512 truncated the
# grade mid-EVIDENCE_USE (pilot: 8/8 parse-fails hit exactly 512). The visible output is tiny; the
# headroom is for the model's reasoning.
_GRADE_MAX_TOKENS = 2048

_LABELS = {  # judge-output label -> criterion key
    "STANCE_CORRECTNESS": "stance_correctness",
    "CALIBRATION": "calibration",
    "RETRACTION": "retraction",
    "EVIDENCE_USE": "evidence_use",
    "EPISTEMIC_HUMILITY": "epistemic_humility",
}

JUDGE_SYSTEM = (
    "You are a strict, fair grader scoring a formed position against a rubric. Use the anchors; "
    "reserve 4 for clear cases and 0 for clear failures. Judge qualitatively — there is no "
    "exact-match answer key."
)

RUBRIC = (
    "Score each criterion 0-4 (anchors at 0 / 2 / 4; use 1 and 3 for in-between):\n"
    "- STANCE_CORRECTNESS: 0=opposite/wrong; 2=partially right, misses the core; "
    "4=matches the correct position's direction + reasoning.\n"
    "- CALIBRATION: 0=badly off (confident when uncertain, or vice versa); 2=roughly in range but "
    "off; 4=near the target confidence band.\n"
    "- RETRACTION: 0=none/vacuous; 2=generic but present; 4=specific, names concrete disconfirming "
    "evidence.\n"
    "- EVIDENCE_USE: 0=driven by distractors / ignored targets; 2=mixed pull; 4=weighed the "
    "targets, resisted the distractors.\n"
    "- EPISTEMIC_HUMILITY: 0=false certainty on contested points OR over-hedges a solid claim; "
    "2=uneven; 4=hedges where contested, commits where solid."
)


@dataclass(frozen=True)
class GradeResult:
    scores: dict[str, int]  # criterion -> 0-4 (-1 = unparseable)
    rationale: str
    raw: str

    @property
    def total(self) -> int:
        return sum(max(v, 0) for v in self.scores.values())  # -1 counts as 0 in the aggregate

    @property
    def parsed_ok(self) -> bool:
        return all(self.scores.get(k, -1) >= 0 for k in CRITERIA)


def _text(content: list[Any]) -> str:
    return "".join(getattr(b, "text", "") for b in content if getattr(b, "type", None) == "text")


def _parse_score(s: str) -> int:
    m = re.search(r"-?\d+", s)
    if not m:
        return -1
    v = int(m.group())
    return v if 0 <= v <= 4 else -1


def _parse_grade(text: str) -> GradeResult:
    scores = {k: -1 for k in CRITERIA}
    rationale: list[str] = []
    in_rationale = False
    for line in text.splitlines():
        m = LABEL_LINE_RE.match(line)
        if m and (lbl := m.group(1)) in _LABELS:
            scores[_LABELS[lbl]] = _parse_score(m.group(2))
            in_rationale = False
        elif m and m.group(1) == "RATIONALE":
            in_rationale = True
            if rest := m.group(2).strip(" *"):
                rationale.append(rest)
        elif in_rationale:
            rationale.append(line.strip())
    return GradeResult(scores=scores, rationale=" ".join(rationale).strip(), raw=text)


def _grade_prompt(task: Task, result: ArmResult) -> str:
    evidence = "\n".join(f"- [{e.kind}] {e.ref}: {e.text}" for e in task.evidence)  # LABELED
    p = result.position
    return (
        f"{RUBRIC}\n\n"
        f"DEBATE: {task.debate}\n\n"
        f"CORRECT POSITION (the grading key):\n{task.correct_position}\n\n"
        f"EVIDENCE (each labeled target or distractor):\n{evidence}\n\n"
        "THE POSITION TO GRADE:\n"
        f"STANCE: {p.stance}\nCONFIDENCE: {p.confidence}\nRETRACTION: {p.retraction}\n"
        f"EVIDENCE_USED: {', '.join(p.evidence_used)}\n\n"
        "Output EXACTLY these six labelled lines and nothing else:\n"
        "STANCE_CORRECTNESS: <0-4>\nCALIBRATION: <0-4>\nRETRACTION: <0-4>\n"
        "EVIDENCE_USE: <0-4>\nEPISTEMIC_HUMILITY: <0-4>\nRATIONALE: <one or two sentences>"
    )


def grade(task: Task, result: ArmResult, judge: Client) -> GradeResult:
    resp = judge.complete(
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": _grade_prompt(task, result)}],
        max_tokens=_GRADE_MAX_TOKENS,
    )
    return _parse_grade(_text(resp.content))
