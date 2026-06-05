# Phase 1.0 — Exercise B: KV-Cache Instrumentation (sub-plan)

> Sub-plan of `phase-1.0-plan.md` (Exercise B, "DEEP"). Tests **§1.1**
> (tool/prefix stability) and **§3.3** (anti-pattern break/restore). Written
> 2026-06-04.

## Goals

1. **Validate §1.1 empirically** — mutating the stable prefix (tools/system)
   mid-run is a real, measurable cost lever: it destroys the KV-cache and spikes
   cost. Not folklore — a number.
2. **Test §3.3** — quantify the hit-rate / $-per-turn delta for each anti-pattern
   {timestamp-in-system, tool-reorder, content-shape-mix}, and confirm reverting
   to the stable prefix **restores** the hit rate (damage is transient).
3. **Turn Manus's claim into our own number (§0.8)** — Manus: "KV-cache hit rate
   is *the* metric; cached vs uncached differ ~10×." We measure the penalty *in
   our harness*.
4. **Build reusable, exact cost instrumentation (throughline)** — `cache`-aware
   usage capture + a pinned price table → permanent, accurate cost observability
   for Stance's own loop (also makes `spend.md` exact, incl. cache savings).

## Mechanism (the finding, not just "caching works")

Anthropic caches the **longest identical prefix** up to a `cache_control`
breakpoint; `usage` reports `cache_read_input_tokens` (~0.1× price),
`cache_creation_input_tokens` (~1.25×), uncached `input_tokens`, `output_tokens`.
A perturbation invalidates **everything after its position**. Hence the
pre-registered claim:

> **Anti-pattern cost ∝ how *early* in the prefix it perturbs.** Timestamp-in-
> **system** (earliest) invalidates the whole prefix → worst; tool-**reorder**
> (after system) invalidates from tools on; content-**shape-mix** in history
> (latest) invalidates least.

The **positional cost gradient** is the result — it upgrades §3.3 from
"anti-patterns are bad" to "here is the cost gradient, and it's positional."

## Instrumentation — exact + reproducible only (course-correction)

**Audited 2026-06-04: we currently have NEITHER $/turn nor latency.** Nothing reads
`response.usage` (the rot runner records a `count_tokens` *estimate*, which is
*blind to caching*); there is no price table and no call timing. The two candidate
DVs are **not** equally salvageable:

