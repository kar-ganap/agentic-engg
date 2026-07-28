"""Post-three-reviewer-pass adjustments (Phase 1.2 close, 2026-07-27). Appends the corrected
Positions (latest-wins; the trajectory stays in the append-only history). The pass converged:
- §1.2 compaction: the 68->74 up-move was NOT earned (bite engineered-guaranteed, DV = payload
  survival NOT the stance's behavioral-supervision claim, single-provider). Revert 74 -> 68; reframe
  to lead with the null; the "REFUTED" down-5-10 clause reopened to untested.
- §1.10 tool-selection: the "degrades/failure" framing is a DV-labeling artifact; the mechanism
  (name>description weighting, verb-swap-isolated) is what's earned. Shave 78 -> 74; retitle.
User-confirmed confidences: §1.2 -> 68, §1.10 -> 74. Run ONCE.

    uv run python experiments/phase-1.2/record_postreview_adjustments.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Leg, Position, Retraction
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")

COMPACTION = Position(
    id="compaction-preserve-failures",
    title="Compaction should preserve failures verbatim — iff reasoning ephemeral (common: null)",
    stance=(
        "REVIEWER-ADJUSTED (three-reviewer pass, 2026-07-27) — leads with the NULL. Whether to "
        "preserve failures under compaction depends on reasoning-persistence: in the common case "
        "(reasoning persisted — default tool loops; forced for DeepSeek reasoning_content + "
        "Anthropic extended-thinking) the model self-rescues the failure's content into its own "
        "tokens, so preservation is REDUNDANT (a no-op). Only when the compactor ALSO strips "
        "reasoning (ephemeral CoT — e.g. Anthropic clear_thinking) does verbatim preservation bite "
        "(Haiku, 5 seeds; single-provider, engineered corner). The own-substrate DV tested PAYLOAD "
        "SURVIVAL, not the stance's literature BEHAVIORAL claim (Reflexion/ReAct) — that "
        "is UNTESTED (path-to-active). Base claim = Reflexion; self-rescue = scratchpad/CoT; the "
        "contribution is the reasoning-persistence BOUNDARY. Chroma-eviction dominates; Manus "
        "keep-it-in is the narrow special case."
    ),
    confidence=68,
    status="candidate",
    registered="2026-07-27",
    updated="2026-07-27",
    legs=(
        Leg("persist-null-cross-provider", 80,
            "flat 1.00 all policies on Haiku AND DeepSeek — self-rescue via reasoning (DeepSeek's "
            "null is FORCED: it can't reach strip, §0.27)"),
        Leg("reasoning-persistence-boundary", 70,
            "the genuine contribution: clearing tool-results is a no-op iff reasoning persists"),
        Leg("verbatim-not-signal", 65,
            "flag==uniform (0.13) — but partly a keep_last positional artifact; the down-5-10 "
            "behavioral-lesson clause is UNTESTED, not refuted"),
        Leg("bite-single-provider", 50,
            "the preserve>summarize bite is Haiku-only; near-true-by-construction (§0.28)"),
        Leg("regime-generality", 50,
            "engineered regime + payload DV; behavioral + downstream DV untested"),
    ),
    preconditions=(
        "Haiku substrate (DeepSeek can't reach strip — reasoning_content stateful, §0.27)",
        "breadcrumb-chain task; ~530-tok BLOCKED transcript, buried ref; ref-recall = PAYLOAD "
        "survival (NOT behavioral supervision — the stance's actual claim is untested)",
        "reasoning{persist,strip} × policy{preserve,flag,uniform} × 5 seeds; keep_last=2 (the 0.13 "
        "summarize mean is positional; honest contrast on compacted failures = 1.00 v 0.00)",
    ),
    retraction=(
        Retraction("up", 12,
                   "a BEHAVIORAL-supervision test (failure carries a corrective the agent must "
                   "APPLY; task-success DV; learn-early/apply-late/no-intervening-use) confirms "
                   "its actual claim, on a NON-reasoning provider", ("behavioral", "active")),
        Retraction("down", 15,
                   "persist shows preserve>summarize on a wider set — self-rescue story breaks",
                   ("persist-null-cross-provider",)),
    ),
    edges=(("tension_with", "2.1"),),
    synthesis_ref="1.2",
)

SELECTION = Position(
    id="tool-selection",
    title="Models weight tool-NAME lexical match over tool-DESCRIPTION semantics",
    stance=(
        "REVIEWER-ADJUSTED (three-reviewer pass, 2026-07-27) — reframed off 'degrades/failure' to "
        "the mechanism. When a sibling tool's NAME lexically matches the request verb, it CAPTURES "
        "the agent's first tool choice over a tool with the best-matching DESCRIPTION — verb-swap "
        "isolates it causally (move 'lookup' onto the right tool -> it wins). PREDICTABLE "
        "and FIXABLE BY NAMING, not a breakdown: the model applies the same rule in both "
        "arms, and picking a tool named lookup_user for 'look up' is a defensible synonym choice — "
        "so it is selection NON-DETERMINISM under naming, not failure (the DV counts a reasonable "
        "synonym as 'wrong' by the pre-registered expected_tool). Fix: namespace by entity, which "
        "works by REMOVING the verb-collision (same mechanism). Mechanism + causal design are both "
        "established (HANS/shortcut-learning); the contribution is the clean tool-selection demo. "
        "Cross-provider (Haiku+DeepSeek) rules out cheap-model-only but both instantiate HANS. One "
        "verb-pair (the cap). Mechanical DV."
    ),
    confidence=74,
    status="candidate",
    registered="2026-07-27",
    updated="2026-07-27",
    legs=(
        Leg("name-over-description-weighting", 78,
            "the mechanism, verb-swap-isolated (post-swap 'lookup' is only in the winner's name; "
            "its description still says 'Find a customer by name')"),
        Leg("presence-not-count", 76,
            "N=1 (find_user, entity-share) holds 1.00; collapse at N=2 when the verb-matching "
            "sibling enters — but 'not count' = not count-of-NON-verb-matching siblings"),
        Leg("cross-provider", 70,
            "same attractor on Haiku + DeepSeek; rules out cheap-model-only, but both instantiate "
            "the known HANS lexical-overlap heuristic (expected, not independent)"),
        Leg("namespacing-removes-collision", 70,
            "post-namespace recovery is ENTAILED by the mechanism (deletes the collision), not "
            "a separate disambiguation benefit"),
        Leg("template-generality", 50,
            "one task template + one verb-pair (lookup/look up) — the cap; path to active"),
    ),
    preconditions=(
        "DeepSeek v4-flash + Haiku; single template 'Look up the customer X'; one verb-pair",
        "N∈{0,1,2,3,5} × {pre,post} × 5 seeds; verb-swap at N∈{3,5}; mechanical first-tool DV",
        "DV counts a defensible synonym pick as 'wrong' -> measures selection DETERMINISM, not "
        "task failure",
    ),
    retraction=(
        Retraction("down", 20,
                   "the capture fails to replicate on a 2nd task template / verb-pair",
                   ("template-generality",)),
        Retraction("up", 10,
                   "a 2nd template/verb-pair replicates the name>description capture -> active",
                   ("template-generality",)),
    ),
    synthesis_ref="1.10",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; latest-wins
    store.add(COMPACTION)
    store.add(SELECTION)
    print("post-review: compaction-preserve-failures 74->68; tool-selection 78->74 (reframed)")


if __name__ == "__main__":
    main()
