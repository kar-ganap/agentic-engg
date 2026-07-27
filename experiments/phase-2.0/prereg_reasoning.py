"""Thread B pre-registration (Phase 2.0) — APPENDS the prior on which reasoning pattern for
position-forming to the evidence graph, BEFORE the comparison runs (Substrate Discipline #1).

A LIVE hypothesis (status="hypothesis"), NOT a transcription — the experiment will MOVE it via
`record_experiment_result`. This APPENDS to the committed `data/graph/` (the append-only living
store); it does NOT reset. (`seed_graph.py` was the one-time bootstrap and DOES reset — do not
re-run it, or you lose appends like this one; new records go through append scripts / the surfaces.)

Headline framing (B): pick the pattern to wire into the spine. Pre-registered bonus (A): the §1.8
interaction — does a retrieval loop beat stuffing once the evidence is large + confusable enough
to rot? Priors (user-set): primary 40 / ranking 40 / reflection 45; headline capped at 40.

    uv run python experiments/phase-2.0/prereg_reasoning.py     # run once (appends)
"""

from __future__ import annotations

from pathlib import Path

from stance.graph.models import Leg, Position, Retraction
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")


def main() -> None:
    store = GraphStore(GRAPH_DIR)  # append-only; no reset
    store.add(Position(
        id="reasoning-pattern",
        title="Which reasoning pattern for position-forming over an evidence graph",
        stance="Pragmatic (B): compare a no-loop baseline vs ReAct / plan-execute / reflection on "
               "position quality x token-cost x latency, to pick the loop to wire into the spine. "
               "Pre-registered bonus (A, the interaction): a retrieval loop (ReAct) beats the "
               "stuff-it baseline ONLY once the evidence set is large AND confusable enough to "
               "trigger the §1.8 diffuse-competition collapse — winning by sidestepping the rot, "
               "not on cost; below that regime the baseline ties.",
        confidence=40, status="hypothesis", registered="2026-06-29", updated="2026-06-29",
        legs=(
            Leg("primary-interaction", 40, "§1.8 rot makes a retrieval loop beat stuffing as "
                "evidence grows+confuses — RISKY: agentic §1.8-rot failed to induce 3x (#4)"),
            Leg("ranking-react-vs-plan", 40, "ReAct >= plan-execute: adaptivity beats lookahead "
                "on small/known evidence; plan-execute earns keep only at large sets"),
            Leg("reflection-vs-reputation", 45, "reflection lift < its HumanEval reputation — our "
                "feedback is a fuzzy rubric, not crisp pass/fail (self-review-on-noise risk)"),
        ),
        preconditions=(
            "position-forming over the seeded evidence graph (not synthetic puzzles)",
            "evidence-set-size swept AND >=1 deliberately-confusable cell (else the primary is "
            "untestable — the #4/§0.20 control-never-fires trap)",
            "grader = the FUZZY rubric (a crisp/oracle grader smuggles in reflection's home edge)",
            "DeepSeek-primary, Claude-anchored (§0.8)",
        ),
        retraction=(
            Retraction("down", 30, "baseline competitive across ALL sizes/confusabilities — the "
                       "§1.8 rot is not inducible (a 4th null after #4); primary refuted",
                       ("primary", "null")),
            Retraction("down", 15, "plan-execute tops ReAct (lookahead helps even on small/known "
                       "evidence)", ("ranking",)),
            Retraction("down", 15, "reflection clearly dominates — crisp-feedback reputation "
                       "transfers to the fuzzy rubric", ("reflection",)),
        ),
        synthesis_ref=None,
    ))
    print("appended pre-registration: reasoning-pattern (hypothesis, conf 40)")


if __name__ == "__main__":
    main()
