"""Re-capture `reasoning-pattern` after the confound-removing re-test (2026-07-26).

The re-test (anonymized presentation -> triage impossible; neutral critique; prose-EVIDENCE_USE)
DISCRIMINATED: plan-execute's §1.8 "commit-to-few" win EVAPORATED (plan ≈ react, order flips by N —
it was teaser-triage), while reflection's §3.8 caution win SURVIVED the neutral critique (uniform
confidence-lowering; holds the hedge) — earned, not a keyword artifact. So the position moves back
UP from the interim (50 -> 58, candidate): one artifact killed, one mechanism earned. Append-only;
latest-wins. Run ONCE.

    uv run python experiments/phase-2.0/record_reasoning_retest.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Evidence, Leg, Position, Retraction, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")
SRC = "experiments/phase-2.0/results-reasoning.md#retest"

EVIDENCE = Evidence(
    "ev-reason-retest", "experimental", SRC,
    "Confound-removing re-test (anonymized presentation defeats triage; neutral critique; "
    "prose-EVIDENCE_USE): plan-execute's §1.8 'commit-to-few' win EVAPORATED — with triage "
    "defeated plan ≈ react (10.6/8.2/9.6 vs 15.8/6.2/9.8, order flips by N) — so it WAS "
    "teaser-triage. reflection's §3.8 caution win SURVIVED the neutral critique (uniform "
    "confidence-lowering Δ-9/-9/-18 vs baseline; holds the ~45 hedge at conf 40) — earned. "
    "retrieve>stuff under §1.8 dilution survives generically (baseline collapses to 3.6@N24).",
    "direct",
)

SUPPORT = Support(
    "reasoning-pattern", "ev-reason-retest", polarity="supports",
    warrant="removing the triage + critique-keyword confounds KILLED the plan-specific mechanism "
            "(artifact) but EARNED reflection's caution mechanism (survives neutral critique); the "
            "two earned mechanisms + no-universal-winner define the candidate",
)

POSITION = Position(
    id="reasoning-pattern",
    title="Which reasoning pattern for position-forming over an evidence graph",
    stance=(
        "No universal best reasoning pattern; effectiveness = alignment between a pattern's "
        "inductive bias and the debate's epistemic structure. Two mechanisms EARNED by a "
        "confound-removing re-test (anonymized presentation -> no triage; neutral critique; "
        "prose-EVIDENCE_USE): (1) reflection = SYSTEMATIC CAUTION — uniformly lowers confidence "
        "(survives a neutral critique -> not a keyword artifact), which miscalibrates "
        "confident-convergent debates (§1.8) but correctly reins in the overclaiming a hedge "
        "debate "
        "induces (§3.8, holds the ~45 hedge); (2) RETRIEVING A SUBSET beats STUFFING the full set "
        "under §1.8 diffuse on-axis dilution — but GENERIC (plan-execute ≈ react; the earlier "
        "'commit-to-few' edge was teaser-triage, REFUTED). §1.1 is a null (a robust single fact is "
        "undilutable). Winner varies by debate; every arm has a debate it is clearly bad at."
    ),
    confidence=58,
    status="candidate",
    registered="2026-06-29",
    updated="2026-07-26",
    legs=(
        Leg("no-universal-winner", 65,
            "each arm has a clear failure debate; the winner varies by regime"),
        Leg("reflection-systematic-caution", 60,
            "EARNED — survives the neutral-critique re-test; uniform confidence-lowering "
            "(Δ-9/-9/-18 vs baseline); holds the §3.8 hedge (conf 40)"),
        Leg("retrieve-beats-stuff-under-dilution", 55,
            "survives triage-defeat but GENERIC (plan ≈ react); baseline collapses to 3.6@N24; the "
            "'commit-to-few/plan' sub-claim is REFUTED (was teaser-triage)"),
        Leg("bias-x-structure", 52,
            "two clean alignments: caution/§3.8-hedge, retrieve/§1.8-dilution; plan-specific dead"),
        Leg("regime-taxonomy", 40,
            "2 regimes (dilution / overclaiming) + 1 null (§1.1); n=1-2 debates per regime"),
    ),
    preconditions=(
        "DeepSeek-v4-flash arms + Sonnet-5 fuzzy judge; cross-provider untested",
        "anonymized presentation + neutral critique + prose-EVIDENCE_USE (the §0.25 re-test that "
        "removes the triage + keyword confounds)",
        "5 seeds/cell (9/180 bad rows, all retrieve arms); N∈{4,12,24}",
    ),
    retraction=(
        Retraction("down", 25,
                   "one arm dominates >=4/5 debate types in a wider set",
                   ("no-universal-winner",)),
        Retraction("down", 20,
                   "reflection's caution doesn't replicate cross-provider (is DeepSeek-specific)",
                   ("reflection",)),
        Retraction("down", 15,
                   "retrieve>stuff under dilution fails to replicate cross-provider",
                   ("retrieve",)),
        Retraction("up", 15,
                   "a regime's winner replicates on a 2nd debate AND cross-provider",
                   ("regime-taxonomy",)),
    ),
    synthesis_ref="1.9",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; latest-wins
    store.add(EVIDENCE)
    store.add(SUPPORT)
    store.add(POSITION)
    print("re-captured reasoning-pattern -> candidate, conf 58 (trajectory 40->62->50->58); "
          "reflection EARNED, plan commit-to-few REFUTED, retrieve>stuff generic")


if __name__ == "__main__":
    main()
