"""§3.8 position-forming task pool (Thread B, debate #3) — content is yours to own.

On-axis-flawed principle (lessons §0.25) with a §3.8 TWIST: the correct answer is a calibrated
HEDGE (~45), so the failure mode isn't "pulled to a wrong stance" — it's DROPPING THE HEDGE for
false confidence (either direction). Distractors are confounded findings that *seem to resolve* the
capability->failure-mode question (pro-shift / anti-shift / knee); they pull both ways, so the
correct move is to RESIST and hold the hedge. Each carries an explicit flaw (a clean finding would
legitimately update the hedge -> decisive); the flaw is a skimmable clause, so the distractor tests
whether the model ATTENDS to the confound (the epistemic_humility + calibration criteria carry it).
"""

from __future__ import annotations

from stance.reasoning.pool import Distractor, Pool

DEBATE = (
    "Under diffuse competition, does higher model capability shift the failure mode "
    "(confabulate -> refuse) and pull the collapse knee earlier?"
)

# Correct = a HEDGE. The contradicting evidence (ev-loops-to-oops) is a TARGET — it's WHY we hedge.
CORRECT_POSITION = (
    "PLAUSIBLE but UNCONFIRMED: one n=9 comparison shows the direction (stronger model refuses, "
    "weaker confabulates, earlier knee), BUT the explicit UNKNOWN affordance is an equally-live "
    "cause (not capability), and the parametric-regime literature scales the OPPOSITE way — a "
    "candidate regime-dependent reversal, undecided pending the affordance-controlled ladder. "
    "Confidence ~45. The confident-looking findings in the set (pointing both ways) are confounded "
    "— they don't resolve the question, so the ~45 hedge stands. A good answer hedges, names the "
    "confounds + the contradicting literature, and refuses to be pushed to a confident stance."
)

# Targets: support + inconclusive + CONTRADICTING (the last is load-bearing for the hedge).
TARGET_EVIDENCE_IDS = ("ev-exA-capability", "ev-deepseek-abstain", "ev-loops-to-oops")

DISTRACTORS: tuple[Distractor, ...] = (
    # A. confounded pro-shift: tempts a confident YES; the flaw IS §3.8's own live confound.
    Distractor(
        "d-shift", "confounded-pro-shift", "high", "synthetic",
        "Larger models refused ambiguous lookups {factor} more than small ones, {confound}.",
        slots={
            "factor": ("3x", "far", "consistently", "markedly"),
            "confound": (
                "but they were also tuned to abstain, entangling capability with abstention",
                "but only on items with no correct answer, where refusal was appropriate",
                "but the small models weren't offered the same refusal option",
                "but ambiguity wasn't verified independently",
            ),
        },  # 4x4 = 16
    ),
    # B. confounded anti-shift: tempts a confident NO (capability just helps, no mode shift).
    Distractor(
        "d-noshift", "confounded-anti-shift", "high", "synthetic",
        "Scaling {verb} accuracy on ambiguous items without extra refusals, {confound}.",
        slots={
            "verb": ("raised", "improved", "lifted"),
            "confound": (
                "but the suite lacked an explicit 'unknown' option, so refusal couldn't surface",
                "but only two model sizes were compared",
                "but ambiguity wasn't annotator-verified",
                "but correct abstentions were scored as errors",
            ),
        },  # 3x4 = 12
    ),
    # C. confounded knee-shift: tempts a confident YES on the earlier knee.
    Distractor(
        "d-knee", "confounded-knee", "high", "synthetic",
        "Stronger models degraded at {lower} competition thresholds, {confound}.",
        slots={
            "lower": ("lower", "earlier", "smaller"),
            "confound": (
                "but weren't difficulty-matched to the weaker models",
                "but the threshold metric differed across models",
                "but n=2 per size",
                "but the stronger models saw harder items",
            ),
        },  # 3x4 = 12
    ),
)  # ~40 HIGH variants across 3 flaw-types (pull both ways -> hold the hedge)

# ---- TRAPS ----
# 1. A clean (unflawed) pro/anti-shift finding => legitimately updates the hedge => decisive.
# 2. Orthogonal rival failure modes (safety-refusal, sycophancy, prompt-injection) => off-axis =>
#    triage-able => no competition (the old §3.8 design; replaced under §0.25).
# 3. A mixed/underpowered finding => that SUPPORTS the hedge (consistent with uncertainty), so it's
#    not a temptation here — §3.8's distractors must seem to RESOLVE, not to muddy.
NEAR_MISSES_EXCLUDED = (
    "clean pro/anti-shift finding (decisive — updates the hedge)",
    "orthogonal failure mode (off-axis, triage-able)",
    "mixed/underpowered finding (supports the hedge, not a temptation)",
)

POOL = Pool(
    id="capability-failuremode",
    debate=DEBATE,
    correct_position=CORRECT_POSITION,
    target_ids=TARGET_EVIDENCE_IDS,
    distractors=DISTRACTORS,
)
