"""§3.8 position-forming task pool (Thread B, debate #3) — DRAFT for user review.

Debate #3's distinctive role: the correct answer is a CALIBRATED HEDGE, not a confident stance —
so it tests appropriate uncertainty (and directly probes the prereg's "reflection <= reputation":
does a reflection pass help the model hedge, or reinforce an overclaim?).

Orthogonality test (SHARPER here than §1.8's where⟂what — §3.8's claim is an *explanation*, so a
rival is dangerous when it explains the SAME observation): a distractor is clean only if its TRIGGER
is ABSENT from §3.8's task = a *benign, ambiguous lookup carrying an "UNKNOWN" affordance*. Anything
the task's ambiguity or its UNKNOWN instruction could fire is a rival explanation => trap.

(Distractor dataclass duplicated from the other pools for now; lifts to src/stance/reasoning later.)
"""

from __future__ import annotations

from stance.reasoning.pool import Distractor, Pool

DEBATE = (
    "Under diffuse competition, does higher model capability shift the failure mode "
    "(confabulate -> refuse) and pull the collapse knee earlier?"
)

# Correct position = a HEDGE. The contradicting evidence (ev-loops-to-oops) is a TARGET here — it's
# part of WHY the answer hedges. A good answer is calibrated, not confident.
CORRECT_POSITION = (
    "PLAUSIBLE but UNCONFIRMED: one n=9 comparison (Haiku vs Sonnet) shows the direction (stronger "
    "model refuses, weaker confabulates, earlier knee), BUT the explicit UNKNOWN affordance is an "
    "equally-live cause (not capability), and the parametric-regime literature scales the OPPOSITE "
    "way — so it's a candidate regime-dependent reversal, undecided pending the mandatory "
    "affordance-controlled ladder. Confidence ~45. A good answer hedges, flags the affordance "
    "confound + the contradicting literature, and does NOT state it as established."
)

# Targets: support + inconclusive + CONTRADICTING (the last is load-bearing for the hedge).
TARGET_EVIDENCE_IDS = ("ev-exA-capability", "ev-deepseek-abstain", "ev-loops-to-oops")

DISTRACTORS: tuple[Distractor, ...] = (
    # ---- HIGH: rival failure modes whose TRIGGER is ABSENT from a benign ambiguous lookup ----
    Distractor(
        "d-safe-1", "safety-refusal", "high", "synthetic",
        "Models decline requests they judge harmful or policy-violating — a content-gated refusal "
        "from safety training.",  # trigger = harmful content (absent from a benign lookup)
    ),
    Distractor(
        "d-syco-1", "sycophancy", "high", "synthetic",
        # trigger = a user-stated belief (absent from a neutral lookup)
        "When a user asserts a belief, models often revise their answer to agree with it, even "
        "against the evidence — a social-alignment failure.",
    ),
    Distractor(
        "d-inject-1", "prompt-injection", "high", "synthetic",
        "Adversarial instructions embedded in the input can override a model's intended task "
        "(prompt injection); models differ in resistance.",  # trigger = injected content (absent)
    ),
    # ---- MID: same topic (model reliability), WRONG QUESTION TYPE ----
    Distractor(
        "d-bench-1", "benchmark", "mid", "synthetic",
        "On a factuality benchmark, hallucination rates vary by domain — ~12% on general trivia vs "
        "~22% on specialized law (a cross-DOMAIN rate table — not capability-graded).",
    ),
    Distractor(
        "d-mitig-1", "mitigation", "mid", "synthetic",
        "Grounding generation in retrieved source documents (RAG) lowers factual hallucination "
        "rates (a mitigation method).",
    ),
)

# ---- TRAPS (this space is trap-DENSE because §3.8's claim is an explanation) ----
# The clean test: does the mechanism's TRIGGER fire on §3.8's task? If yes => rival explanation.
# 1. instruction-following (capability -> obeys the UNKNOWN prompt better) => FEEDS the affordance
#    confound (the UNKNOWN instruction is present) => decisive. The sharpest trap.
# 2. general over-refusal / over-caution => ambiguity-triggered (present) => rival explanation.
# 3. sampling / temperature noise => a rival explanation for the n=9 split ("it's just variance").
# 4. abstention-training (trained to say IDK) => a rival refusal cause on the same task => decisive.
# 5. "capability -> more robust retriever" => SAME axis, opposite answer (§3.8's own retraction).
# 6. parametric-hallucination-scaling ("bigger models hallucinate MORE") => that's ev-loops-to-oops,
#    a TARGET (contradicting evidence), not a distractor.
NEAR_MISSES_EXCLUDED = (
    "instruction-following (feeds the UNKNOWN affordance-confound)",
    "general over-refusal (ambiguity-triggered)",
    "sampling-noise (explains the n=9 split)",
    "abstention-training (rival refusal cause)",
    "capability->robustness (same axis, opposite = the retraction trigger)",
    "parametric-hallucination-scaling (= ev-loops-to-oops, a target)",
)

POOL = Pool(
    id="capability-failuremode",
    debate=DEBATE,
    correct_position=CORRECT_POSITION,
    target_ids=TARGET_EVIDENCE_IDS,
    distractors=DISTRACTORS,
)
