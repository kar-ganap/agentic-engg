"""Pre-registration of the §1.2 BEHAVIORAL-supervision test (Phase 1.2 Thread C), BEFORE the powered
run (Substrate Discipline #1). §1.2 is already candidate 68; this test targets its ACTUAL stated
claim — failures as *behavioral supervision* (the agent adapts its ACTIONS) — which the three-reviewer
pass flagged as untested (the ref-recall DV measured payload survival). Committing this script before
the sweep IS the pre-registration; the graph moves at `record_correction.py`. Run to print it.

CLAIM: preserving a failure that carries a CORRECTIVE (a format RULE the agent must APPLY) enables
behavioral correction — a LATE submit succeeds — while summarizing it away breaks it, UNDER ephemeral
reasoning (Haiku `strip`) or a NON-reasoning model (`deepseek-chat`). With persisted reasoning the
model self-rescues the rule (null). This is a task-success DV, not payload survival.

FALSIFIER (user-confirmed): (a) `strip`+preserve does NOT beat `strip`+summarize on behavioral success
at 5 seeds → the behavioral claim fails on own-substrate (down §1.2); (b) `persist` ALSO shows a
preserve>summarize gap → the self-rescue story breaks.

PRIOR (user-set): 62 — the mechanism is plausible (and the smoke bit: strip preserve 1.00 vs
summarize 0.00) but the no-intervening-success structure is delicate and the design is fresh. A clean
confirm on Haiku + the non-reasoning 2nd provider would move §1.2 toward active (the reviewers' +12).

DESIGN: reasoning{persist,strip} × policy{preserve_failures,summarize_uniform} × 5 seeds on Haiku; +
deepseek-chat (non-reasoning, validated) for the cross-provider bite. keep_last=2, budget 700,
loop_guard OFF. DV = behavioral success = fraction of late records whose FIRST submit applies the rule.
"""

from __future__ import annotations

PRIOR = 62
FALSIFIER = (
    "(a) strip+preserve does not beat strip+summarize on behavioral success (5 seeds) -> claim fails; "
    "(b) persist also shows preserve>summarize -> self-rescue story breaks"
)


def main() -> None:
    print(f"pre-registered: §1.2 behavioral-supervision test — prior {PRIOR}")
    print(f"falsifier: {FALSIFIER}")


if __name__ == "__main__":
    main()
