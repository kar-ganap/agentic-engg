"""Pre-registration of §1.2 (compaction-preserve-failures) — Phase 1.2 Thread B, BEFORE the powered
run (Substrate Discipline #1). §1.2 was literature-only (65, synthesis §1.2, never in the graph);
this files the OWN-SUBSTRATE test as a hypothesis at the user-set prior 68. The smokes were
instrument-tuning (they forced the design: sequential chain, cache-inclusive trigger, large
transcripts, strip_reasoning, Haiku substrate); the powered Haiku 2×3×5 run moves it. Append once.

    uv run python experiments/phase-1.2/prereg_compaction.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Position, Retraction
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")

POSITION = Position(
    id="compaction-preserve-failures",
    title="Compaction should preserve failures verbatim — iff the agent's reasoning is ephemeral",
    stance=(
        "Under mid-loop compaction, preserving FAILURES verbatim retains goal-critical information "
        "that summarizing them away (to a signal or a stub) loses — CONDITIONAL on the agent's own "
        "reasoning being EPHEMERAL (not persisted across turns). With persisted reasoning a "
        "capable model self-rescues the salient failure-content into its own tokens, so "
        "raw-failure preservation is redundant (null). Own-substrate: Haiku (clean content "
        "ablation). The "
        "persist-regime null is corroborated cross-provider (DeepSeek v4-flash, whose stateful "
        "reasoning_content pins it to persist — §0.x); the strip-regime BITE is Haiku-only "
        "(DeepSeek's reasoning is un-ablatable). Also: it is the VERBATIM failure that matters — "
        "not a distilled signal — the needed datum lives in the failure body, so flag ~ uniform. "
        "Pre-registered prior 68 (user-set): literature (Manus/Anthropic) + a stark smoke signal, "
        "capped by single-provider for the bite and the two conditions."
    ),
    confidence=68,
    status="hypothesis",
    registered="2026-07-27",
    updated="2026-07-27",
    preconditions=(
        "Haiku (claude-haiku-4-5) substrate — the ablation must reach the model; DeepSeek's "
        "stateful reasoning_content defeats content editing (both /anthropic + native, §0.x)",
        "breadcrumb-chain task; ~530-token BLOCKED transcripts with a release ref buried inside; "
        "ref-recall DV (mechanical — parsed from file_report args, no judge)",
        "reasoning{persist,strip} × policy{preserve_failures,summarize_but_flag,summarize_uniform} "
        "× 5 seeds; budget 800, keep_last 2, loop_guard OFF",
    ),
    retraction=(
        Retraction("down", 15,
                   "at 5 seeds, strip+preserve does NOT beat strip+summarize on ref-recall — the "
                   "bite was a fluke", ("strip", "bite")),
        Retraction("down", 15,
                   "persist ALSO shows preserve>summarize — the self-rescue explanation is wrong",
                   ("persist", "self-rescue")),
        Retraction("up", 10,
                   "a NON-reasoning 2nd provider replicates the strip bite — cross-provider for "
                   "the bite, not just the null", ("cross-provider",)),
    ),
    synthesis_ref="1.2",
)


def main() -> None:
    GraphStore(GRAPH_DIR).add(POSITION)  # append-only; first graph record for §1.2
    print("pre-registered: compaction-preserve-failures (§1.2) — hypothesis, conf 68")


if __name__ == "__main__":
    main()
