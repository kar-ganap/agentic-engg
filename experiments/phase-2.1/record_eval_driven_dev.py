"""Record B5 (eval-driven-dev) evidence for §1.10 `tool-selection` (2026-07-28).

Adds the Evidence + Support ONLY — the Position is HELD untouched (user torn between nudge-up and
hold; the possible +confidence and the statement enrichment are DEFERRED to the phase-close
three-reviewer pass, which sees all of Phase 2.1). B5 strengthens the name>description core via a
new test (`correct_only` fails) but is DeepSeek-only. Append-only; latest-wins. Run ONCE.

    uv run python experiments/phase-2.1/record_eval_driven_dev.py
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Evidence, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")
SRC = "experiments/phase-2.1/results-eval-driven-dev.md"

EVIDENCE = Evidence(
    "ev-eval-driven-dev", "experimental", SRC,
    "Eval-driven-dev follow-up (Module 6 L88): can improving the DESCRIPTION overcome the §1.10 "
    "name-bias? Held-out selection (reserved seeds 101-110, pre-namespace, DeepSeek v4-flash, "
    "mechanical first-tool DV). DETERMINISTIC single-clause isolation: adding the request verb "
    "'look up' to the CORRECT tool's description (`correct_only`) does NOT recover — 0.30 @N=3,5, "
    "no better than baseline; the correct `search_users` still loses to `lookup_user` whose NAME "
    "carries the verb. Recovery comes ONLY from an EXCLUSIONARY clause on the ATTRACTOR "
    "(`attractor_only` = 'NOT for customer lookup' -> 1.00 @N=3,5). A free-rewrite LLM improver "
    "recovered to 1.00, but the isolation shows the lever was the attractor-nerf, not the "
    "correct-tool edit. => name>description CONFIRMED on a new test (the correct tool's "
    "description carrying the verb still loses); the only description-side lever that works is "
    "dis-endorsing the competitor, not improving the correct tool. Caveat: DeepSeek-only (no "
    "Claude anchor); a maximally aggressive correct-tool clause untested.",
    "corroborating", date="2026-07-28",
)

SUPPORT = Support(
    "tool-selection", "ev-eval-driven-dev",
    warrant="`correct_only` is a clean mechanical test complementary to the original verb-swap: "
            "the verb-swap showed the name-matched sibling wins; B5 shows you cannot fix it by "
            "improving the correct tool's description (verb included) -> the name>description core "
            "is strengthened, not qualified. The exclusionary-attractor lever is a genuine nuance "
            "(descriptions are not fully ignored) but it does NOT rescue the correct tool, so it "
            "does not contradict the core. Bearing = supports; DeepSeek-only, so the confidence "
            "move is deferred to the phase-close reviewer pass.",
    polarity="supports", date="2026-07-28",
)


def main() -> None:
    store = GraphStore(GRAPH_DIR)
    store.add(EVIDENCE)
    store.add(SUPPORT)
    print("recorded ev-eval-driven-dev + support -> tool-selection (Position HELD; nudge deferred)")


if __name__ == "__main__":
    main()
