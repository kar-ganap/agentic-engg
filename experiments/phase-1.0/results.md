# Phase 1.0 — Exercise A: Context-Rot under Competition (results)

> Committed result for Module 1 / §1.8 / §5.2 / §3.6. Numbers regenerate from
> committed code + run files (see **Reproducibility**). Scored offline by
> `experiments/phase-1.0/score.py`; raw runs in `runs/phase-1.0/` (gitignored,
> regenerable). Written 2026-06-04.

## Headline

Under **diffuse** competition (the whole haystack task-related, so competitors are
pervasive and their count scales with length — the real agentic regime), confident
needle retrieval **collapses**, while **neutral** (topic-unrelated filler) and
**localized** (a fixed handful of similar-but-wrong distractors) competition **hold a
passband flat to 100k** — no sustained collapse. The neutral arm, where only *length*
varies, shows **no knee through 100k** → **length *without competition* is benign;
competition at realistic density collapses it.** The finding **replicates across two
models**. (Precise form, per the method-review: the diffuse arm couples competitor
*count* with length by design — `count ∝ L` — so the clean isolation is the *neutral*
arm's length-only null, not a count-at-fixed-length cell; the latter is the deferred §5
sweep. "Competition, not token count" is the slogan; the null is what licenses it.)

**The collapse *knee* is potency-dependent (robustness check, below).** With the
templated diffuse competitors (uniform, ~75% rival *same-attribute* values) the knee is
~10–20k (Haiku) / ~5k (Sonnet). With **LLM-generated natural-phrasing** competitors of
mixed-but-genuine potency the knee shifts to ~50k but **still collapses** (0.20 @100k).
So competitor *relatedness/composition* sets the *knee position*, not whether collapse
happens — the phenomenon is robust to phrasing; the specific small budget is the
templated case, not universal.

This is direct own-substrate support for **§1.8** (signal density, not token count,
governs rot — confidence 70→78; the monotone potency ordering low<mixed<saturated is
additional evidence) and confirmation of **§5.2**'s agentic-budget-collapse prediction
(qualified: knee is potency-dependent). Mechanism: **discriminability loss** (the model
cannot bind the needle to its entity among competitors), expressed as **confabulation**
(Haiku) or **refusal** (Sonnet) — a capability-dependent failure mode logged as **§3.8**.

## Setup

- **Task:** single-needle lookup. Needle: *"The catalog number for the Meridian
  manuscript is QX-7793-LK."* Question (low lexical similarity, forcing semantic
  routing): *"What call number identifies the Meridian folio?"* Answer key:
  `QX-7793-LK`. Benign archive/catalog domain (the original security framing caused
  safety refusals — lessons §0.9).
- **Structure:** `tool_call_stream` (assistant tool_use + tool_result history — the
  controlled agentic structure, §3.6). Needle injected at depth ∈ {0.1, 0.5, 0.9}.
