"""§1.8 position-forming task pool (Thread B) — DRAFT for user review (content is yours to own).

A position-forming task = DEBATE + an evidence set. The set = TARGETS (the graph's real evidence,
which fix the gradeable correct position) + DISTRACTORS (same-topic, NON-decisive records).

Confusability (the primary's knob):
  HIGH = an orthogonal rival "why long-context fails" mechanism — its axis ⟂ competition-vs-length
         (where / form / systems / attention-allocation), so it's maximally confusable yet leaves
         the correct answer unchanged.
  MID  = same topic but the WRONG QUESTION TYPE (measurement / construction) — an easier tell.

AUTHORING RED LINE (§0.22), learned while writing these — subtler than it looks:
  A distractor must assert its OWN mechanism and stay SILENT on competition-vs-length. The moment it
  *denies* competition ("...regardless of the content mix", "...independent of what the tokens say")
  it makes a claim on our axis => DECISIVE => breaks grading. Silent, not opposed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Distractor:
    id: str
    axis: str           # position | form | systems | attention-sink | benchmark | architecture
    confusability: str  # high | mid
    realism: str        # synthetic | real (verify §0.16 before use)
    text: str           # the evidence-like claim: same topic, non-decisive, no lexical give-away


DEBATE = (
    "Under long context, does signal-density / competition — not raw token length — drive the "
    "retrieval/reasoning collapse?"
)

# The correct position the rubric grades toward (fixed by the TARGETS).
CORRECT_POSITION = (
    "Competition / signal-density is the primary driver: at fixed length, adding similar "
    "competitors sharply degrades retrieval; at fixed density, length matters far less. "
    "Confidence ~80; cross-family generality still open (clause b). A good answer states this "
    "stance + a calibrated confidence + a falsifiable retraction (e.g., demote if a neutral "
    "knee appears below a diffuse knee)."
)

# Targets = decisive real evidence already in data/graph (reused, not re-authored).
TARGET_EVIDENCE_IDS = ("ev-ruler", "ev-nolima", "ev-length-ext")

DISTRACTORS: tuple[Distractor, ...] = (
    # ---- HIGH: orthogonal rival mechanisms (axis ⟂ competition-vs-length) ----
    Distractor(
        "d-pos-1", "position", "high", "synthetic",
        "In long inputs, retrieval accuracy depends sharply on WHERE the relevant span sits: items "
        "in the middle are recovered far worse than those near the start or the end.",
    ),
    Distractor(
        "d-form-1", "form", "high", "synthetic",
        "Re-serializing the same passage — chunk boundaries, whitespace, JSON-vs-prose framing — "
        "shifts long-context retrieval scores by double digits.",
    ),
    Distractor(
        "d-sink-1", "attention-sink", "high", "real",  # Xiao 2023, arXiv:2309.17453 (verified)
        "Transformers place a large, near-constant share of attention on the first few tokens "
        "('attention sinks'); removing them destabilizes long-context behavior.",
    ),
    Distractor(
        "d-hop-1", "reasoning-depth", "high", "synthetic",
        "Holding context length fixed, tasks that require chaining several facts (multi-hop) "
        "degrade sharply, while single-hop lookups over the same context stay accurate.",
    ),
    # ---- MID: same topic, WRONG QUESTION TYPE (measurement / construction), non-decisive
    Distractor(
        "d-bench-1", "benchmark", "mid", "synthetic",
        "On a long-context QA leaderboard, model M scores 71, model N 65, model P 58 "
        "(a cross-model score table — reports numbers, argues no driver).",
    ),
    Distractor(
        "d-arch-1", "architecture", "mid", "synthetic",
        "A new linear-attention variant processes 1M-token context at ~4x throughput with a "
        "fixed memory budget (a construction/efficiency result).",
    ),
)

# ---- TRAPS: documented so we (and the builder) never add them as distractors ----
# 1. "Length alone collapses retrieval, independent of competition" — SAME axis, OPPOSITE answer =>
#    DECISIVE (contradicts the target). Belongs in a Type-B *weighing* task, never as a distractor.
# 2. "RoPE fails to extrapolate beyond training length" — a LENGTH-side mechanism => not orthogonal
#    (it argues the length driver); would tilt the answer.
# 3. "Retrieve-then-read beats stuffing" (RAG) — echoes our *primary prediction* (a retrieval loop
#    beats the baseline); a confound here, not a clean §1.8 distractor.
# 4. "KV-cache eviction / quantization degrades with length" (systems) — eviction SCALES with length
#    => length-correlated, not orthogonal (same failure as RoPE). Cut 2026-07-25 on review.
NEAR_MISSES_EXCLUDED = (
    "length-alone (decisive)", "RoPE-extrapolation (length-axis)", "RAG (echoes primary)",
    "systems/KV-eviction (length-correlated)",
)
