# Phase 1.1 #3 — carry-vs-swap tool-set break-even (KV-cache economics)

> **Outcome: a carry-vs-swap break-even EXISTS and is governed by KV-cache economics.** Given a
> large tool universe, do you load a fixed **superset** once and keep it cache-stable (**carry**,
> §1.1-compliant), or load only the small per-task **subset** and eat a cache-bust each time the
> task changes (**swap**)? There is a break-even in superset size: **carry below it, swap above it.**
> We **predicted** the crossover analytically (pre-registered N\* ≈ 5,111 tool-tokens) and
> **verified** it empirically on DeepSeek v4-flash (N\* ≈ 6,461 actual tool-tokens) — same direction,
> same curve shape (carry linear in tool-size, swap flat), location matched to **~26%**, with the
> residual fully attributable to the measured swap floor overshooting the nominal target (+22%).
> **#3 prior 70 → 78** (qualifies §1.1 cache leg). Single-provider (DeepSeek); the break-even *location* is
> provider- and session-shape-dependent (TTL, hit/miss ratio) — the **existence + the cost model**
> is the cross-provider claim, not the number. Written 2026-06-14. Regenerates from
> `experiments/phase-1.1/{smoke_cache,predict_cache_breakeven,cache_breakeven}.py`.

## The question

§1.1 says *don't mutate the tool block mid-loop* (cache root + model coherence). But that advice
collides with "carry a minimal viable tool set" (Anthropic tool-design) the moment the tool
**universe** is large: keeping all of it stable means every cached turn still re-reads a huge tool
block (at the hit rate), while swapping to the few tools a task needs keeps each request small but
**busts the cache** on every task boundary. Which wins is an economics question with a crossover.

- **CARRY** — fixed superset of N tool-tokens, never mutated → cache-stable (turn 1 misses; turns
  2…T hit the whole prefix). Cost rises with **N**.
- **SWAP** — subset of k tool-tokens, mutated at each task boundary → each bust re-misses the full
  request. Cost is ~independent of the superset size; set by **#busts**.

## Method — predict (B) then verify (A)

**Step 1 — mechanism gate** (`smoke_cache.py`, $0.01). Does DeepSeek prefix-cache *tool defs* (the
doc leaves this undocumented), and does mutating the tool block bust the suffix? Sequence warm→
repeat→mutate→repeat: `cache_read` **15,488 → 15,488 → 0 → 15,488**. Confirmed: tools are in the
cached prefix; mutating them invalidates the whole suffix, reported as Anthropic-style
`cache_read_input_tokens`. (This is the cost model #3 stands on.)

**Step 2 — analytic PREDICTION** (`predict_cache_breakeven.py`, pure arithmetic, pre-registered).
Cost model from the smoke + v4-flash rates (hit $0.0028, miss $0.14/MTok). Scripted T=8 session,
history +C tokens/turn, system S, subset k=1500, one swap at turn 4:

```
per turn t (request = S + tools + t·C):
  cold (t=1) or swap-turn → full MISS: S + tools + t·C
  stable turn (t≥2)       → HIT prefix S+tools+(t-1)C, MISS only the new C
```

Carry cost is **linear in N** (N paid once at miss + 7× at hit ⇒ slope = MISS + 7·HIT = 0.1596/MTok);
swap cost is **flat** in N. Sweep → **pre-registered N\* ≈ 5,111 tool-tokens.**

**Step 3 — empirical VERIFICATION** (`cache_breakeven.py`, DeepSeek v4-flash, ~$0.15 over iters).
A **scripted** (no-agent) T=8 session — fixed turns, so no agent call-count variance (the confound
that muddied #6). Real `cache_read_input_tokens`/`input_tokens` costed at the same rates. Two
measurement-discipline fixes were needed and both materially moved the result:
- **cross-N cache contamination** — all carry sessions first shared one filler prefix, so larger-N
  sessions got cache hits on the slice they shared with a prior smaller-N session, flattening the
  curve and inflating the apparent N\*. Fix: a per-run nonce + per-N salt so every session is
  genuinely cold. (DeepSeek's hours-days TTL makes this bite across re-runs too.)
- **nominal vs actual tokens** — the filler param wasn't token-calibrated (~2× actual). Recover
  actual tool-tokens from the linear turn-1 input (slope = tokens/nominal-N; intercept = S+C
  overhead) so the empirical N\* is in the same currency as the prediction.

## Result (final clean run)

```
 tool tok   CARRY $e-3   SWAP $e-3   cheaper
     3250      1.7171      2.2249     carry
     6500      2.2312      2.2249     swap
     8125      2.4882      2.2249     swap
     9750      2.7628      2.2249     swap
    11375      3.0022      2.2249     swap
    13000      3.2768      2.2249     swap
```

| | predicted (B) | empirical (A) |
|---|---|---|
| crossover N\* | **5,111** tool-tokens | **6,461** actual tool-tokens |
| carry shape | linear in tool-size | linear ✓ |
| swap shape | flat | flat ✓ |
| direction | carry below, swap above | confirmed ✓ |
| swap floor | $1.82e-3 | $2.22e-3 (+22%) |

**The crossover exists, the curve shapes match the cost model exactly, and the location matched the
pre-registered prediction to ~26%.** The residual is calibration, not mechanism: the measured swap
floor came in 22% above the nominal target (actual S/C/k overshoot the predictor's targets), and a
higher swap floor lets carry stay competitive to a larger superset — pushing N\* up, in the observed
direction and rough magnitude.

## What this is, and isn't

- **Cross-provider claim:** the **existence** of a carry-vs-swap break-even and its **cost model**
  (carry linear in superset size; swap flat in #busts; crossover where they meet) — both follow from
  any prefix-cache with hit < miss, which is provider-general.
- **NOT cross-provider:** the **number** (6,461). It scales with the hit/miss ratio (DeepSeek ~50×;
  Anthropic ~10× → crossover moves), the **cache TTL** (DeepSeek hours-days vs Anthropic 5-min — a
  session whose turns are spaced beyond TTL loses carry's cached-prefix advantage entirely, shoving
  the crossover hard toward swap), #busts, T, and content growth. The break-even is **computable per
  deployment** from these, not a universal constant.
- **Relation to §1.1:** this **qualifies** §1.1's cache-economics leg rather than refuting it.
  "Don't mutate tools mid-loop" is the cheaper strategy *while the tool universe is small* (below
  the break-even). Once the universe is large, **swapping a minimal per-task set is the cheaper
  strategy despite busting the cache** — the §1.1 stable-prefix advice and the "minimal viable tool
  set" advice trade off at exactly N\*. (The §1.1 model-**coherence** leg is untouched by this — a
  separate, still-untested concern.)

## Caveats / open

- **Single-provider, single session-shape.** Anthropic (Claude) anchor deferred — would test whether
  the 10× discount + 5-min TTL move the crossover as the cost model predicts. This is the natural
  §0.8 cross-provider follow-on.
- **Scripted, not agentic.** Deliberate (kills the call-count confound), but a real agent's
  #busts/turn count is endogenous; the break-even shifts with how often the live task actually
  changes the needed tool set.
- The model-coherence question (does a swapping agent hallucinate stale tool names?) is the §1.1
  follow-on and is **not** addressed here — swap's *correctness* cost, separate from its dollar cost.
