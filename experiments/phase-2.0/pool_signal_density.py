"""§1.8 position-forming task pool (Thread B) — content is yours to own.

A position-forming task = DEBATE + an evidence set = TARGETS (the graph's real evidence, which fix
the correct position) + DISTRACTORS (non-decisive records that compete for attention).

Confusability principle (REVISED 2026-07-25, replacing the earlier "silent" criterion):
  A distractor must be ON-AXIS (engage competition-vs-length, even lean toward LENGTH) but
  NON-DECISIVE via an EXPLICIT FLAW (confound / underpower / mixed result / metric fragility).
  WHY: silent/off-axis distractors (the old rule) are trivially triaged as off-topic -> no
  competition -> the §1.8 rot can't fire. First sweep: plan_execute read exactly the 3 targets
  (96% target citations) and baseline held flat, because off-axis mechanisms are obvious filler.
  On-axis-flawed distractors can't be triaged by topic and can't be taken as decisive, so the
  model must actually reason about each flaw. See lessons §0.25.

RED LINE: every distractor carries an explicit decisiveness-defeating flaw. On-axis WITHOUT a flaw
= decisive (would really support length) => breaks grading. The flaw is mandatory, not optional.
"""

from __future__ import annotations

from stance.reasoning.pool import Distractor, Pool

DEBATE = (
    "Under long context, does signal-density / competition — not raw token length — drive the "
    "retrieval/reasoning collapse?"
)

# The correct position the rubric grades toward (fixed by the TARGETS). The clause about the
# length-leaning findings is what makes the grader reward FLAW-DETECTION (judge-only; see the
# retro on why the key must name the discount-the-flawed-evidence move).
CORRECT_POSITION = (
    "Competition / signal-density is the primary driver: at fixed length, adding similar "
    "competitors sharply degrades retrieval; at fixed density, length matters far less. "
    "Confidence ~80; cross-family generality still open (clause b). The length-leaning findings in "
    "the evidence set are confounded, underpowered, or mixed — flawed evidence that neither "
    "overturns the clean competition results nor lowers the confidence. A good answer states this "
    "stance + a calibrated confidence, explains why the length-leaning items are non-decisive, and "
    "gives a falsifiable retraction (e.g., demote if a neutral knee appears below a diffuse knee)."
)

# Targets = decisive real evidence already in data/graph (reused, not re-authored).
TARGET_EVIDENCE_IDS = ("ev-ruler", "ev-nolima", "ev-length-ext")

DISTRACTORS: tuple[Distractor, ...] = (
    # A. confounded-length: leans toward the WRONG answer (length); non-decisive via the confound.
    Distractor(
        "d-conf", "confounded-length", "high", "synthetic",
        "Recall fell {drop} from {span} tokens, but the eval {confound} — length and competition "
        "stay entangled.",
        slots={
            "drop": ("~37%", "by nearly half", "28 points", "to near-chance"),
            "span": ("32k to 128k", "16k to 200k", "50k to 512k"),
            "confound": (
                "did not hold the number of near-duplicate passages fixed",
                "added more distractor documents at the longer lengths",
                "let topic diversity grow with length",
                "did not control needle-question similarity",
            ),
        },  # 4x3x4 = 48
    ),
    # B. mixed-result: on-axis, non-decisive via inconsistency.
    Distractor(
        "d-mix", "mixed-result", "high", "synthetic",
        "Across {n}, denser contexts {verb} recall about as often as the reverse — {caveat}.",
        slots={
            "n": ("four benchmarks", "six evaluations", "five QA datasets", "three model families"),
            "verb": ("helped", "improved", "boosted"),
            "caveat": ("no consistent direction", "effect sizes overlapped zero"),
        },  # 4x3x2 = 24
    ),
    # C. underpowered: on-axis, non-decisive via noise.
    Distractor(
        "d-under", "underpowered", "high", "synthetic",
        "A {size} probe found {dir} recall in denser contexts, but the gap sat within noise.",
        slots={
            "size": ("3-model", "2-model", "small 4-model", "single-seed"),
            "dir": ("lower", "slightly lower", "marginally worse"),
        },  # 4x3 = 12
    ),
    # D. metric-fragile: on-axis, non-decisive via fragility (metricpair paired to avoid nonsense).
    Distractor(
        "d-metr", "metric-fragile", "high", "synthetic",
        "The competition effect was clear under {metricpair} on {scope}.",
        slots={
            "metricpair": (
                "exact-match but vanished under semantic scoring",
                "recall@1 but vanished under recall@5",
                "lexical scoring but vanished under embedding scoring",
            ),
            "scope": ("one dataset", "the reranked subset", "a single model family"),
        },  # 3x3 = 9
    ),
)  # ~93 HIGH variants across 4 flaw-types

# ---- TRAPS under the revised principle ----
# 1. On-axis length-leaning finding WITHOUT a flaw => DECISIVE for length => breaks grading. The
#    flaw is what keeps it non-decisive; never omit it.
# 2. Silent / off-axis mechanism (position, form, hop, attention-sink, RoPE, KV-eviction) =>
#    triage-able as off-topic => induces NO competition (the failure the first sweep exposed).
# 3. A flaw so glaring it's trivially dismissed => no temptation => no competition. The flaw must be
#    real but take a beat to catch (a subtle confound, not "n=1").
NEAR_MISSES_EXCLUDED = (
    "on-axis-without-a-flaw (decisive for length)",
    "silent/off-axis mechanism (triage-able -> no competition)",
    "glaring flaw (trivially dismissed -> no temptation)",
)

POOL = Pool(
    id="signal-density",
    debate=DEBATE,
    correct_position=CORRECT_POSITION,
    target_ids=TARGET_EVIDENCE_IDS,
    distractors=DISTRACTORS,
)
