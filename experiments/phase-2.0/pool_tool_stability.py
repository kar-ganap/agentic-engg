"""§1.1 position-forming task pool (Thread B, debate #2) — content is yours to own.

Same on-axis-flawed principle as §1.8 (lessons §0.25): distractors ENGAGE the mutate-or-not
question and lean toward the WRONG answer (mutation is fine) but are NON-DECISIVE via an EXPLICIT
flaw (confound / underpower / mixed / metric-fragile). Silent/orthogonal tool-design concerns
(description, return-format, error-handling) would be triaged as off-topic -> no competition.

TRAP: do NOT invoke tool-COUNT reduction as a pro-mutation confound — swapping above the measured
tool-set break-even (#3) is genuinely decisive, not a flaw. The confounds here are all OTHER
entanglements (prompt length, difficulty, retry logic, model).
"""

from __future__ import annotations

from stance.reasoning.pool import Distractor, Pool

DEBATE = "Should tool definitions be stable across a run — i.e., never mutated mid-loop?"

CORRECT_POSITION = (
    "Yes — set tools once and don't mutate mid-loop; handle state-dependent availability via the "
    "latest user message / tool_choice. Two legs: cache-economics (~90: mutating the tool block "
    "busts the cached prefix, ~7x a stable one) + model-coherence (~65, literature-only) -> "
    "headline ~80. The pro-mutation findings in the set are confounded, underpowered, or "
    "metric-fragile — flawed evidence that neither overturns the cache case nor lowers the "
    "confidence (the one real exception is swapping above the measured tool-COUNT break-even, #3 — "
    "not mid-run mutation itself). A good answer states the stance + both legs, flags why "
    "the pro-mutation items are non-decisive, + a falsifiable retraction."
)

TARGET_EVIDENCE_IDS = ("ev-manus", "ev-exb")

DISTRACTORS: tuple[Distractor, ...] = (
    # A. confounded-pro-mutation: leans toward the WRONG answer (mutate); non-decisive via confound.
    Distractor(
        "d-conf", "confounded-pro-mutation", "high", "synthetic",
        "Agents that {mutation} mid-run completed {gain} more tasks, but {confound} — the gain "
        "isn't attributable to the mutation.",
        slots={
            "mutation": ("swapped their toolset", "pruned unused tools", "added tools on demand",
                         "reordered the tool list"),
            "gain": ("12%", "a handful of", "noticeably"),
            "confound": (
                "the run also used a shorter system prompt",
                "task difficulty wasn't matched across arms",
                "the baseline lacked retry logic",
                "a different model served the mutated runs",
            ),
        },  # 4x3x4 = 48
    ),
    # B. mixed-result: on-axis, non-decisive via inconsistency.
    Distractor(
        "d-mix", "mixed-result", "high", "synthetic",
        "Across {n}, mid-run tool {change} helped about as often as they hurt — {caveat}.",
        slots={
            "n": ("four agent frameworks", "six task suites", "five setups", "three families"),
            "change": ("swaps", "additions", "prunes"),
            "caveat": ("no consistent effect", "effect sizes overlapped zero"),
        },  # 4x3x2 = 24
    ),
    # C. underpowered: on-axis, non-decisive via noise.
    Distractor(
        "d-under", "underpowered", "high", "synthetic",
        "A {size} probe found mid-run tool swaps {dir} success, but the gap sat within noise.",
        slots={
            "size": ("2-agent", "single-task", "3-run", "small"),
            "dir": ("slightly improved", "marginally raised", "nudged up"),
        },  # 4x3 = 12
    ),
    # D. metric-fragile: stability's benefit looks illusory (leans pro-mutation); non-decisive.
    Distractor(
        "d-metr", "metric-fragile", "high", "synthetic",
        "Stable tools helped on {metricpair} on {scope}.",
        slots={
            "metricpair": (
                "latency but the effect vanished on task-success",
                "cost but vanished on accuracy",
                "first-call success but vanished end-to-end",
            ),
            "scope": ("one eval", "the reranked subset", "a single suite"),
        },  # 3x3 = 9
    ),
)  # ~93 HIGH variants across 4 flaw-types

# ---- TRAPS under the revised principle (§0.25) ----
# 1. Pro-mutation finding WITHOUT a flaw => decisive for mutation => breaks grading.
# 2. tool-COUNT reduction as the pro-mutation reason => that's #3's real break-even => decisive.
# 3. Silent/orthogonal tool-design concern (description/return-format/error-handling/parallelism)
#    => off-axis => triage-able => no competition (the §1.8 failure).
NEAR_MISSES_EXCLUDED = (
    "pro-mutation-without-a-flaw (decisive)",
    "tool-count break-even (#3, genuinely decisive)",
    "silent/off-axis tool-design concern (triage-able)",
)

POOL = Pool(
    id="tool-stability",
    debate=DEBATE,
    correct_position=CORRECT_POSITION,
    target_ids=TARGET_EVIDENCE_IDS,
    distractors=DISTRACTORS,
)
