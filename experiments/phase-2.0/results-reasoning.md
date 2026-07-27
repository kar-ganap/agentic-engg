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

## Re-test — confound removal (2026-07-26)  {#retest}

The three-reviewer pass found the two *mechanism* legs were artifacts, so we re-ran with all three
confounds removed: **anonymized presentation** (uniform `item-NN` ids + a content-free label in both
`list_evidence` and the stuffed prompt — no id-prefix or teaser tell, so triage is *structurally*
impossible), a **neutral critique** prompt (no "overclaim" keyword), and **prose-scored
EVIDENCE_USE** (judged on the stance's reasoning, not citation-list purity). 180 runs; the re-test
**discriminated cleanly**:

- **plan-execute's "commit-to-few" §1.8 win — REFUTED (was teaser-triage).** With triage defeated,
  plan reads a wide blind range (mean ~7–10, not "exactly the targets"), and plan vs react on §1.8
  is **10.6 / 8.2 / 9.6 vs 15.8 / 6.2 / 9.8** — order flips by N, within noise. The commit-to-few
  edge does not survive.
- **reflection's §3.8 caution win — EARNED (survives the neutral critique).** Reflection still
  lowers confidence **uniformly** (Δ −9 / −9 / −18 vs baseline across the three debates), holds the
  §3.8 hedge (conf 40, wins 16.6), and mis-serves the confident debates. The mechanism was **not**
  the keyword.
- **retrieve > stuff under §1.8 dilution — survives, but GENERIC.** baseline collapses hardest of
  all (3.6 @N=24, pulled to length/skepticism); the retrieve arms (plan ≈ react ~9.7) beat it — but
  it's *retrieval*, not commit-to-few.
- **§1.1 null / no-universal-winner — confirmed.** Data note: 9/180 bad rows, all retrieve arms on
  the two hard debates (anonymized loops truncate more) — depresses react slightly, no direction
  change.

**Net:** one artifact killed, one mechanism earned → `reasoning-pattern` moves 50 → **58, candidate**
(trajectory 40 → 62 → 50 → 58). Earned: reflection=systematic-caution (60); retrieve>stuff-generic
(55); no-universal-winner (65). Dropped: plan commit-to-few.

## Cross-provider (Kimi K3 vs DeepSeek) — 2026-07-26  {#xprovider}

The position's #1 caveat was single-provider. Focused matched-config run (§1.8 + §3.8 only — §1.1
is a null, low value to replicate) with the **arms swapped to Kimi K3** (2.8T flagship — a very
different family) and the **judge held at Sonnet** (isolates the provider effect). Both earned
mechanisms **replicate directionally**:

- **reflection = systematic caution — CONFIRMED.** On clean data, K3 reflection holds the §3.8 hedge
  (conf **46** @N=4, 54 @N=24 ≈ correct ~45), wins §3.8 (grade 13–17), and lowers confidence
  uniformly (**Δ−10** vs baseline; DeepSeek Δ−15) — same mechanism, marginally weaker. *Caveat that
  became a finding:* K3's verbose **3-call reflection burned even 4096 tokens on reasoning with an
  empty visible answer** (7/20 parse-fails). Raising the cap to **8192** fixed it (2/19) — so the
  earlier "weaker/inconclusive" read was the *measurement*, not the mechanism. Very-verbose models
  need a larger answer cap → a precondition.
- **retrieve > stuff under §1.8 dilution — replicates** (retrieve arms > collapsed baseline on both;
  milder on K3 — baseline 8.6 vs DeepSeek 5.2).

**Net:** single-provider is discharged; `reasoning-pattern` firms **58 → 63** (candidate). Remaining
caps: unvalidated grader, 1–2 debates/regime. Path to *active*: a validated grader + a 2nd debate
per regime. Data: `reasoning-20260726T101930` (DeepSeek), `-110319` + `-153204` (Kimi K3, the latter
the clean reflection re-run @8192). *Billing note:* the K3 reflection re-run stopped at 19/20 on a
Moonshot balance suspension — enough data; no re-run needed.

## Data
Result JSONLs in `experiments/phase-2.0/results/reasoning-*.jsonl` (each row carries the position,
arm telemetry, judge tokens, the raw arm+judge outputs, plan trace, and the 5 grade scores). First
sweeps (confounded): §1.8 = `reasoning-20260725T180547`, §1.1+§3.8 = `reasoning-20260725T190138`.
**Confound-removed re-test: `reasoning-20260725T222940` (all three pools).** Pools:
`pool_signal_density.py` / `pool_tool_stability.py` / `pool_capability_failuremode.py`.
