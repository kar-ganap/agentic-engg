"""Offline re-scoring of context-rot runs (Phase 1.0) — reproducible analysis.

Reads the committed JSONL run files (which record each answer) and computes
accuracy curves under two scorers:
  - lenient:   the answer key appears anywhere in the response.
  - committed: the key appears AND no hedge/refusal marker is present
               (length-independent; separates a confident answer from a hedge).

The committed detector normalizes apostrophes so forms like "don't have" are
caught (an earlier inline version missed them — see lessons §0.11 discussion).

    uv run python experiments/phase-1.0/score.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

RUNS = Path(__file__).resolve().parents[2] / "runs" / "phase-1.0"
ANSWER_KEY = "QX-7793-LK"

# Markers of a non-committed answer (hedge / refusal / deferral). Matched against
# apostrophe-stripped lowercase text.
HEDGE_MARKERS = [
    "unable", "cannot", "cant", "couldnt", "could not", "couldn",
    "do not have", "dont have", "unknown", "conflicting", "multiple",
    "no single", "not have a single", "need to search", "no definitive",
    "could not find", "not find a", "no catalog number",
]


def _norm_alnum(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def _norm_text(s: str) -> str:
    return s.lower().replace("'", "").replace("’", "")  # strip apostrophes


_KEY = _norm_alnum(ANSWER_KEY)


def lenient(answer: str) -> bool:
    return _KEY in _norm_alnum(answer)


def committed(answer: str) -> bool:
    text = _norm_text(answer)
    return lenient(answer) and not any(m in text for m in HEDGE_MARKERS)


def _curve(rows: list[dict], scorer) -> dict[int, float]:  # type: ignore[no-untyped-def]
    by: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["target_tokens"]].append(r)
    return {t: sum(scorer(r["answer"]) for r in by[t]) / len(by[t]) for t in sorted(by)}


def _load(comp: str, model: str = "haiku-4-5-20251001") -> list[dict]:
    f = RUNS / f"tool_call_stream__{comp}__low__{model}.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def main() -> None:
    conds = ["neutral", "localized", "diffuse"]
    data = {c: _load(c) for c in conds}
    lengths = sorted({r["target_tokens"] for c in conds for r in data[c]})
    for label, scorer in (("COMMITTED (fixed detector)", committed), ("LENIENT (mentioned)", lenient)):
        print(f"\n{label}")
        header = f"{'length':>7} " + " ".join(f"{c:>9}" for c in conds) + "   n/pt"
        print(header)
        cs = {c: _curve(data[c], scorer) for c in conds}
        for t in lengths:
            ns = "/".join(str(sum(1 for r in data[c] if r["target_tokens"] == t)) for c in conds)
            vals = " ".join(f"{cs[c][t]:>9.2f}" if t in cs[c] else f"{'-':>9}" for c in conds)
            print(f"{t:>7} {vals}   {ns}")


if __name__ == "__main__":
    main()
