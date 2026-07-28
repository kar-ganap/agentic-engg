"""Capture position #2 `tool-selection` from the Phase 1.2 Thread-A run (2026-07-27).

Both pre-registered falsifier clauses FAILED to fire -> #2 confirmed and SHARPENED. The main
sweep + two controls (N=2 fill, verb-swap) + a Haiku anchor turned "density degrades" into a
causally-pinned, cross-provider LEXICAL mechanism. Moves 55 (hypothesis) -> 78 (candidate).
Append-only; latest-wins. Run ONCE.

    uv run python experiments/phase-1.2/record_selection_result.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Evidence, Leg, Position, Retraction, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")
SRC = "experiments/phase-1.2/results-selection.md"

EVIDENCE = Evidence(
    "ev-tool-selection", "experimental", SRC,
    "Selection accuracy (first-tool == expected, mechanical DV — no judge) over density_n x "
    "{pre-,post-namespace} x 5 seeds, DeepSeek v4-flash + Haiku anchor. PRE-namespace is a "
    "STEP-FUNCTION, not a count-gradient: N=0,1 hold 1.00 (N=1 = `find_user`, shares the entity "
    "token 'user'), then collapse the instant `lookup_user` enters — N=2/3 -> 0.00, N=5 -> 0.20 "
    "(DeepSeek); N=1 1.00 -> N=3 0.20 (Haiku). EVERY wrong pick, both providers, was the one "
    "sibling `lookup_user` whose NAME matches the prompt verb ('Look up the customer'), beating "
    "the correct `search_users` whose DESCRIPTION ('Find a customer by name') is the best semantic "
    "match. POST-namespace holds 1.00 at every density (both providers). VERB-SWAP causal control "
    "(move 'lookup' onto the correct tool -> `lookup_users`): 100% recovery, both providers "
    "(prediction was >=0.80). => selection is governed by lexical name<->request-verb alignment, "
    "not tool count; namespacing recovers by making the entity token the unique disambiguator.",
    "direct",
)

SUPPORT = Support(
    "tool-selection", "ev-tool-selection", polarity="supports",
    warrant="the verb-swap is a clean causal test (100% recovery when the matching verb-token "
            "moves to the correct tool) and it replicates on an independent provider (Haiku, same "
            "attractor, same step-function) -> the mechanism is lexical + cross-provider, not a "
            "cheap-model or count artifact; the mechanical DV removes the fuzzy-judge caveat",
)

POSITION = Position(
    id="tool-selection",
    title="Tool selection is governed by lexical name<->request alignment, not tool count",
    stance=(
        "Confusable-sibling PRESENCE — not count — degrades first-tool selection: a sibling whose "
        "NAME lexically matches the request verb captures the call the instant it appears "
        "(step-function; N=1 entity-share holds, N=2 verb-match collapses), overriding the "
        "semantically-correct description. Confirmed cross-provider (DeepSeek v4-flash + Haiku, "
        "same attractor `lookup_user`) and causally pinned by a verb-swap (move the matching verb "
        "onto the correct tool -> 100% recovery). Two fixes: (1) NAMESPACE BY ENTITY — "
        "`{entity}_search` makes the entity token the unique disambiguator -> 1.00 at every "
        "density, both providers; "
        "(2) equivalently, align the tool's name-verb to the expected request. DV is mechanical "
        "(deterministic first-tool match). Scope: single task template + single verb-pair so far."
    ),
    confidence=78,
    status="candidate",
    registered="2026-07-27",
    updated="2026-07-27",
    legs=(
        Leg("namespacing-recovers", 85,
            "post-namespace 1.00 at every density on BOTH providers; entity token becomes unique"),
        Leg("lexical-verb-capture", 80,
            "verb-swap causal test: move 'lookup' onto the correct tool -> 100% recovery, both "
            "providers; the correct description loses to the matching name"),
        Leg("presence-not-count", 78,
            "step-function: N=1 (find_user, entity-share) holds 1.00, collapse at N=2 when the "
            "verb-matching sibling enters; N=5's 0.20 is floor-noise, not a gradient"),
        Leg("cross-provider", 72,
            "DeepSeek v4-flash + Haiku: same specific attractor, same step, same namespacing + "
            "verb-swap recovery (Haiku a hair more robust: N=3 0.20 vs 0.00)"),
        Leg("template-generality", 55,
            "single task template ('Look up the customer X') + single verb-pair (lookup/look up); "
            "breadth across verbs/domains untested -> the path to active"),
    ),
    preconditions=(
        "DeepSeek v4-flash (primary) + Haiku anchor; mechanical first-tool DV (no LLM judge)",
        "single template 'Look up the customer X'; pre-siblings = synonyms/cross-entity, "
        "post = {entity}_search; correct-tool description is the best semantic match (the lure)",
        "N in {0,1,2,3,5} x {pre,post} x 5 seeds; verb-swap control at N in {3,5}",
    ),
    retraction=(
        Retraction("down", 20,
                   "the lexical capture fails to replicate on a 2nd task template / verb-pair "
                   "(it was specific to 'lookup'/'look up')", ("template-generality",)),
        Retraction("down", 15,
                   "a 3rd provider holds 1.00 pre-namespace at N>=3 (the 2-provider agreement was "
                   "luck)", ("cross-provider",)),
        Retraction("up", 12,
                   "a 2nd template/verb-pair replicates the capture AND the verb-swap recovery "
                   "-> promote to active", ("template-generality",)),
    ),
    synthesis_ref="1.10",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; latest-wins
    store.add(EVIDENCE)
    store.add(SUPPORT)
    store.add(POSITION)
    print("captured: tool-selection -> candidate, conf 78 (trajectory 55->78); "
          "lexical verb-capture, cross-provider (DeepSeek + Haiku), verb-swap causal")


if __name__ == "__main__":
    main()