- **Competition conditions (the independent variable):**
  - `neutral` — filler topically unrelated to the needle (Chroma's bulk; isolates pure length).
  - `localized` — a fixed small set (n=4) of similar-but-wrong distractors in neutral bulk (Chroma's distractor design; competitor count constant in L).
  - `diffuse` — the whole haystack is task-related (density ρ=0.3); competitor count ∝ L. Competitors = other manuscripts' catalog numbers (varied phrasings) + same-manuscript different-attribute distractors (box number, shelf, page count, donor). **The agentic regime Chroma did not test.**
- **Lengths:** 1k–100k tokens (Haiku); 1k–20k (Sonnet spot-check). The *exact*
  `count_tokens` value is the x-axis; the builder's estimate only targets it.
- **Models:** `claude-haiku-4-5-20251001` (primary, 5 seeds × 3 depths = 15/point);
  `claude-sonnet-4-6` (within-family validation, 3 seeds × 3 depths = 9/point, ≤20k).
- **Scoring (two brackets, offline, deterministic — no LLM judge):**
  - **lenient** — the answer key appears anywhere (a *retrievability* floor).
  - **committed (primary)** — key present **AND** no hedge/refusal marker (a confident,
    usable answer). The *gap* between them is itself a result (see Mechanism).
  - Answer prompt forces concision (*"reply with ONLY the exact catalog number… else
    UNKNOWN"*) so the scorer measures retrieval, not verbosity (lessons §0.11). **No
    `tools` param** is passed — the model must answer from context, not "search."

## Results

### Haiku 4.5 — committed (15 runs/point)

| length | neutral | localized | diffuse |
|-------:|--------:|----------:|--------:|
|     1k |    1.00 |      0.93 |    1.00 |
|     2k |    0.80 |      0.93 |    0.87 |
|     5k |    0.67 |      0.93 |    0.67 |
|    10k |    0.73 |      0.80 |  **0.27** |
|    20k |    0.80 |      0.73 |  **0.00** |
|    50k |    0.87 |      0.80 |  **0.00** |
|   100k |    0.87 |      0.87 |  **0.00** |

### Haiku 4.5 — lenient / mentioned (15 runs/point)

| length | neutral | localized | diffuse |
|-------:|--------:|----------:|--------:|
|     1k |    1.00 |      1.00 |    1.00 |
|     5k |    0.80 |      0.93 |    0.87 |
|    10k |    0.87 |      0.87 |    0.47 |
|    20k |    0.93 |      0.73 |    0.53 |
|    50k |    0.87 |      0.80 |    0.40 |
|   100k |    0.87 |      0.93 |  **0.13** |

### Sonnet 4.6 — committed (9 runs/point, ≤20k)

| length | neutral | localized | diffuse |
|-------:|--------:|----------:|--------:|
|     1k |    0.78 |      0.67 |    0.44 |
|     2k |    1.00 |      1.00 |    0.33 |
|     5k |    0.67 |      1.00 |  **0.00** |
|    10k |    0.67 |      0.89 |  **0.00** |
|    20k |    0.67 |      0.56 |  **0.00** |

(Sonnet lenient collapses too: diffuse `0.44 → 0.33 → 0.11 → 0.11 → 0.00` — the key
string often does not appear at all. Full table via `score.py`.)

### Clean-essay baseline (harness validation — reproduces Chroma)

Before trusting the agentic curves, we confirm the instrument reproduces the known
clean-vs-distractor result on plain essays (Chroma's own substrate), high-sim, 5 seeds:

| length | neutral-high (clean) | localized-high (distractors) |
|-------:|---:|---:|
| 1k–20k | 1.00 | 1.00 |
| 50k | 1.00 | 0.93 |
| 100k | **1.00** | **0.80** |

- **Clean plateau exists:** neutral-high is a perfect 1.00 flat to 100k — the harness is
  *not* rot-prone by construction; given clean signal it finds a full passband.
- **Distractors shrink it:** localized-high declines to 0.80 (knee ~50k) — Chroma's
  distractor effect reproduced.
- **committed == lenient exactly** here → zero hedging in the easy high-sim case,
  confirming the committed/lenient gap on `tool_call_stream` is *competition + low-sim*
  driven, not baseline behavior.

This makes the whole study a monotone gradient: **clean essay high-sim (perfect plateau)
→ +fixed distractors (0.80@100k) → diffuse low-sim agentic (0@20k).** The instrument
shows no rot where there shouldn't be any, which legitimizes the diffuse collapse.

### Position (depth) and roll-off slope

**Depth decomposition (Haiku committed, by needle depth 0.1 / 0.5 / 0.9):** the diffuse
collapse is **uniform across needle position** — at 20k+ all three depths are 0
together (Δ ≤ 0.20 at every length). The larger spreads in the *neutral* arm (up to
Δ0.40–0.80 at 2–10k) are not a monotone middle-penalty (the worst depth moves around
by length) — they're small-N noise (n=5/cell) plus the folio wrinkle. **No systematic
position effect**, consistent with Chroma's no-NIAH-position-effect → the collapse is
*competition*-driven, not *position*-driven.

**Slope — the §5.2 third parameter** (Δ committed-accuracy per 10× tokens, OLS on
log₁₀ length):

| model | neutral | localized | diffuse |
|---|---:|---:|---:|
| Haiku 4.5 | −0.015 | −0.070 | **−0.572** |
| Sonnet 4.6 | −0.177 | −0.094 | **−0.378** |

Diffuse rolls off ~8× steeper than localized and ~38× steeper than neutral (Haiku) —
the quantitative form of "competition, not length." (Sonnet's neutral slope is steeper
and noisier: n=9, only to 20k, and the low-sim ceiling depresses the short end; the
diffuse-is-steepest ordering holds.)

## Findings vs. the pre-registration (§3.6, locked 2026-06-03)

- **P1 (diffuse > neutral; gap widens with L) — CONFIRMED, strongly.** Diffuse collapses
  to a *sustained* zero; neutral has no sustained collapse (the 5k neutral dip recovers
  to 0.87 by 100k — folio wrinkle, see Caveats). It is *qualitative*: neutral has no
  knee in range, so the gap is collapse-vs-passband, not a ratio.
- **P2 (diffuse steeper than localized; possible crossover) — SUPPORTED, QUALIFIED.**
  Diffuse ≫ localized confirmed (localized held to 100k; diffuse dead by 20k). **No
  crossover** — localized never rotted, so it was never "worse at short L." The
  length-coupled-noise mechanism is supported by the *split*, not a crossover.
- **P3 (harm ∝ per-competitor relatedness; H_A pocket at low relatedness) — UNTESTED.**
  Relatedness not swept this phase. Deferred.
- **P4 (hardest when distractors share needle structure) — UNTESTED directly,** but
  consistent with the binding-failure mode observed (model confuses Meridian's catalog
  number with other manuscripts' and with Meridian's other attributes). Deferred.

## Mechanism

**It is discriminability loss, not pure burial.** Two pieces of evidence:

1. **Committed → 0 *precedes* lenient → 0 (Haiku).** At 20k diffuse, committed is
   0.00 while lenient is 0.53 — the model can still *surface* the string but cannot
   *commit* to it as THE answer. Pure attention-dilution/burial would drop lenient
   too; it doesn't until ~100k (0.13). So the early knee is a **discriminability**
   failure (can't bind needle→Meridian among competitors); outright **burial** is a
   second, slower effect at extreme length.

2. **The failure mode is capability-dependent (→ new hypothesis §3.8).** From the
   recorded answers:
   - **Haiku confabulates** — *"found multiple catalog numbers for the Meridian
     manuscript: QX-7793-LK / BF-1573-NT…"*, or commits-then-undercuts.
   - **Sonnet refuses** — terse `UNKNOWN` (even at 1k), or *"the records are
     inconsistent and unreliable… cannot be reliably confirmed."*
   - Sonnet collapses **earlier** (zero by ~5k vs Haiku's ~20k) and its *lenient*
     score collapses too (it doesn't emit the string at all). **The stronger model is
     a better conflict-detector, not a more robust retriever** — so on committed
     accuracy it looks *worse* while behaving more appropriately about its own
     uncertainty. Provisional (n=9, two models); see §3.8 for the retraction criterion
     and the affordance-control caveat.

## Methods note — the committed scorer and its refinement (audit trail)

The committed scorer flags a hedge/refusal via `HEDGE_MARKERS`. During analysis we
found two **false-negative** classes and refined the detector (offline, $0), auditing
every answer that changed classification:

1. **Roleplay preamble ≠ hedge.** Haiku often says *"I need to search for the catalog
   number…"* then answers correctly from context (it has no tools). The marker
   `"need to search"` wrongly flagged these. **Removed it** — a preamble is preamble as
   long as the core answer is unhedged. 8 Haiku answers flipped hedge→commit; all 8
   verified genuine commits (incl. localized correctly splitting box-number 4471 from
   catalog QX).
2. **`"multiple"` was too blunt.** *"multiple **references**"* (search breadth, preamble)
   vs. *"multiple **catalog numbers**"* (genuine answer ambiguity) are different.
   **Replaced bare `"multiple"` with `"multiple catalog"` + `"different catalog"`.**
   Verified: the BF-1573-NT confabulation and the *"…QX-7793-LK. However, I should
   note…"* hedges stay flagged; clean *"multiple references… QX"* commits now count.

**Effect:** the refinement *sharpened* the contrast (localized's spurious 20k dip
0.47→0.73 was preamble false-negatives) and did **not** rescue diffuse 10k+ (those are
genuine key-absent binding failures, robust to every detector variant). The headline is
therefore not a scorer artifact: the *lenient* curve (immune to the detector) shows the
diffuse collapse independently.

## Robustness — is the collapse a templating artifact? (realism check)

The diffuse competitors above are *templated* (`"the catalog number for the {X}
manuscript is {code}"`). To test whether the collapse is an artifact of templated
phrasing, we re-ran diffuse with **LLM-generated** competitor lines drawn from a pinned
pool (`gen_competitor_pool.py` → `data/competitor_pools/realism_v*.json`; the run samples
deterministically by seed, so it regenerates). Two pools, Haiku committed:

| length | templated | v1 (loose prompt) | v2 (relatedness-matched) |
|-------:|---:|---:|---:|
| 5k | 0.67 | 1.00 | 0.80 |
| 20k | **0.00** | **1.00** | 0.80 |
| 50k | 0.00 | — | 0.40 |
| 100k | 0.00 | — | **0.20** |

- **v1 had *no* effect — but it was a confound, not a refutation.** Only **15%** of v1's
  lines actually asserted a catalog number (the rest embedded the code as a manuscript
  *ID*, or were other attributes), so v1 inadvertently *lowered relatedness*. It varied
  realism **and** potency at once — a botched check, and a measurement lesson (hold the
  potency axis fixed; see lessons).
- **v2 (relatedness-matched, ~96% genuinely competing, natural phrasing) reproduces the
  collapse — just with a later knee.** It holds ~0.80 through 20k, then declines to 0.40
  (50k) → 0.20 (100k). So **natural-phrasing potent competition is not benign; the
  collapse is not a templating artifact.**
- **Composition/potency sets the *knee*, not the *floor*.** Templated (uniform, ~75%
  rival same-attribute values): knee ~5–10k, floor 0 by 20k. v2 (natural, ~46%): knee
  ~50k, still falling. The monotone ordering **v1 (low potency) < v2 (mixed) < templated
  (saturated)** is clean §1.8 potency evidence.
- **Honest correction:** an earlier read of v2-to-20k called 0.80 a "plateau." Extending
  to 100k showed it is a *delayed collapse*, not a plateau — so the "≈10–20k free budget"
  figure is the **templated/saturated** case, not universal.

*Open (→ §5 sweep, not closed here):* v2 differs from templated in *both* composition
(46% vs 75% potent) and phrasing (varied vs uniform), so the knee-shift isn't yet
attributed between them. The controlled relatedness/composition sweep (§5) isolates it;
a one-off v3 was deliberately skipped (sandbox-pull).

## Caveats / threats to validity

- **Unique-string needle = retrievability ceiling.** `QX-7793-LK` is exact-matchable;
  this measures *retrievability* (the easier quantity, §1.3). Active-influence budget is
  plausibly **≤** this — the agentic problem is, if anything, worse.
- **Folio wrinkle (low-sim question).** The synonymized question (*"folio / call
  number"* vs. needle's *"manuscript / catalog number"*) makes some models pedantically
  answer `UNKNOWN` even in *neutral* — depressing the absolute neutral ceiling (~0.8,
  not 1.0) and causing the short-length neutral dip. The *cross-condition contrast* is
  unaffected (same question across all conditions); only absolute neutral height is.
- **`diffuse_density = 0.3` is a knob, not swept.** A different density would move the
  knee; we fixed one operating point. P3 (relatedness sweep) also deferred.
- **Naive `passband_knee` is fooled by the neutral dip-recover.** Anchored on the 1k
  point, it reports a spurious neutral "knee" at 5k. We use *sustained zero* for the
  headline; only diffuse qualifies.
- **§3.8 is provisional:** n=9/point, one (structure × similarity) cell, two models; the
  explicit `UNKNOWN` affordance may inflate Sonnet's refusal rate (control test pending).
- **Single agentic structure:** `tool_call_stream` only (low-sim). `research_doc_stream`
  and cross-provider (DeepSeek) replication are deferred to next phase.

## Reproducibility

```bash
# regenerate raw runs (writes runs/phase-1.0/*.jsonl; needs ANTHROPIC_API_KEY in .env)
uv run python experiments/phase-1.0/run.py --item 3 --competition diffuse   --go    # + neutral, localized
uv run python experiments/phase-1.0/run.py --item 3 --competition diffuse --model claude-sonnet-4-6 --max-len 20000 --max-seeds 3 --go
uv run python experiments/phase-1.0/run.py --item 2 --similarity high --go          # clean-essay baseline
# realism check: regenerate the pinned pool (one LLM call) then run diffuse from it
uv run python experiments/phase-1.0/gen_competitor_pool.py --version v2 --go
uv run python experiments/phase-1.0/run.py --item 3 --competition diffuse --similarity low \
    --competitor-pool data/competitor_pools/realism_v2.json --go
# re-score (offline, no API) — prints all tables above
uv run python experiments/phase-1.0/score.py
```

- Pinned: models above; seeds 1–5 (Haiku) / 1–3 (Sonnet); depths {0.1,0.5,0.9};
  density 0.3; n_distractors 4. Run records are self-describing (stamp `system`,
  `max_tokens`, `diffuse_density`, `n_distractors`, `competitor_pool_size`, full
  `answer`). The realism pool is a **pinned artifact** (`realism_v2.json`); the run
  samples it by seed, so it regenerates despite one LLM call.
- **Cost (logged in `tasks/spend.md`):** Haiku evidence ~$15.80, Sonnet ~$3.51,
  baseline ~$5.37, realism (v1+v2) ~$4 (reproducible regeneration cost; input-dominated).

## Synthesis updates made (2026-06-04 / -05)

- **§1.8** 70→78 + retraction criterion + experimental Evidence entry (monotone
  potency ordering v1<v2<templated is additional support).
- **§5.2** own-substrate-confirmed, **qualified**: the budget collapses, but the knee is
  *potency-dependent* — ≈10–20k for templated/saturated competition, ≈50k for natural
  mixed competition (still collapsing by 100k). The "≈10–20k" is not universal.
- **§3.6** OUTCOME block (P1 ✓ / P2 qualified / P3–P4 untested; Sonnet + realism checks done).
- **§3.8** new hypothesis: capability shifts failure mode (confabulate→refuse), knee earlier.
- **§1.3** candidate architectural mechanism note (arXiv:2603.10123), held loosely.
