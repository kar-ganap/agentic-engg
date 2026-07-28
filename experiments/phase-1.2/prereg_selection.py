"""Pre-registration of position #2 (tool-selection) — Phase 1.2 Thread A, BEFORE the run
(Substrate Discipline #1). A LIVE hypothesis; the run moves it. Appends (no reset). Run ONCE.

    uv run python experiments/phase-1.2/prereg_selection.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Position, Retraction
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")

POSITION = Position(
    id="tool-selection",
    title="Does confusable-tool density degrade selection, and does namespacing recover it?",
    stance=(
        "Confusable-sibling density degrades first-tool selection accuracy; namespacing "
        "(disambiguated {entity}_search names) recovers it. Pre-registered design: density "
        "N∈{0,1,3,5} × {pre-namespace synonyms / post-namespace disambiguated} × 5 seeds; DV = "
        "first tool call == expected_tool. Prior 55 (user-set): the recovery half is likely "
        "(strong practitioner consensus) but the degradation half is uncertain on a capable model "
        "— if selection stays accurate even at N=5, the manipulation didn't bite (a #4/§0.20 null)."
    ),
    confidence=55,
    status="hypothesis",
    registered="2026-07-27",
    updated="2026-07-27",
    preconditions=(
        "DeepSeek-v4-flash; single-step selection task (first-tool DV, no loop)",
        "density N∈{0,1,3,5} × {pre,post-namespace} × 5 seeds; names vary, descriptions fixed",
        "a discriminating signal must exist (semantic overlap real) — else selection is a "
        "coin-flip",
    ),
    retraction=(
        Retraction("down", 25,
                   "accuracy flat in density_n — no degradation induced (manipulation didn't bite; "
                   "#4/§0.20 control-never-fires null)", ("degradation", "null")),
        Retraction("down", 20,
                   "namespacing does not recover accuracy at high N", ("namespacing",)),
    ),
    synthesis_ref=None,
)


def main() -> None:
    GraphStore(GRAPH_DIR).add(POSITION)  # append-only; no reset
    print("pre-registered: tool-selection (#2) — hypothesis, conf 55")


if __name__ == "__main__":
    main()
