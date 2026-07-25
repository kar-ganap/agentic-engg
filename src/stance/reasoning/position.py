"""The position-forming output contract: a `FormedPosition`, a parser, and the format instruction
every arm appends. The format is the CONTROL — all arms produce the same shape, so the DV isolates
reasoning structure, not output format. Parsing is text-based (labelled lines), NOT structured
output, to stay provider-agnostic (DeepSeek-primary; the §0.17 shim can leak tool markup).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_LABELS = ("STANCE", "CONFIDENCE", "RETRACTION", "EVIDENCE_USED")

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
    Robust to ordering, multi-line values, and surrounding prose."""
    buckets: dict[str, list[str]] = {k: [] for k in _LABELS}
    current: str | None = None
    for line in text.splitlines():
        m = re.match(r"\s*([A-Z_]+)\s*:(.*)", line)
        if m and (label := m.group(1)) in _LABELS:
            current = label
            rest = m.group(2).strip()
            if rest:
                buckets[label].append(rest)
        elif current is not None:
            buckets[current].append(line.strip())
    refs = " ".join(buckets["EVIDENCE_USED"]).replace(",", " ").split()
    return FormedPosition(
        stance=" ".join(buckets["STANCE"]).strip(),
        confidence=_parse_confidence(" ".join(buckets["CONFIDENCE"])),
        retraction=" ".join(buckets["RETRACTION"]).strip(),
        evidence_used=tuple(r for r in refs if r),
        raw=text,
    )
