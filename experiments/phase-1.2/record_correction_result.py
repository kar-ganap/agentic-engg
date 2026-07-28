"""Capture the §1.2 BEHAVIORAL-supervision result (Phase 1.2 Thread C, 2026-07-27). The powered run
confirmed §1.2's ACTUAL claim (behavioral supervision, task-success DV) cross-provider, discharging
the two biggest reviewer caps (behavioral-untested; single-provider). Both falsifier clauses failed.
Moves compaction-preserve-failures 68 -> 78, candidate -> ACTIVE (the reviewers' pre-registered
path-to-active). User-confirmed: 78 / active. Append-only; latest-wins. Run ONCE.

    uv run python experiments/phase-1.2/record_correction_result.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Evidence, Leg, Position, Retraction, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")
SRC = "experiments/phase-1.2/results-correction.md"

EVIDENCE = Evidence(
    "ev-correction-behavioral", "experimental", SRC,
    "BEHAVIORAL test (task-success DV, not payload survival): the agent learns a format "
    "RULE from an early failure, a distractor audit compacts it, then APPLIES it to late "
    "submits (fail-early / no-intervening-success / apply-late). DV = fraction of late records "
    "whose FIRST submit applies the rule. Under STRIP: preserve=1.00 vs summarize=0.00 — Haiku (5 "
    "seeds) AND deepseek-chat (non-reasoning, 3 seeds) → CROSS-PROVIDER. Under PERSIST: flat "
    "1.00 (self-rescue via reasoning). probe-fail=1.00 everywhere (the teaching failure fired). "
    "Confirms §1.2's actual stated claim (Reflexion-style behavioral adaptation), not just the "
    "payload-survival proxy — the reviewers' pre-registered path-to-active.",
    "direct",
)

SUPPORT = Support(
    "compaction-preserve-failures", "ev-correction-behavioral", polarity="supports",
    warrant="discharges the two biggest caps: (1) the DV now measures behavioral adaptation (the "
            "agent fixes its ACTION from the failure → task success), not a datum; (2) the "
            "bite replicates on a NON-reasoning 2nd provider (deepseek-chat) → cross-provider, not "
            "Haiku-strip-only. The pre-registered +12 up-clause fires → active; persist stays null",
)

POSITION = Position(
    id="compaction-preserve-failures",
    title="Compaction should preserve failures verbatim — iff reasoning ephemeral (common: null)",
    stance=(
        "Under mid-loop compaction, preserving FAILURES verbatim is REDUNDANT when reasoning "
        "persists (the common case — the model self-rescues the failure into its own tokens; "
        "cross-provider null). It MATTERS only when reasoning is ephemeral. Now BEHAVIORALLY "
        "CONFIRMED (Thread C, the reviewers' path-to-active): a failure carrying a corrective the "
        "agent must APPLY (a format rule): under strip, preserve enables correction (late submit "
        "succeeds, TASK-SUCCESS DV) 1.00 vs summarize 0.00, on Haiku (5 seeds) AND deepseek-chat "
        "(non-reasoning, 3 seeds) — a CROSS-PROVIDER bite. So the boundary (preserve iff ephemeral "
        "reasoning) holds for the ACTUAL behavioral claim (Reflexion), not just payload "
        "survival. Chroma-eviction dominates; Manus keep-it-in is the narrow ephemeral-reasoning "
        "special case. Capped by the engineered fail-early/apply-late task structure."
    ),
    confidence=78,
    status="active",
    registered="2026-07-27",
    updated="2026-07-27",
    legs=(
        Leg("behavioral-supervision-confirmed", 80,
            "the ACTUAL claim: agent adapts its ACTION from the failure (task-success DV); strip "
            "preserve 1.00 vs summarize 0.00, per-seed-consistent"),
        Leg("cross-provider-bite", 78,
            "replicates on deepseek-chat (non-reasoning) — the single-provider cap is discharged"),
        Leg("persist-null-cross-provider", 80,
            "flat 1.00 all policies on Haiku + DeepSeek — self-rescue; preservation redundant"),
        Leg("reasoning-persistence-boundary", 75,
            "clearing tool-results is a no-op iff reasoning persists — now on both a payload and a "
            "behavioral DV"),
        Leg("regime-generality", 58,
            "engineered fail-early/apply-late + format-rule task; a natural-failure / production "
            "task untested — the remaining cap"),
    ),
    preconditions=(
        "Haiku strip (ephemeral CoT) + deepseek-chat (non-reasoning) reach the bite; persist "
        "(default, reasoning retained) is the null",
        "correction task: submit_record enforces a format learned from a failure; fail-early "
        "(R1-TEST) → distractor audit compacts it → apply-late (R2/R3), no intervening success",
        "task-success DV (first-attempt format-correctness); reasoning × policy × 5 seeds (Haiku), "
        "×3 (deepseek-chat); budget 700, keep_last 2, loop_guard OFF",
    ),
    retraction=(
        Retraction("down", 18,
                   "the behavioral bite fails on a less-engineered / production failure task, "
                   "or a downstream multi-step goal DV", ("regime-generality",)),
        Retraction("down", 15,
                   "persist shows preserve>summarize on a wider set — the self-rescue story breaks",
                   ("persist-null-cross-provider",)),
    ),
    edges=(("tension_with", "2.1"),),
    synthesis_ref="1.2",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; latest-wins
    store.add(EVIDENCE)
    store.add(SUPPORT)
    store.add(POSITION)
    print("captured: compaction-preserve-failures 68 -> 78, ACTIVE (behavioral confirm, "
          "cross-provider); trajectory 65->68->74->68->78")


if __name__ == "__main__":
    main()