- **Cache hit rate + $/turn — PRIMARY (gated).** Source = `response.usage` (the
  API's own exact counts), deterministic, environment-independent, regenerates from
  committed code → passes the "numbers regenerate" gate. `count_tokens` **cannot**
  see caching, so these MUST come from the real call response.
- **Latency ms/turn — DEMOTED, NOT gated.** Wall-clock is confounded by network RTT
  + server load; total latency = prefill + decode but the cache effect is *prefill
  only* (correct metric is TTFT, needs streaming); latency ∝ output tokens; and it's
  single-machine/single-region → **not reproducible** (fails our gate as a committed
  number). Optional **TTFT sidebar** only, explicitly labelled "our-setup-only, not
  reproducible." Default: **omit.** ($/turn already captures the actionable penalty.)

### Price table (pin; verify at run time)

`src/stance/instrumentation/pricing.py` — pure, fully unit-tested. Per-model
$/MTok, as of 2026-06 (**verify against current pricing before each run; pinned for
reproducibility**):

| model | input | output | cache write (5m, 1.25×) | cache read (0.1×) |
|---|---:|---:|---:|---:|
| claude-haiku-4-5 | 1.00 | 5.00 | 1.25 | 0.10 |
| claude-sonnet-4-6 | 3.00 | 15.00 | 3.75 | 0.30 |

`cost = input·p_in + output·p_out + cache_creation·p_write + cache_read·p_read`
(all per token). Cache-hit rate = `cache_read / (cache_read + cache_creation + input)`.

## Build (plumbing — Claude scaffolds)

- **`src/stance/instrumentation/pricing.py`** (NEW) — price table + `cost(usage,
  model)` pure function. Fully unit-tested (no API).
- **`src/stance/context.py`** (extend) — place ephemeral `cache_control`
  breakpoints (after system, after tools); helper to assemble messages with
  breakpoints. Surface which blocks carry a breakpoint.
- **`src/stance/instrumentation/token_budget.py`** (extend) — record the four
  `usage` fields + computed `cost` per turn (alongside the existing category
  snapshot); add `cache_read`/`cache_creation`/`input`/`output`.
- **`experiments/phase-1.0/cache_run.py`** (NEW) — fire a repeated-call loop under
  a given **prefix policy**, capture `response.usage`, compute cost, log
  append-only JSONL. **Reuse the `tool_call_stream` haystack as the cacheable
  history** (mirrors agentic structure; no new materials).

## Conditions (prefix policies — load-bearing, user sets the anti-patterns)

| policy | perturbation | predicted hit rate |
|---|---|---|
| `stable` (control) | none | climbs → ~1.0 after turn 1 |
| `timestamp_system` | changing timestamp in system | ≈0 (whole prefix invalid) |
| `tool_reorder` | shuffle tool order each turn | only system cached |
| `shape_mix` | vary history serialization each turn | cached up to first change |
| `restore` | anti-pattern K turns → stable K turns | recovers within ~1 turn |

## Pre-registration (§3.3 — lock before running)

- **P-B1:** `stable` hit rate ~0 on turn 1 (writes), then climbs to ~1.0
  (reads); cost/turn drops sharply (cached portion at 0.1×).
- **P-B2:** each anti-pattern floors hit rate at the *unperturbed-prefix fraction*;
  cost/turn near full price.
- **P-B3 (the finding):** anti-pattern cost ordering `timestamp_system` >
  `tool_reorder` > `shape_mix` (earlier perturbation → more invalidated → costlier).
- **P-B4:** `restore` recovers hit rate within ~1 turn (cache re-warms; damage
  transient, not permanent).

## Gotchas (wire in)

- **Min cacheable length** (~1024 Haiku / up to 2048 some models) — pad
  system+tools above ~2048 tokens or *nothing caches*.
- **Cache TTL 5 min** — fire calls back-to-back so reads persist; the *first* call
  always writes (creation), not reads (account for it in P-B1).
- **Determinism** — caching is a server behavior; unit-test the *wiring* with DI'd
  fakes, but the hit-rate/cost numbers need the real API.

## Tests (TDD)

- Offline (DI'd fakes): `cache_control` placement; `usage` parsing into TurnBudget;
  `pricing.cost()` exact on hand-computed cases (incl. cache fields).
- One real-API smoke (`@pytest.mark.slow`, 1–2 calls): `cache_read_input_tokens`
  is populated on a repeated prefix → confirms the path end-to-end.

## Cost estimate

Haiku; ~5 policies × ~10 turns × ~2 reps ≈ **100 calls**; prefix ~10k tok avg →
~1M input tokens. Anti-pattern arms pay full price (~$1); control pays cache-write
1.25× then 0.1× reads. **Estimate ~$3–5.** (No latency rig → no extra reps for
timing-noise.) Logged in `spend.md` (now exact, via `usage`).

## Validation gate

1. `make check` green (pricing + wiring + parsing unit-tested offline).
2. §3.3 predictions pre-registered before runs; **hit-rate + $/turn regenerate**
   from committed code + the pinned price table.
3. Results appended to `experiments/phase-1.0/results.md` (or a sibling) — the
   positional cost gradient + restore-recovery; §1.1 / §3.3 confidence updates.
4. **Latency is NOT in the gate** (non-reproducible); any TTFT sidebar is labelled
   our-setup-only.

## Division of labor (learning-first)

- **User (load-bearing):** the anti-pattern definitions (what exactly to perturb
  and where), the DV choice (ratified: hit-rate + $/turn), the §3.3 prediction
  ordering, the §1.1/§3.3 confidence updates.
- **Claude (plumbing):** `pricing.py`, `cache_control` wiring in `context.py`,
  `token_budget` extension, `cache_run.py`, tests.
- **Pair on:** interpreting the cost gradient + the position updates.

## Sequencing

Part of the **Phase 1.0 close batch** (Claude): clean-essay baseline (~$3) +
realism spot-check (~$2) + **Exercise B (~$3–5)** + phase-close ritual. Precedes
the DeepSeek migration phase (instrument validated on home turf first). Note the
batch nudges cumulative ~$53–55 vs the soft $50 cap — cap decision pending.
