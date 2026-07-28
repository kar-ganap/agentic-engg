# Pre-registration — Eval-driven tool-development (Phase 2.1, B5)

**Registered:** 2026-07-28, before any B5 run. Module 6 L88 (eval-driven tool-dev) × §1.10 follow-up.

## Question
§1.10 (`tool-selection`, candidate 74): for *"Look up the customer NAME"* requests, the agent picks
`lookup_user` (whose **name** matches the verb "look up") over the correct `search_users` (whose
**description** — "Find a customer by name" — is the best semantic match). The verb-swap control
recovered accuracy to 1.00 by moving "lookup" onto the correct tool's **name**. B5 asks the
complementary question:

> Can an agent, driven by eval feedback, recover selection accuracy by improving the correct tool's
> **description** (keeping its name `search_users`) — i.e., is the §1.10 name-bias surmountable by
> *re-describing* rather than *renaming*?

## Prediction (user-registered: **substantial**)
Both refinement arms — **free-rewrite** (rewrite descriptions freely) and **controlled** (append one
disambiguating clause) — **substantially recover** pre-namespace held-out selection accuracy on the
§1.10 clash cells, without breaking the no-clash control.

- **Operationalized "substantial":** held-out accuracy recovers to **≥ 0.80 at density 3 AND
  density 5** for **at least one** refinement arm (mirrors the verb-swap control's pre-registered
  ≥ 0.80 recovery bar — a pre-existing threshold, not a new one).
- **Interpretation if confirmed:** the name-bias is **defeasible by a sharp description** (the
  verb-token can live in the DESCRIPTION, not only the NAME) → **qualifies §1.10** (name-dominance
  is not absolute).

## Falsifier / retraction
- **If NEITHER refinement arm reaches ≥ 0.80 at density 3 and 5** (names still win despite the
  improved description) → prediction **wrong**; §1.10's name-dominance is **robust to re-describing**,
  and the fix is *renaming* (as the verb-swap showed). This would **strengthen §1.10**.
- **Control guard:** if refinement drops the no-clash control (density 1) below 0.80, the
  improvement is not clean (description damage / over-fit) — report it, don't count the recovery.

## Design (held-out discipline)
1. **Training baseline** (seeds 1–5, pre-namespace, densities {3,5}) — confirm the collapse and
   observe the failures (agent → `lookup_user`). Supplies the failure count the improver sees.
2. **Improver** (DeepSeek): sees the *training* toolset + failures → rewrites descriptions (free) /
   appends a clause (controlled). **Never sees held-out entities** → any gain is generalization.
3. **Measure on the HELD-OUT set** (seeds 101–110, pre-namespace, densities {1,3,5}): baseline
   (original descriptions) vs free vs controlled. **DV = deterministic first-tool selection**
   (`selection_hit`), no judge.

**Substrate:** DeepSeek-primary (v4-flash) for both arm calls and the improver. Claude-Haiku anchor
deferred. Single improvement round (no iterate-to-convergence).
