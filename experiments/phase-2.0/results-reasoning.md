# Thread B — reasoning-pattern comparison (Module 3)

**Question (prereg `reasoning-pattern`, 2026-06-29):** which reasoning loop should form positions
over an evidence graph — a no-loop `baseline`, `react` (retrieve + adaptive), `plan_execute`
(retrieve + plan-first), or `reflection` (stuff + draft→critique→revise)? Plus the pre-registered
bonus: does a retrieval loop beat stuffing once the evidence is large + confusable enough to trigger
the §1.8 diffuse-competition rot?

**Substrate:** arms = DeepSeek-v4-flash; judge = Claude-Sonnet-5 (anchor — grading noise feeds the
DV); fuzzy 5-criterion rubric (0–20). Paired design (all arms on the same materialized task).
5 seeds/cell, N∈{4,12,24} distractors, HIGH confusability. Reproduce:
`uv run python experiments/phase-2.0/run_reasoning.py --pools <id> --sizes 4,12,24 --seeds 1,2,3,4,5 --go`.

## The design pivot that made it work (§0.25)

The first §1.8 sweep found **nothing** — because the original distractors (§0.22: same-topic but
*silent* on the axis) are trivially triaged as off-topic: `plan_execute` read exactly the 3 targets
(96% target citations) at every N; `baseline` held flat. **Silent = off-axis = triage-able = no
competition.** Fix (lessons §0.25): distractors must be **on-axis** (engage the debate, even lean to
the wrong answer) but **non-decisive via an explicit flaw** (confound / underpower / mixed /
metric-fragile), multiplied into distinct-*looking* studies. All three pools were rebuilt this way.

## Results (grade 0–20, mean; @N=24 unless noted)

| debate | epistemic structure | baseline | plan_execute | react | reflection |
|---|---|---|---|---|---|
| **§1.8** signal-density | confident, **dilutable** convergent | 16.6→16.8→**8.0** | 16.8→17.4→**16.4** | 16.8→18.0→14.6 | 11.4→10.8→10.8 |
| **§1.1** tool-stability | confident, **one robust fact** | 17.8→16.8→17.2 | 15.2→15.4→15.8 | 18.4→16.8→**17.8** | 16.2→16.8→16.0 |
| **§3.8** capability | **hedge** (~45) | 11.6→11.8→11.2 | 11.0→10.2→10.2 | 13.0→9.8→**6.6** | 14.4→15.4→**17.6** |

**Winner flips by debate.** §1.8 → plan_execute; §1.1 → react/baseline; §3.8 → reflection.

## Mechanisms (confirmed, not inferred)

**The "rot" is regime-specific.**
- **§1.8 — dilution.** `baseline` @N=24 is a *bimodal collapse*: `[1, 5, 5, 13, 16]` — 3/5 runs rot.
  Mechanism confirmed: the worst run (stance-correctness 0) was **pulled to length** ("raw token
  length is the primary driver"). Confidence erodes with N (81→74→68). `plan_execute` reads ~3 items
  → never drowns → holds (`[14,16,17,17,18]`). Retrieve **sidesteps by committing to few**.
- **§1.1 — none.** `baseline` stance-correctness is **4/4/4** across N: the cache-economics fact
  (measured ~7× cost) can't be diluted by confounded pro-mutation findings. All arms flat;
  `plan_execute` marginally *worst* (reading few risks missing the one decisive fact).
- **§3.8 — overclaiming.** Correct = hedge ~45; every arm **overclaims** (conf 66–73) *except*
  `reflection` (44). `react` amplifies it worst (`[0,8,8,8,9]` @N=24, declining with N as confounded
  findings pile up); `reflection` wins and *rises* with N (`[16,16,16,20,20]`).

**The unifying law — bias × structure.** Effectiveness = alignment between a pattern's inductive
bias and the debate's epistemic structure:
- `plan_execute` = **commit-to-few** → sidesteps dilution (§1.8); risks the lone fact (§1.1).
- `reflection` = **inject caution** (uniform confidence-lowering: underclaims §1.8 at 61 vs 80,
  correctly holds §3.8 at 44≈45) → wrong for confident answers, right for hedges.
- `react` = **read-everything adaptively** → fine when a fact dominates (§1.1); amplifies
  overclaiming (§3.8).

## Verdict on the prereg
- **Pragmatic "pick one loop": REFUTED** — no universal winner.
- **Primary interaction (retrieve sidesteps rot): SUPPORTED but regime-specific** (dilution/§1.8;
  on §3.8 it's reflection, not retrieve, that sidesteps the overclaiming rot).
- **Ranking (react ≥ plan): REFUTED** as universal (§1.8 plan>react; §1.1 react>plan; §3.8 both lose).
- **Reflection (< reputation): REFINED** — reflection = systematic caution: hurts confident tasks,
  **wins** hedge tasks.

## Caveats
- **n=1 debate per regime** → the 3-cell taxonomy is a well-mechanized *hypothesis*; the mechanisms
  are confirmed, the partition is not.
- DeepSeek arms + Sonnet judge only; cross-provider untested. Fuzzy grader is an unvalidated
  instrument (not checked against human grades). 5 seeds/cell; the rot is stochastic (bimodal).

## Data
Result JSONLs in `experiments/phase-2.0/results/reasoning-*.jsonl` (each row carries the position,
arm telemetry, judge tokens, the raw arm+judge outputs, and the 5 grade scores). §1.8 =
`reasoning-20260725T180547`; §1.1+§3.8 = `reasoning-20260725T190138`. Pools:
`pool_signal_density.py` / `pool_tool_stability.py` / `pool_capability_failuremode.py`.
