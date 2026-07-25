"""§1.1 position-forming task pool (Thread B, debate #2) — DRAFT for user review.

Same design as pool_signal_density.py, new domain (tool design / agent loops). Target question:
"should tool definitions be STABLE across a run (no mid-loop mutation)?" Orthogonal rival
distractors are same-topic (tool design) concerns that DON'T decide the *mutation* question.

(Distractor dataclass duplicated from pool_signal_density for now; lifts to src/stance/reasoning
when the builder lands.)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Distractor:
    id: str
    axis: str           # description|return-format|error-handling|parallelism|benchmark|framework
    confusability: str  # high | mid
    realism: str        # synthetic | real (verify §0.16 before use)
    text: str


DEBATE = "Should tool definitions be stable across a run — i.e., never mutated mid-loop?"

# The correct position the rubric grades toward (fixed by the TARGETS).
CORRECT_POSITION = (
    "Yes — set tools once at run start and don't mutate mid-loop; handle state-dependent "
    "availability in the latest user message / tool_choice. Two legs: cache-economics (measured "
    "~90: mutating the tool block busts the cached prefix, ~7x a stable one) and model-coherence "
    "(~65, literature-only) — headline ~80, capped by the untested coherence leg. A good answer "
    "states the stance + both legs + a falsifiable retraction."
)

# Targets = decisive real evidence already in data/graph.
TARGET_EVIDENCE_IDS = ("ev-manus", "ev-exb")

DISTRACTORS: tuple[Distractor, ...] = (
    # ---- HIGH: orthogonal rival tool-design concerns (axis ⟂ mutate-or-not) ----
    Distractor(
        "d-desc-1", "description", "high", "real",  # Anthropic tool-design blog (verified)
        "Anthropic's tool-design guidance: write tool descriptions as if onboarding a new hire — "
        "make implicit context, query formats, and term definitions explicit; clearer specs "
        "measurably raise agent tool-use.",
    ),
    Distractor(
        "d-ret-1", "return-format", "high", "synthetic",
        "Whether a tool returns a verbose or a compact result shape changes downstream success on "
        "tasks that depend on the returned handle.",
    ),
    Distractor(
        "d-err-1", "error-handling", "high", "synthetic",
        "Agents that retry a failed tool call with the error fed back complete more tasks than "
        "agents that abort on the first failure.",
    ),
    Distractor(
        "d-par-1", "parallelism", "high", "synthetic",
        "Issuing independent tool calls in parallel rather than sequentially cuts end-to-end "
        "latency at equal task success.",
    ),
    # ---- MID: same topic, WRONG QUESTION TYPE (measurement / construction), non-decisive
    Distractor(
        "d-bench-1", "benchmark", "mid", "synthetic",
        "On a tool-use benchmark, agent A completes 68% of tasks and agent B 61% "
        "(a cross-agent score table).",
    ),
    Distractor(
        "d-fw-1", "framework", "mid", "synthetic",
        "A new agent framework ships typed tool schemas and a unified tracing UI "
        "(a library / construction result).",
    ),
)

# ---- TRAPS: documented so we (and the builder) never add them as distractors ----
# 1. "Models degrade past ~N tools; prune to a minimal per-task set" — this IS the #3 carry-swap
#    axis (tool-count -> swap) => DECISIVE for §1.1's scope (argues FOR mutating). The §1.1 analog
#    of §1.8's RAG-echoes-primary trap.
# 2. "Prune/swap unused tools mid-run" — literally advocates mutation => decisive, OPPOSITE answer.
# 3. "Models robustly ignore stale tool refs; mutation has no cost" => decisive CONTRADICT.
# 4. "Prompt caching makes a cached prefix ~10x cheaper" — the MECHANISM behind §1.1's cache leg =>
#    decisive SUPPORT (it's evidence FOR the target, not orthogonal noise).
NEAR_MISSES_EXCLUDED = (
    "tool-count/selection (= #3 carry-swap, decisive)",
    "prune-mid-run (advocates mutation)",
    "stale-refs-harmless (contradict)",
    "prompt-caching-mechanics (supports)",
)
