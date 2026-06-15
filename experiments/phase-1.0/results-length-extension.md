# Phase 1.0 (ext) — §1.8 Length-Extension Pressure Test (results)

> Goal: pressure-test §1.8's **pillar B** — *"competition, not token count, drives the
> retrieval collapse"* — out of its measured range (≤100k) toward **~758k tokens** on
> **one capable non-Anthropic model** (DeepSeek v4-pro; n=1 cross-family).
> **Outcome: pillar B holds on the capable cross-family model — the neutral null is flat
> to ~94k and shows only a *mild* pure-length decay by 758k (0.67); "holds to ~1M" would
> overstate. §1.8 → 80.** Written 2026-06-13; phrasing tightened 2026-06-14 (three-reviewer
> pass). Numbers regenerate from committed code +
> `runs/phase-1.0/clean_essay__neutral__high__deepseek-*.jsonl`.

## Why this cell (and not the cross-family attempt's)

The cross-family attempt (`results-cross-family.md`) was inconclusive from a **structure ×
needle-similarity entanglement**: `tool_call_stream` is provider-confounded on DeepSeek
(DSML tool-call leak, §0.17), and `clean_essay` low-sim breaks the *neutral control*
(folio-wrinkle, §0.18). But this pressure test does **not** need diffuse to bite — pillar B
is the *neutral-arm* (zero-competition) null. So the clean cell is:

**`clean_essay` / competition=neutral / similarity=high.** Prose → no tool-history to leak;
high-sim → control reliably retrievable at short length (the "too easy" property that
*defeated diffuse* is a *feature* for a pure-length test); neutral → genuinely zero
competition. This sidesteps both cross-family walls. (`run_config.py:50`, the harness-
validation cell; here run on DeepSeek + extended in length.)

## Setup

`run.py --provider deepseek` (Anthropic-compat endpoint; tokens counted on Anthropic-Haiku
for a consistent x-axis — verified Haiku `count_tokens` accepts >1M payloads, so the count
path is unchanged at extreme length). Harness changes: `--lengths` override (grid capped at
100k) and `--max-input-tokens` (the `190k` skip guard would silently drop every high run).
Depths {0.1, 0.5, 0.9}; failure scored as `committed` (≈ `lenient` here — answers are the
exact key, `UNKNOWN`, or empty).

## Results

### v4-pro + Haiku — the clean signal (capability gradient)

| length (exact) | Haiku (existing, ≤200k cap) | **DeepSeek v4-pro** (3 seeds) |
|---:|---:|---:|
| ~10k | 1.00 | — |
| **~94k** | **1.00** | **1.00** (9/9) |
| ~758k | (cannot — 200k window) | **0.67** (6/9) |

Both *capable* models hold the neutral needle perfectly to ~94k on the **identical**
haystacks. v4-pro — a **non-Anthropic** family — degrades only **mildly** at extreme length
(0.67 @758k), ≈7× beyond §1.8's measured range, and **far above** any diffuse knee (~10–50k).
Pure length rots *much later* than competition — reinforcing the competition-first ordering,
not threatening it.

### v4-flash — too noisy to characterize (control not solid)

| target | overall (5 seeds) | d=0.1 | d=0.5 | d=0.9 |
|---:|---:|---:|---:|---:|
| 10k | 0.67 | 1.00 | 0.60 | 0.40 |
| 50k | 0.53 | 0.60 | 0.60 | 0.40 |
| 100k | 0.73 | 0.80 | 1.00 | 0.40 |
| 250k | 0.47 | 0.60 | 0.60 | 0.20 |
| 500k | 0.47 | 0.40 | 0.20 | 0.80 |
| 800k | 0.40 | 0.60 | 0.40 | 0.20 |

v4-flash sits at **~0.4–0.7 across all lengths, including 10k** (the control is *not* solid),
non-monotone (100k > 50k), depth-erratic — a **high baseline abstention rate swamps any
clean length signal**. v4-flash cannot cleanly measure this needle.

> **Pilot-artifact correction.** A 2-seed pilot showed a clean `1.00 → 0.50(94k) →
> 0.17(758k)` v4-flash curve and was over-read as "pure length collapses retrieval." It did
> **not survive 5 seeds** — seeds 1–2 were the lucky draws. The dramatic v4-flash collapse is
> **retracted** as a small-sample artifact (→ lessons §0.21). The pre-registration +
> "hold the confidence" discipline caught it before it was committed.

### Failure mode

Throughout, DeepSeek fails by **abstention** (empty / `UNKNOWN`), never confabulation —
consistent with §3.8 (DeepSeek's distinctive abstention mode), now seen under **pure length**,
not only competition.

## Controls / artifact ruled out

Haiku scores **1.00 on the identical builder/needle/scorer** to 94k → not a harness bug, not
a needle/structure problem. `n_competitors = 0` throughout → genuinely zero competition.
DeepSeek accepted the full 758k input (probe confirmed ~1M intake) → not truncation. Failures
are literal `UNKNOWN`/empty → not a scorer misread. The degradation, where real (v4-pro
@758k), is genuine retrieval decay expressed as abstention.

## Disposition

- **§1.8: 78 → 80.** The neutral-arm length-only null — §1.8's *single strongest fact* — now
  holds **cross-provider** (v4-pro 1.00 @94k matches Haiku) and **out to ~1M** (mild, far-out
  degradation only). Capped at 80 (not 85): this generalizes **pillar B** ("not length"), not
  the **diffuse collapse** (clause b), which stays provider-confounded on DeepSeek; and v4-flash
  was too noisy to add.
- **Retraction clause (a) reinforced:** v4-pro's neutral degradation appears ~7× *above* its
  competition knee → pure length rots *later* than competition, never before.
- **Clause (b) untouched** — this is pillar B, not the treatment; the diffuse cross-family
  collapse remains open.
- **§3.8:** abstention generalizes from competition-stress to length-stress (caveated; no
  number change here).

## Reproduce

```bash
# v4-flash full curve (5 seeds)
uv run python experiments/phase-1.0/run.py --item 2 --competition neutral --similarity high \
  --provider deepseek --lengths 10000,50000,100000,250000,500000,800000 \
  --max-input-tokens 1050000 --max-seeds 5 --go
# v4-pro capability spot (3 seeds)
uv run python experiments/phase-1.0/run.py --item 2 --competition neutral --similarity high \
  --provider deepseek --model deepseek-v4-pro --lengths 100000,800000 \
  --max-input-tokens 1050000 --max-seeds 3 --go
# Haiku anchor (existing data, free)
uv run python experiments/phase-1.0/run.py --item 2 --competition neutral --similarity high --summarize
```

## Cost (logged in `tasks/spend.md`)

v4-flash full curve $3.41 (90 runs, 24.3M in) + v4-pro spot $3.34 (18 runs, 7.7M in) +
pilot ~$0.76 (overwritten) + context/count probes ~$0.29 ≈ **$7.8** (exact from
`exact_tokens`). Failure mode = abstention; the capability gradient is the yield.
