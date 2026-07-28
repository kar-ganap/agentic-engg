# Phase 2.1 B5 — Eval-driven tool-development (Module 6 L88 × §1.10 follow-up)

> Can DESCRIPTION-refinement overcome the §1.10 name-bias? Pre-reg: `prereg-eval-driven-dev.md`
> (user-registered prediction: **substantial** recovery → *qualifies* §1.10). Substrate:
> DeepSeek v4-flash, held-out seeds 101–110, deterministic first-tool DV. 2026-07-28.

## Setup
Eval-driven loop: training baseline (seeds 1–5) confirms the collapse + drives an improver LLM →
measure the improved descriptions on the **held-out** set (seeds 101–110, never seen by the
improver). Pre-namespace only (where §1.10 bites). DV = first tool == `search_users` (`selection_hit`).

## Result 1 — the collapse reproduces on held-out
Training: the attractor `lookup_user` captured **7–10 / 10** across runs. Held-out **baseline**
selection accuracy collapses at the clash cells (N=3: 0.20–0.60; N=5: 0.00–0.20) and is clean at the
no-clash control (N=1: 0.90–1.00). §1.10 reproduces on fresh entities.

## Result 2 — free-rewrite recovers … (surface prediction met)
The free-rewrite improver (rewrite all descriptions from the failures) recovered held-out accuracy to
**1.00 at N=3 and N=5** across two independent runs, control intact. On its face this meets the
pre-registered ≥0.80 bar. **But** the improver edited *both* the correct tool (added the verb "look
up" to `search_users`) **and** the attractor (`lookup_user` → "internal system user records… audit").
Confounded — which lever did the work?

## Result 3 — isolation (deterministic, decisive): it was the ATTRACTOR, not the correct tool
Single-clause deterministic edits, appended to the original description (no LLM improver → reproducible):

| held-out N | baseline | correct_only | attractor_only | both |
|-----------:|---------:|-------------:|---------------:|-----:|
| 1 (control)|     1.00 |         1.00 |           1.00 | 1.00 |
| 3 (clash)  |     0.60 |     **0.30** |       **1.00** | 0.90 |
| 5 (clash)  |     0.20 |     **0.30** |       **1.00** | 1.00 |

- **`correct_only` does NOT recover** — appending *"Use this to LOOK UP a customer by name."* to
  `search_users` (the verb now explicitly in its DESCRIPTION, name unchanged) leaves it losing to
  `lookup_user` (0.30, no better than baseline). **A name-matched sibling beats the correct tool even
  when the correct tool's description carries the request verb.**
- **`attractor_only` fully recovers** — appending *"For internal user records only — NOT customer
  lookup."* to `lookup_user` demotes it → 1.00 at N=3 and N=5.

## Interpretation — this STRENGTHENS §1.10 (opposite the pre-registered direction)
The pre-registration predicted description-refinement would *qualify* §1.10 (name-bias defeasible by a
sharp description). The mechanism-level result points the **other way**:

1. **§1.10's core is strengthened.** `correct_only` is a new, direct test — the correct tool's
   DESCRIPTION carrying the verb still loses to the sibling whose NAME carries it. Name > description
   for *which tool wins*, confirmed on a fresh lever.
2. **New adjacent lever (a genuine qualification, but not the predicted one):** descriptions are not
   *ignored* — an **exclusionary** clause on the ATTRACTOR ("NOT for X") demotes it. So the fix for a
   name-capture is either **renaming** the correct tool (the verb-swap control, §1.10) or
   **dis-endorsing the competitor** in *its* description — not improving the correct tool's prose.

**Net for §1.10 (`tool-selection`, candidate 74):** confirming direction. The name-over-description
weighting holds under a new test; add the nuance that exclusionary attractor-descriptions are the
description-side lever that works. (Position update is the author's call.)

## Caveats
- **Clause strength:** `correct_only` used a natural verb-adding clause; a maximally aggressive
  clause (explicitly naming the competitor: "do NOT use lookup_user") was not tested — so the claim
  is "a natural description improvement on the correct tool doesn't recover," not "none ever could."
- **Controlled-LLM arm failed on-substrate:** the constrained "append a clause" improver returned
  **empty visible content** on v4-flash (both runs; raw text ''), likely the §0.27 reasoning-content
  behavior. Superseded here by the deterministic isolation, which is cleaner and reproducible anyway.
- **Baseline noise:** held-out baseline varies run-to-run (model stochasticity); the decisive
  contrasts (`correct_only` vs `attractor_only`) are *within-run*, so they are not confounded by it.

## Reproduce
```
uv run python experiments/phase-2.1/eval_driven_dev.py --go        # loop: baseline → improve → held-out
uv run python experiments/phase-2.1/eval_driven_isolate.py --go    # deterministic lever isolation
```
Raw: `results/eval-driven-dev-*.jsonl` (first line = the exact improver overrides), `results/
eval-driven-isolate-*.jsonl`.
