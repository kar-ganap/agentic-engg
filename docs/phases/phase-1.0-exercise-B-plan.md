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

*Multipliers (write 1.25×/5m, 2×/1h, read 0.1×) are docs-confirmed 2026-06-05. The
**base** input/output $/MTok above are from memory — verify per-model before the run.*

`cost = input·p_in + output·p_out + cache_creation·p_write + cache_read·p_read`
(all per token). Cache-hit rate = `cache_read / (cache_read + cache_creation + input)`.

## Build (plumbing — Claude scaffolds)

- **`src/stance/instrumentation/pricing.py`** (NEW) — price table + `cost(usage,
  model)` pure function. Fully unit-tested (no API).
- **`src/stance/context.py`** (extend) — place ephemeral `cache_control`
  breakpoints **after tools, after system, and at end-of-history (moving)** — 3 of
  the 4 allowed; required to resolve the per-level gradient. Helper to assemble
  messages with breakpoints; surface which blocks carry one.
- **`src/stance/instrumentation/token_budget.py`** (extend) — record the four
  `usage` fields + computed `cost` per turn (alongside the existing category
  snapshot); add `cache_read`/`cache_creation`/`input`/`output`.
- **`experiments/phase-1.0/cache_run.py`** (NEW) — fire a repeated-call loop under
  a given **prefix policy**, capture `response.usage`, compute cost, log
  append-only JSONL. **Reuse the `tool_call_stream` haystack as the cacheable
  history** (mirrors agentic structure; no new materials).

## The invalidation hierarchy (docs-confirmed 2026-06-05) — drives everything

Anthropic caches by exact prefix match; the hierarchy is **`tools → system →
messages`**, and *"changes at each level invalidate that level and all subsequent
levels."* So **tools is the cache root** — a tool change invalidates *everything*
(this is the mechanistic core of §1.1, and why Manus harps on tool stability).
Earlier mental model (system-first) was wrong; corrected here.

## Anti-pattern set ① (locked) + conditions

Set ① spans all three levels so the gradient is observable (C2/③ compaction-bridge
optional, deferred). **3 breakpoints: after tools, after system, end-of-history
(moving).** Multi-breakpoint is *required* — with a single end-breakpoint all
anti-patterns full-miss and the gradient is invisible.

| policy | level perturbed | what invalidates | predicted cache_read |
|---|---|---|---|
| `stable` (control) | none | new turn only | ~100% of old prefix |
| `tool_reorder` (B1) | **tools (root)** | tools+system+messages = **all** | **~0%** |
| `timestamp_system` (A1) | system | system+messages (tools stays) | **tools/total** |
| `shape_mix` (C1) | messages (*re-serialize ALL prior tool results*) | from first history block | **(tools+system)/total** |
| `restore` | B1 K turns → stable K turns | re-warm | recovers by **turn 2** |

## Pre-registration (§3.3 — lock before running; confidence omitted per author)

Predictions are **computed** from the documented hierarchy + `count_tokens`-measured
spans (not guessed). Illustrative budget `tools 4,500 / system 1,500 /
history@10 8,000 / new 800` (exact spans measured at run time):

- **P-B1 (baseline):** `stable` writes the prefix on turn 1, then `cache_read`
  climbs toward `cached/(cached+new)` (≈94% here, **not** exactly 1.0 — the new turn
  is always uncached). Cost/turn drops ~8×.
- **P-B2 (cardinal — the test):** each anti-pattern's `cache_read` = the fraction of
  the prefix *before* the perturbed level:

  | anti-pattern | cache_read (of 14k) | $/turn (Haiku) | × vs stable |
  |---|---:|---:|---:|
  | stable | ~100% | $0.0024 | 1.0× |
  | C1 shape_mix | ~43% (tools+system) | $0.0116 | ~4.8× |
  | A1 timestamp | ~32% (tools) | $0.0133 | ~5.5× |
  | B1 tool_reorder | ~0% | $0.0185 | ~7.7× |

- **P-B3 (ordinal):** cost **B1 > A1 > C1 > stable** (tools-root worst). *Corrected
  ordering* — earlier draft had A1>B1.
- **P-B4 (restore):** hit-rate returns to stable levels by **turn 2** (turn 1
  re-writes, turn 2+ reads) → damage is transient, not permanent.
- **(c) deliverable, not a prediction:** report the worst-case $/turn ratio as our
  own number vs Manus's "~10×" (climbs toward 10× as cached-prefix/new-turn grows).

**Calibration (allowed; not peeking):** a 2–3 turn `stable`-only pilot to confirm
caching *engages* on the >4,096 prefix and that the cached/new split matches
`count_tokens`. Anti-patterns are NOT piloted — they remain genuine forecasts.

## Gotchas (docs-confirmed 2026-06-05 — wire in)

- **Min cacheable length = 4,096 tokens for Haiku 4.5** (1,024 for Sonnet 4.6). Below
  this, `cache_control` is *silently ignored* — no caching, no error. **Pad
  system+tools well above 4,096**, and **tools ≥4,096 *alone*** so the after-tools
  breakpoint caches independently (required to separate B1 from A1).
- **20-block lookback** — the system checks ≤20 block-boundaries per breakpoint. Keep
  per-turn block growth ≪20 (a burst of many tool calls in one turn can blow past it
  and silently miss the moving-history hit).
- **Cache TTL 5 min, refreshes on each hit** — fire calls back-to-back; the *first*
  call writes (creation), reads resume turn 2 (account for it in P-B1/P-B4). 1-hour
  TTL exists at 2× write but we don't need it.
- **C1 must re-serialize *all* prior tool results** (invalidate from the first history
  block) — if it only touches the latest result it's ≈ stable and P-B2 collapses.
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
