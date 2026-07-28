# Phase 1.2 Thread C — §1.2 behavioral-supervision test (the reviewers' path-to-active)

> Thread B tested §1.2 via **ref-recall** (payload survival). The three-reviewer pass flagged that
> §1.2's *stance* claims failures are **behavioral supervision** (the agent *adapts its actions* from
> the failure — Reflexion) — a stronger claim the payload DV never tested. This thread tests it, with
> a **task-success** DV, and was the reviewers' pre-registered path-to-active.

## Pre-registration (before the powered run)

**Claim:** preserving a failure that carries a **corrective the agent must APPLY** (a format rule)
enables behavioral correction — a late submit succeeds — while summarizing it away breaks it, under
**ephemeral reasoning** (Haiku `strip`) or a **non-reasoning** model (`deepseek-chat`); with persisted
reasoning the model self-rescues (null). **Prior 62** (user-set). **Falsifier:** (a) `strip`+preserve
doesn't beat `strip`+summarize on behavioral success at 5 seeds → the claim fails; (b) `persist` also
shows a gap → the self-rescue story breaks. `prereg_correction.py`.

## Design — fail-early / distract / apply-late (defeats every self-rescue channel)

`submit_record(record_id, code)` enforces a **format** (`correct_code`: a dash after the first 3
chars). The task (`build_correction_task`) has three steps: (1) **FORMAT CHECK** — submit `R1-TEST`
with a raw code → `INVALID` teaches the *rule* (generic example, not the answer); R1-TEST is **not
resubmitted** (no success to re-teach it). (2) **AUDIT** — a 7-order `check_shipment` chain fills
context past the budget → compaction drops the early failure. (3) **SUBMIT** the real records R2/R3.

**Why this isolates behavioral supervision:** the rule lives ONLY in the failure content (the agent's
own submit shows the *wrong* code; the correction is in the result); there is **no intervening
successful submit** to re-derive it; and under `strip` the reasoning can't carry it. So a late submit
is format-correct on first attempt **iff the failure was preserved** — the agent *adapting its action*
from the failure. **DV = fraction of {R2, R3} whose FIRST submit applies the rule** (task success).

## Result

| provider | reasoning | preserve | summarize |
|---|---|---|---|
| **Haiku** (5 seeds) | strip | **1.00** (all 5) | **0.00** (all 5) |
| **Haiku** | persist | 1.00 | 1.00 |
| **deepseek-chat** (3 seeds, non-reasoning) | strip | **1.00** (all 3) | **0.00** (all 3) |

Per-seed perfect (no variance). `probe-fail = 1.00` everywhere — the R1-TEST teaching failure fired
(sanity). `persist` = flat null (self-rescue via the model's own reasoning, which compaction doesn't
touch).

## Disposition

Both falsifier clauses fail → **§1.2's behavioral claim confirmed.** This discharges the two biggest
caps from the three-reviewer pass:
- **The DV now measures behavioral adaptation** (the agent fixes its *action* from the failure → task
  success), not a surviving datum — the reviewers' #1 method-rigor issue.
- **The bite replicates on a non-reasoning 2nd provider** (`deepseek-chat`, validated to emit no
  `reasoning_content`) → **cross-provider**, not Haiku-strip-only.

Both were the pre-registered up-clause → **§1.2 68 → 78, candidate → active** (user-confirmed).
Trajectory **65 (literature) → 68 (prereg) → 74 (over-claim) → 68 (reviewer correction) → 78
(behavioral confirm, cross-provider)**. Remaining cap (`regime-generality` 58): the fail-early /
apply-late + format-rule structure is a specific operationalization; a natural-failure / downstream
multi-step-goal DV is the next step.

**The boundary still leads with the null:** with persisted reasoning (the common case) preservation is
redundant; the behavioral bite is the *ephemeral-reasoning* corner — now confirmed for the actual
claim, cross-provider.

## Reproducibility

| script | produces |
|---|---|
| `prereg_correction.py` | the pre-registered claim/falsifier/prior 62 (committed before the run) |
| `run_correction.py --go [--reasoning …] [--arm-provider …] [--bust-cache]` | the 2×2 sweep; DV = behavioral success |
| `record_correction_result.py` | graph: `ev-correction-behavioral` + §1.2 → active 78 |

Mechanism: `make_correction_tools` / `build_correction_task` (TDD). Raw rows:
`experiments/phase-1.2/results/correction-*.jsonl` (Haiku 2×2×5 = `…173111`; deepseek-chat strip×3 =
`…173618`); events in `runs/phase-1.2/`. ~$0.47 (Haiku; deepseek-chat tokens uncosted — not in the
pricing table).
