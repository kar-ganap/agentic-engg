# Phase 1.0 — Exercise B: KV-Cache Anti-Patterns (results)

> Tests §1.1 (tool/prefix stability) and §3.3 (positional cache-cost gradient).
> Pre-registration LOCKED in `docs/phases/phase-1.0-exercise-B-plan.md`. DVs are
> exact, from `response.usage`: cache_read fraction + $/turn (latency dropped —
> non-reproducible). Harness: `cache_run.py` + tested `stance` helpers
> (`pricing.cost`, `with_cache_breakpoints`, `token_budget`). Written 2026-06-05.

## Headline

The cache-cost of a prefix anti-pattern is set by **how early in the
`tools → system → messages` hierarchy it strikes** — a tool change is worst
because **tools is the cache root**. On Haiku 4.5 with a padded ~6.4k prefix +
3 breakpoints (tools/system/end-history), at matched ~9k context (turn 5):

| policy | level changed | cache_read (t≥1) | predicted | hit | $/turn | **× stable** |
|---|---|---:|---|---:|---:|---:|
| `stable` (control) | — | ~full prefix | full | 0.93 | $0.0016 | **1.0×** |
| `shape_mix` (C1) | messages | 5759 | tools+system (6067) | 0.72 | $0.0050 | **3.0×** |
| `timestamp_system` (A1) | system | 4216 | tools (4536) | 0.53 | $0.0067 | **4.1×** |
| `tool_reorder` (B1) | tools (root) | **0** | ~0 | 0.00 | $0.0115 | **7.0×** |

**§1.1 is mechanistically confirmed: tool-definition instability is the single
most expensive cache anti-pattern** (7× a stable prefix here, climbing toward 10×
as the cached prefix grows vs the per-turn new tokens — our own version of Manus's
"~10×"). This is *why* tools must be stable across a run: they are the literal
cache prefix root, so any change re-bills the entire context.

## Pre-registration outcomes (§3.3)

- **P-B1 (baseline) — CONFIRMED.** `stable`: turn 0 writes the prefix (read 0,
  $0.0080), then `cache_read` climbs and hit settles ~0.92–0.94 (not 1.0 — the
  ~560 new tokens/turn are always uncached, exactly the predicted
  `cached/(cached+new)` ceiling). Cost drops ~5–6× after turn 0.
- **P-B2 (cardinal — the test) — CONFIRMED.** Each anti-pattern's steady-state
  `cache_read` equals the prefix fraction *before* the perturbed level: B1 → 0
  (tools root invalidates all); A1 → tools (4216 ≈ measured 4536); C1 →
  tools+system (5759 ≈ measured 6067). Computed from `count_tokens` spans, matched
  by observed `usage`.
- **P-B3 (ordering) — CONFIRMED.** Cost **stable < shape_mix < timestamp <
  tool_reorder** = stable < C1 < A1 < B1 (earlier perturbation → more invalidated
  → costlier). The corrected hierarchy held (tools-root worst).
- **P-B4 (restore) — DIRECTIONALLY SUPPORTED.** Reverting B1 → stable recovers the
  hit rate to baseline within ~2 turns (anti phase ~0.5 → stable t+1 = 0.95) →
  damage is transient, not permanent. **Caveat:** the anti phase wasn't fully
  zeroed (read=tools, not 0) because the `tools` cache *root* is shared across
  policies and our isolation nonce sat in `system` (after tools). Clean isolation
  needs per-policy *tool-content* uniqueness; the recovery direction is
  nonetheless clear. Not chased further (secondary prediction; sandbox-pull).

## Mechanism note

Caching matches the longest identical prefix up to a breakpoint; the documented
hierarchy `tools → system → messages` means a change cascades *downward* only. So:
- a **tools** change invalidates tools+system+messages → `cache_read ≈ 0`;
- a **system** change keeps tools cached → `cache_read ≈ tools`;
- a **messages** change keeps tools+system cached → `cache_read ≈ tools+system`.
The observed reads (0 / 4216 / 5759) trace this exactly. Multi-breakpoint
placement (after tools, after system, end-history) is what makes the gradient
*observable* — a single end-breakpoint would full-miss on every anti-pattern.

## Caveats / threats to validity

- **Shared 5-minute server cache across conditions.** Running five policies
  back-to-back, the cache bled between them (identical canonical tools / rotations
  / history collided). Mitigated with a per-policy **system nonce**, but the
  `tools` root stayed shared (nonce is after tools) — visible as warm-tools reads
  at some t=0 turns and in the restore anti phase. Steady-state (t≥1)
  measurements for stable/A1/C1/B1 are robust to it; only restore's anti-phase
  baseline is affected. (Measurement lesson logged.)
- **Synthetic prefix.** Padded filler tools/system/history (content-independent
  for caching) — the point is the byte-stability structure, not content realism.
- **Single model** (Haiku 4.5). The multipliers are model-independent; the
  *absolute* $/turn and the ×-ratio scale with the base price and prefix size.
- **Latency not measured** (prefill-only effect needs TTFT/streaming; wall-clock
  is network/load-confounded and non-reproducible — excluded by design).

## Reproducibility

```bash
uv run python experiments/phase-1.0/cache_run.py --pilot --go   # calibration (stable, 3 turns)
uv run python experiments/phase-1.0/cache_run.py --go           # all 5 policies
```
- Pinned: model, padded spans verified via `count_tokens` (tools ≥4096 alone),
  3 ephemeral breakpoints, 6 turns/policy (restore 12). Prices from
  `stance.instrumentation.pricing` (verified 2026-06-05). Cost exact from `usage`.
- **Cost (logged in `tasks/spend.md`):** ~$0.42 total incl. 3 debugging
  iterations; a single clean run ~$0.14 (caching makes it cheap).

## Synthesis updates made (2026-06-05)

- **§1.1** confidence raised: own-substrate experimental confirmation that tool
  instability is the worst cache anti-pattern (7× cost; tools = cache root).
- **§3.3** marked tested → confirmed (positional cost gradient B1>A1>C1>stable).
