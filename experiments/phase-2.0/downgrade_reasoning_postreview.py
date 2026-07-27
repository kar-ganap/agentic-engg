"""Interim downgrade of `reasoning-pattern` after the three-reviewer pass (2026-07-25).

The pass found the two MECHANISM legs are artifacts (plan-execute's §1.8 "commit-to-few" win is
teaser-triage; reflection's §3.8 win is confounded by the critique prompt naming "overclaim") and
the EVIDENCE_USE criterion is invalid between arms. Only `no-universal-winner` (via the FAILURE
regimes) survives robustly, and §1.1 is a null, not a regime. Per the disposition (full re-test +
conservative interim), this APPENDS a conservative interim Position (latest-wins) pending the
teaser-matched + neutral-critique + prose-EVIDENCE_USE re-test. Run ONCE.

    uv run python experiments/phase-2.0/downgrade_reasoning_postreview.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Leg, Position, Retraction
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")

POSITION = Position(
    id="reasoning-pattern",
    title="Which reasoning pattern for position-forming over an evidence graph",
    stance=(
        "INTERIM (three-reviewer pass, 2026-07-25): only 'no universal winner' survives robustly, "
        "grounded in the FAILURE regimes — every arm has a debate it is clearly bad at (baseline "
        "§1.8 stance-collapse, reflection §1.8, react §3.8, plan §1.1@N4). The two MECHANISM "
        "claims "
        "are ARTIFACTS: plan-execute's §1.8 'commit-to-few' win is teaser-triage (it reads exactly "
        "the teaser-identifiable targets), and reflection's §3.8 win is confounded by a critique "
        "prompt naming 'overclaim'. §1.1 is a null (2 demonstrated regimes + 1 null, not a 3-cell "
        "partition). A teaser-matched + neutral-critique + prose-EVIDENCE_USE re-test is underway "
        "to "
        "re-earn or drop the mechanism legs; arms are ReAct / ReWOO-Plan-and-Solve / Self-Refine."
    ),
    confidence=50,
    status="hypothesis",  # demoted from candidate: the taxonomy/mechanisms rest on artifacts
    registered="2026-06-29",
    updated="2026-07-25",
    legs=(
        Leg("no-universal-winner", 60,
            "robust — grounded in the FAILURE regimes (each arm has a clearly-bad debate)"),
        Leg("sig-density-dilution", 40,
            "baseline stance-collapse under stuffed on-axis distractors is robust (=§1.8 acting); "
            "plan's 'commit-to-few' hold is teaser-triage — pending the teaser-matched re-test"),
        Leg("bias-x-structure", 40,
            "rests on 2 alignments, one (plan/§1.8) a triage artifact; react's bias wins nowhere"),
        Leg("reflection-systematic-caution", 40,
            "confidence-lowering is real+uniform, but the §3.8 win is confounded by the critique "
            "keyword 'overclaim' (clause c live) — pending the neutral-critique re-test"),
        Leg("regime-taxonomy", 35,
            "§1.1 is a NULL -> 2 regimes + 1 null, not a 3-cell partition; n=1 debate/regime"),
    ),
    preconditions=(
        "DeepSeek-v4-flash arms + Sonnet-5 fuzzy-rubric judge; cross-provider untested",
        "5 seeds/cell, N∈{4,12,24}; one debate per regime; n=5, no significance testing",
        "CURRENT stimulus leaks targets in the teaser (retrieve arms triage) — re-test defeats it",
    ),
    retraction=(
        Retraction("up", 20,
                   "teaser-matched re-test: plan-execute STILL beats stuff when triage is defeated "
                   "-> commit-to-few is real, not triage", ("sig-density", "bias-x-structure")),
        Retraction("up", 15,
                   "neutral-critique re-test: reflection STILL wins §3.8 without the 'overclaim' "
                   "keyword -> the caution mechanism is earned", ("reflection",)),
        Retraction("down", 20,
                   "re-tests null out plan and reflection -> the mechanisms were fully artifacts; "
                   "only no-universal-winner remains", ("sig-density", "reflection")),
    ),
    synthesis_ref="1.9",
)


def main() -> None:
    GraphStore(GRAPH_DIR).add(POSITION)  # append-only, latest-wins
    print("interim downgrade appended: reasoning-pattern -> hypothesis, conf 50 "
          "(mechanism legs ~40; only no-universal-winner robust; re-test underway)")


if __name__ == "__main__":
    main()
