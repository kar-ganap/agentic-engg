"""Capture §1.2 (compaction-preserve-failures) from the powered Phase 1.2 Thread-B run (2026-07-27).

Both pre-registered falsifier clauses FAILED -> §1.2 confirmed own-substrate (conditional). Haiku
2×3×5: strip preserve=1.00 vs summarize=0.13 (consistent every seed); persist flat 1.00; flag ==
uniform. DeepSeek persist flat 1.00 -> cross-provider NULL corroboration. Moves 68 (hypothesis) ->
74 (candidate). Append-only; latest-wins. Run ONCE.

    uv run python experiments/phase-1.2/record_compaction_result.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Evidence, Leg, Position, Retraction, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")
SRC = "experiments/phase-1.2/results-compaction.md"

EVIDENCE = Evidence(
    "ev-compaction", "experimental", SRC,
    "Breadcrumb-chain audit, ~530-token BLOCKED transcripts with a release ref buried inside; DV = "
    "ref-recall in file_report (mechanical). Haiku 2×3×5 (reasoning{persist,strip} × "
    "policy{preserve,flag,uniform}): STRIP (ephemeral reasoning) preserve=1.00 on all 5 seeds vs "
    "summarize (flag==uniform)=0.13 (0.00-0.33/seed; delta +0.67..+1.00) -> preserving the failure "
    "VERBATIM keeps the buried datum, summarizing loses it. PERSIST = flat 1.00 everywhere (the "
    "model self-rescues the ref into its own reasoning, which compaction doesn't touch) -> null. "
    "DeepSeek v4-flash persist = flat 1.00 (cross-provider null). flag==uniform -> the datum is in "
    "the failure body, a one-line signal isn't enough. Mechanism verified: DeepSeek's "
    "reasoning_content literally contains the ref (why its reasoning can't be ablated, §0.x).",
    "direct",
)

SUPPORT = Support(
    "compaction-preserve-failures", "ev-compaction", polarity="supports",
    warrant="the reasoning-persistence IV isolates the mechanism: strip removes the self-rescue "
            "channel so the failure lives only in the tool-result -> preserving it (verbatim) is "
            "load-bearing; persist restores self-rescue -> null. Consistent across 5 seeds, "
            "mechanical DV; the persist null holds cross-provider (Haiku + DeepSeek)",
)

POSITION = Position(
    id="compaction-preserve-failures",
    title="Compaction should preserve failures verbatim — iff the agent's reasoning is ephemeral",
    stance=(
        "Under mid-loop compaction, preserving FAILURES verbatim retains goal-critical information "
        "that summarizing them away loses — CONFIRMED own-substrate (Haiku, 5 seeds: ref-recall "
        "1.00 vs 0.13), but CONDITIONAL on the agent's reasoning being EPHEMERAL. With persisted "
        "reasoning a capable model self-rescues the salient failure-content into its own tokens -> "
        "NULL (flat 1.00), corroborated cross-provider (Haiku + DeepSeek v4-flash). It is the "
        "VERBATIM failure that matters, not a distilled signal (flag ~ uniform: the datum lives in "
        "the failure body). The BITE is single-provider (DeepSeek's stateful reasoning_content "
        "pins it to persist, un-ablatable — §0.x); the NULL is cross-provider. Mechanical DV (no "
        "judge). Regime is somewhat engineered (large un-extractable failure + ephemeral "
        "reasoning) — a real but specific corner."
    ),
    confidence=74,
    status="candidate",
    registered="2026-07-27",
    updated="2026-07-27",
    legs=(
        Leg("persist-null-cross-provider", 80,
            "flat 1.00 across all policies on Haiku AND DeepSeek — the model self-rescues via its "
            "own reasoning, which compaction doesn't touch"),
        Leg("preserve-beats-summarize-under-strip", 78,
            "1.00 vs 0.13, consistent every seed (delta +0.67..+1.00, n=5); the bite"),
        Leg("verbatim-not-signal", 75,
            "flag == uniform (0.13) — the buried datum needs the full failure, not a code"),
        Leg("bite-single-provider", 55,
            "the preserve>summarize bite is Haiku-only; DeepSeek can't reach strip (stateful "
            "reasoning_content) — the cap"),
        Leg("regime-generality", 55,
            "engineered regime (large un-extractable failure + ephemeral CoT); natural-failure "
            "info and a downstream-task DV untested"),
    ),
    preconditions=(
        "Haiku (claude-haiku-4-5) substrate — content ablation must reach the model; DeepSeek's "
        "reasoning_content is stateful (native 400s, shim re-injects) so it can't reach strip",
        "breadcrumb-chain task; ~530-token BLOCKED transcripts with a buried ref; ref-recall DV",
        "reasoning{persist,strip} × policy{preserve,flag,uniform} × 5 seeds; budget 800, keep_last "
        "2, loop_guard OFF",
    ),
    retraction=(
        Retraction("down", 20,
                   "the bite fails to replicate on a less-engineered task (natural failure info, "
                   "not a buried random datum) or on a downstream task-success DV",
                   ("regime-generality",)),
        Retraction("down", 15,
                   "persist shows preserve>summarize on a wider set — the self-rescue story breaks",
                   ("persist-null-cross-provider",)),
        Retraction("up", 10,
                   "a NON-reasoning 2nd provider replicates the strip bite -> cross-provider bite",
                   ("bite-single-provider",)),
    ),
    edges=(("tension_with", "2.1"),),  # informs the Manus-keep-it-in vs Chroma-rot tension
    synthesis_ref="1.2",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; latest-wins
    store.add(EVIDENCE)
    store.add(SUPPORT)
    store.add(POSITION)
    print("captured: compaction-preserve-failures -> candidate, conf 74 (trajectory 65->68->74); "
          "strip bite + cross-provider persist null")


if __name__ == "__main__":
    main()
