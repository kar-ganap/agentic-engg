"""The position-forming output contract: a `FormedPosition`, a parser, and the format instruction
every arm appends. The format is the CONTROL — all arms produce the same shape, so the DV isolates
reasoning structure, not output format. Parsing is text-based (labelled lines), NOT structured
output, to stay provider-agnostic (DeepSeek-primary; the §0.17 shim can leak tool markup).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_LABELS = ("STANCE", "CONFIDENCE", "RETRACTION", "EVIDENCE_USED")

# Markdown-tolerant label-line matcher: LABEL:, **LABEL:**, - LABEL:, ### LABEL: — models bold the
# labels despite "no markdown". Shared by the position parser AND the grade parser so they can't
# drift (both hit the same DeepSeek/Sonnet formatting quirk; smoke 2026-07-25).
LABEL_LINE_RE = re.compile(r"^[\s>*#-]*([A-Z][A-Z_]*)\*{0,2}\s*:(.*)")

POSITION_FORMAT = (
    "End your answer with EXACTLY these four labelled lines (plain text, no markdown):\n"
    "STANCE: <your position on the debate, 1-3 sentences>\n"
    "CONFIDENCE: <an integer 0-100>\n"
    "RETRACTION: <what specific evidence would change your mind>\n"
    "EVIDENCE_USED: <comma-separated ids of the evidence you relied on>"
)


@dataclass(frozen=True)
class FormedPosition:
    stance: str
    confidence: int  # 0-100; -1 = unparseable (the grader penalizes)
    retraction: str
    evidence_used: tuple[str, ...]
    raw: str


def _parse_confidence(s: str) -> int:
    m = re.search(r"-?\d+", s)
    if not m:
        return -1
    v = int(m.group())
    return v if 0 <= v <= 100 else -1


def parse_formed_position(text: str) -> FormedPosition:
    """Field-anchored parse: scan lines, switch buckets on a known LABEL:, accumulate the rest.
    Robust to ordering, multi-line values, surrounding prose, and MARKDOWN around the labels
    (**STANCE:**, - STANCE:, ### STANCE:). Models bold the labels despite the "no markdown"
    instruction (seen on DeepSeek in the react loop) — the instruction is not reliable, so the
    parser is: it tolerates leading markdown markers and strips edge asterisks from values."""
    buckets: dict[str, list[str]] = {k: [] for k in _LABELS}
    current: str | None = None
    for line in text.splitlines():
        m = LABEL_LINE_RE.match(line)
        if m and (label := m.group(1)) in _LABELS:
            current = label
            rest = m.group(2).strip(" *")
            if rest:
                buckets[label].append(rest)
        elif current is not None:
            buckets[current].append(line.strip())
    refs = re.findall(r"[A-Za-z0-9][\w-]*", " ".join(buckets["EVIDENCE_USED"]))
    return FormedPosition(
        stance=" ".join(buckets["STANCE"]).strip(" *"),
        confidence=_parse_confidence(" ".join(buckets["CONFIDENCE"])),
        retraction=" ".join(buckets["RETRACTION"]).strip(" *"),
        evidence_used=tuple(refs),
        raw=text,
    )
