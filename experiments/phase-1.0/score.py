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
# Genuine-uncertainty markers only. A roleplay PREAMBLE ("I need to search …")
# is not a hedge as long as the core answer is unhedged, so "need to search" was
# removed (it caused false negatives: Haiku narrates a search it can't run, then
# commits correctly — see results.md / lessons). The markers below all express
# uncertainty about the ANSWER itself, not about the (fictional) retrieval.
HEDGE_MARKERS = [
    "unable", "cannot", "cant", "couldnt", "could not", "couldn",
    "do not have", "dont have", "unknown", "conflict",
    "no single", "not have a single", "no definitive",
    "could not find", "not find a", "no catalog number",
    # Core ambiguity about the ANSWER, not the search: "multiple catalog
    # numbers"/"different catalog numbers" hedge, but bare "multiple references"
    # (preamble describing the fictional search breadth) does NOT — see the
    # flip-audit in lessons. This is the operational form of "preamble is fine
    # iff the core answer is unhedged".
    "multiple catalog", "different catalog",
    # Sonnet-specific hedges (validated against recorded answers, C step):
    # it states the key then flags the records as untrustworthy. "conflict"
    # subsumes the earlier "conflicting".
    "inconsistent", "unreliable", "different values",
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


def _load(comp: str, model: str) -> list[dict]:
    f = RUNS / f"tool_call_stream__{comp}__low__{model}.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def _models_present() -> list[str]:
    """Model tags that have at least one run file (stable, de-duplicated order)."""
    tags: list[str] = []
    for f in sorted(RUNS.glob("tool_call_stream__*__low__*.jsonl")):
        tag = f.stem.split("__")[-1]
        if tag not in tags:
            tags.append(tag)
    return tags


def _report(model: str, conds: list[str]) -> None:
    data = {c: _load(c, model) for c in conds}
    if not any(data.values()):
        return
    lengths = sorted({r["target_tokens"] for c in conds for r in data[c]})
    print(f"\n################  MODEL: {model}  ################")
    for label, scorer in (("COMMITTED", committed), ("LENIENT (mentioned)", lenient)):
        print(f"\n{label}")
        print(f"{'length':>7} " + " ".join(f"{c:>9}" for c in conds) + "   n/pt")
        cs = {c: _curve(data[c], scorer) for c in conds}
        for t in lengths:
            ns = "/".join(str(sum(1 for r in data[c] if r["target_tokens"] == t)) for c in conds)
            vals = " ".join(f"{cs[c][t]:>9.2f}" if t in cs[c] else f"{'-':>9}" for c in conds)
            print(f"{t:>7} {vals}   {ns}")


def main() -> None:
    conds = ["neutral", "localized", "diffuse"]
    for model in _models_present():
        _report(model, conds)


if __name__ == "__main__":
    main()
