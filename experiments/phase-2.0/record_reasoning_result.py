"""Thread B result capture (Phase 2.0) — APPENDS the reasoning-pattern experimental evidence and
MOVES the `reasoning-pattern` Position from its prereg hypothesis (conf 40) to the taxonomy
(candidate, conf 62). Append-only; latest-wins for the Position. Run ONCE (re-running double-appends
Evidence/Support). Does NOT reset — new records only.

    uv run python experiments/phase-2.0/record_reasoning_result.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Evidence, Leg, Position, Retraction, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")
SRC = "experiments/phase-2.0/results-reasoning.md"

EVIDENCE = (
    Evidence(
        "ev-reason-sd", "experimental", SRC,
        "§1.8 sweep (on-axis flawed distractors, N∈{4,12,24}×5): baseline bimodal-collapses at "
        "N=24 ([1,5,5,13,16], worst run pulled to length), plan_execute holds (16.4) reading ~3 "
        "items — dilution rot fires, commit-to-few sidesteps.",
        "direct",
    ),
    Evidence(
        "ev-reason-ts", "experimental", SRC,
        "§1.1 sweep: NO rot — baseline stance-correctness 4/4/4 across N (the ~7× cache fact is "
        "undilutable); all arms flat ~15-18, plan_execute marginally worst (reading few risks the "
        "lone decisive fact).",
        "direct",
    ),
    Evidence(
        "ev-reason-cf", "experimental", SRC,
        "§3.8 sweep (hedge, correct ~45): overclaiming rot — every arm conf 66-73 except "
        "reflection (44); reflection wins and rises with N (17.6@24), react amplifies the "
        "overclaim worst (6.6@24, [0,8,8,8,9]).",
        "direct",
    ),
    Evidence(
        "ev-reason-refl", "experimental", SRC,
        "Reflection = systematic caution: it uniformly lowers confidence — underclaims §1.8 (61 vs "
        "correct 80) yet correctly holds §3.8 (44≈45). One bias, right for hedges, wrong for "
        "confident answers.",
        "direct",
    ),
)

SUPPORT = (
    Support("reasoning-pattern", "ev-reason-sd", polarity="supports",
            warrant="dilutable-convergent answer + diffuse competition -> dilution rot; committing "
                    "to a small read-set sidesteps it (plan-execute wins the §1.8 regime)"),
    Support("reasoning-pattern", "ev-reason-ts", polarity="supports",
            warrant="a robust single fact can't be diluted -> no rot -> structure-agnostic; "
                    "reading few marginally risks the fact (react/baseline >= plan here)"),
    Support("reasoning-pattern", "ev-reason-cf", polarity="supports",
            warrant="a hedge answer's rot is overclaiming; inject-caution counters it (reflection "
                    "wins), read-all amplifies it (react worst)"),
    Support("reasoning-pattern", "ev-reason-refl", polarity="supports",
            warrant="reflection's bias is uniform caution-injection; effectiveness = match "
                    "between that bias and whether the answer should be cautious"),
)

POSITION = Position(
    id="reasoning-pattern",
    title="Which reasoning pattern for position-forming over an evidence graph",
    stance=(
        "No universal best reasoning pattern. Effectiveness = alignment between a pattern's "
        "inductive bias and the debate's epistemic structure. Across three debates the winner "
        "flips: dilutable-convergent (§1.8) -> plan-execute (commit-to-few sidesteps dilution); "
        "robust-single-fact (§1.1) -> structure-agnostic (the fact dominates); hedge (§3.8) -> "
        "reflection (inject-caution reins the overclaiming all confident-by-default arms suffer). "
        "The competition 'rot' is itself regime-specific: dilution / overclaiming / none."
    ),
    confidence=62,
    status="candidate",
    registered="2026-06-29",
    updated="2026-07-25",
    legs=(
        Leg("no-universal-winner", 68,
            "winner flips across 3 debates (plan / react-baseline / reflection each win one)"),
        Leg("bias-x-structure", 62,
            "each arm's bias (commit-few / inject-caution / read-all) predicts where it wins; "
            "confirmed via confidence + stance data"),
        Leg("reflection-systematic-caution", 62,
            "uniformly lowers confidence: underclaims §1.8 (61 vs 80), holds §3.8 (44≈45)"),
        Leg("sig-density-dilution-sidestep", 70,
            "§1.8 anchor: bimodal baseline collapse (pulled-to-length), plan holds; interaction "
            "specific to large-confusable-N"),
        Leg("regime-taxonomy", 40,
            "the 3-cell partition (dilutable / robust-fact / hedge) is n=1 debate per regime — a "
            "hypothesis; mechanisms confirmed, partition not"),
    ),
    preconditions=(
        "DeepSeek-v4-flash arms + Sonnet-5 fuzzy-rubric judge; cross-provider untested",
        "5 seeds/cell, N∈{4,12,24}; one debate per regime",
        "on-axis flawed distractors (§0.25) — the design that actually induces competition",
    ),
    retraction=(
        Retraction("down", 30,
                   "one arm dominates >=4/5 debate types in a wider set (no-universal-winner)",
                   ("no-universal-winner",)),
        Retraction("down", 20,
                   "an arm's win/loss traces to something other than its bias (e.g. prompt length)",
                   ("bias-x-structure",)),
        Retraction("down", 20,
                   "reflection's caution-injection doesn't replicate or is a generic-critique "
                   "artifact (a rubric-guided critique may differ)", ("reflection",)),
        Retraction("down", 15,
                   "the §1.8 dilution collapse fails cross-provider or is a grader artifact",
                   ("sig-density",)),
        Retraction("up", 15,
                   "a regime's predicted winner replicates on a 2nd debate (taxonomy firms up)",
                   ("regime-taxonomy",)),
    ),
    synthesis_ref="1.9",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; no reset
    for ev in EVIDENCE:
        store.add(ev)
    for s in SUPPORT:
        store.add(s)
    store.add(POSITION)
    print(f"appended {len(EVIDENCE)} evidence + {len(SUPPORT)} support edges; "
          f"moved reasoning-pattern -> candidate, conf 62 (was hypothesis 40)")


if __name__ == "__main__":
    main()
