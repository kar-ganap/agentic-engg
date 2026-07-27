"""Cross-provider firm of `reasoning-pattern` — Kimi K3 replicates both mechanisms (2026-07-26).

Focused cross-provider run (§1.8 + §3.8, matched config): on Kimi K3 (2.8T flagship — a very
different family from DeepSeek v4-flash), BOTH earned mechanisms replicate directionally. retrieve>
stuff-under-dilution holds; reflection=systematic-caution holds on clean data (K3's verbose 3-call
reflection needed the 8192 cap — 7/20 parse-fails @4096 -> 2/19 @8192; NOT a mechanism failure).
Firms 58 -> 63, still candidate (grader unvalidated, 1-2 debates/regime). Append-only. Run ONCE.

    uv run python experiments/phase-2.0/record_reasoning_xprovider.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Evidence, Leg, Position, Retraction, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")
SRC = "experiments/phase-2.0/results-reasoning.md#xprovider"

EVIDENCE = Evidence(
    "ev-reason-xprovider", "experimental", SRC,
    "Cross-provider (Kimi K3, 2.8T flagship, vs DeepSeek v4-flash), §1.8+§3.8 matched config: BOTH "
    "earned mechanisms replicate. retrieve>stuff-under-dilution holds (retrieve arms > collapsed "
    "baseline on both). reflection=systematic-caution holds on clean K3 data: holds the §3.8 hedge "
    "(conf 46-54 ~ 45), wins §3.8 (13-17), lowers confidence uniformly (Δ-10 vs baseline; DeepSeek "
    "Δ-15). K3's verbose 3-call reflection needed the 8192 cap (7/20 parse-fails @4096 -> 2/19 "
    "@8192) — a measurement precondition, not a mechanism failure.",
    "corroborating",
)

SUPPORT = Support(
    "reasoning-pattern", "ev-reason-xprovider", polarity="supports",
    warrant="a second, very different model family confirms both mechanisms directionally -> the "
            "taxonomy's mechanisms are not DeepSeek-specific; firms toward cross-provider "
            "(still candidate — grader unvalidated, 1-2 debates/regime)",
)

POSITION = Position(
    id="reasoning-pattern",
    title="Which reasoning pattern for position-forming over an evidence graph",
    stance=(
        "No universal best reasoning pattern; effectiveness = alignment between a pattern's "
        "inductive bias and the debate's epistemic structure. Two mechanisms, EARNED by a "
        "confound-removing re-test and now CONFIRMED cross-provider on Kimi K3 (a 2.8T flagship, a "
        "very different family): (1) reflection = SYSTEMATIC CAUTION — uniformly lowers confidence "
        "(survives a neutral critique; Δ-10 to -15 vs baseline), which miscalibrates "
        "confident-convergent debates (§1.8) but correctly reins in the overclaiming a hedge "
        "induces (§3.8, holds the ~45 hedge, wins); (2) RETRIEVING A SUBSET beats STUFFING the "
        "set under §1.8 dilution — GENERIC (plan ~ react; 'commit-to-few' was triage, "
        "REFUTED). §1.1 is a null. Winner varies by debate; every arm has a debate it is clearly "
        "bad at. Very-verbose models (K3) need a larger answer cap or multi-call arms parse-fail."
    ),
    confidence=63,
    status="candidate",
    registered="2026-06-29",
    updated="2026-07-26",
    legs=(
        Leg("no-universal-winner", 65,
            "each arm has a clear failure debate; the winner varies by regime"),
        Leg("reflection-systematic-caution", 65,
            "earned on DeepSeek + CONFIRMED clean on Kimi K3 (holds §3.8 hedge 46-54, wins, Δ-10)"),
        Leg("retrieve-beats-stuff-under-dilution", 62,
            "replicates cross-provider (retrieve arms > collapsed baseline on DeepSeek AND K3); "
            "generic (plan ~ react); 'commit-to-few' refuted"),
        Leg("bias-x-structure", 58,
            "both alignments (caution/§3.8, retrieve/§1.8) hold on both model families"),
        Leg("regime-taxonomy", 40,
            "2 regimes + 1 null; still n=1-2 debates/regime — cross-provider adds families, not "
            "debates per regime"),
    ),
    preconditions=(
        "arms cross-family (DeepSeek v4-flash + Kimi K3); Sonnet-5 fuzzy judge (still UNVALIDATED)",
        "anonymized presentation + neutral critique + prose-EVIDENCE_USE (confound-removed)",
        "very-verbose models need a larger answer cap (K3 reflection @8192; @4096 parse-fails)",
        "5 seeds/cell, N in {4,12,24}; 1-2 debates per regime",
    ),
    retraction=(
        Retraction("down", 25,
                   "one arm dominates >=4/5 debate types in a wider set",
                   ("no-universal-winner",)),
        Retraction("down", 20,
                   "the mechanisms fail to replicate on a THIRD family or at a wider debate set",
                   ("reflection", "retrieve")),
        Retraction("up", 15,
                   "a human-validated grader confirms the arm rankings AND a 2nd debate per regime "
                   "replicates -> promote to active", ("regime-taxonomy",)),
    ),
    synthesis_ref="1.9",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; latest-wins
    store.add(EVIDENCE)
    store.add(SUPPORT)
    store.add(POSITION)
    print("cross-provider firm: reasoning-pattern -> candidate, conf 63 "
          "(trajectory ...->58->63); both mechanisms replicate on Kimi K3")


if __name__ == "__main__":
    main()
