# Phase 1.0 Extension — Cross-Family Validation Attempt (results)

> Goal: discharge §1.8's retraction clause (b) — *"diffuse competition fails to
> collapse retrieval in a different model family"* — by replicating the headline
> on DeepSeek. **Outcome: clause (b) remains OPEN.** The attempt hit two genuine
> walls and produced a more important finding: the diffuse-collapse is entangled
> with **structure × needle-question-similarity**, so it does not replicate
> straightforwardly across providers or structures with the current needle.
> Written 2026-06-05. Numbers regenerate from committed code + `score.py`.

## Setup

DeepSeek runs use the **Anthropic-compatible endpoint** (`api.deepseek.com/anthropic`)
so the whole pipeline is reused unchanged; tokens are counted on Anthropic-Haiku for a
consistent cross-provider x-axis (`run.py --provider deepseek`; see
`docs/phases/phase-1.0-extension-plan.md`). Models: `deepseek-v4-flash` (workhorse).

## Attempt 1 — DeepSeek on `tool_call_stream` (CONFOUNDED)

Full grid (neutral/localized/diffuse × low-sim × to 100k × 5 seeds). The Step-0 gate
confirmed the endpoint accepts our pipeline. But the results are **confounded by a
provider-specific behavior**: DeepSeek emits its internal tool-call markup as text
(`<｜｜DSML｜｜tool_calls> … invoke name="search" …`) instead of answering — the
`tool_call_stream` history primes it to *continue calling the search tool*. Our §0.11
"remove the `tools` param so it must answer" fix is Anthropic-specific and does not
transfer. (DeepSeek's *documented* tool format is structured OpenAI-style `tool_calls`;
"DSML" is leaked internal markup, surfaced because no tools were declared.)

Category breakdown (committed scorer; n=105/condition):

| condition | committed | %tool-call-leak | %empty | committed \| *attempted* |
|---|---:|---:|---:|---:|
| neutral | 0.80 | 15% | 2% | 0.97 |
| localized | 0.84 | 10% | 6% | 0.99 |
| diffuse | 0.59 | 13% | **24%** | **0.94** |

Reading:
- **The tool-call-leak is uniform (~10–15%), not competition-driven** → it depresses all
  conditions equally; it doesn't create the diffuse gap. Removable noise.
- **When DeepSeek actually answers, it discriminates the needle fine even under diffuse**
  (`committed|attempted ≈ 0.94`, flat to 100k) — it does **not** show the Anthropic
  *discriminability collapse* (confabulate/mis-bind; committed→0).
- **Diffuse does affect DeepSeek — but via abstention.** The empty-answer rate is
  competition-driven (**24% diffuse vs 2% neutral**); DeepSeek returns nothing (or a
  leaked tool-call attempt) rather than mis-binding. A *different failure mode* than
  Haiku (confabulate) or Sonnet (refuse-with-text).

**Verdict:** inconclusive for clause (b). The Anthropic mechanism does not replicate;
DeepSeek's diffuse degradation is an abstention/tool-call-continuation effect on a
structure that is **provider-confounded** for cross-family comparison.

## Attempt 2 — `clean_essay` (provider-neutral structure) on Haiku (NO CLEAN EFFECT)

To remove the tool-call confound, we ran the *provider-neutral* `clean_essay` (prose,
no tool-call history) — first on Haiku, to confirm the effect even appears before
testing DeepSeek. It does not isolate cleanly. Haiku `clean_essay` low-sim, committed:

| length | neutral | localized | diffuse |
|---:|---:|---:|---:|
| 1k | 0.67 | 1.00 | 1.00 |
| 5k | 0.27 | 0.87 | 0.53 |
| 20k | 0.40 | 0.93 | 0.33 |
| 100k | 0.40 | 0.40 | 0.20 |

**The neutral *control* is broken** (`committed ≈ lenient` ≈ 0.4 — the key is *absent*,
not hedged). Inspecting answers: in a reading-comprehension framing the model **refuses
to bridge the low-sim synonyms** — needle says "Meridian *manuscript* **catalog** number,"
question asks "Meridian *folio* **call** number," and it answers *"the text does not
contain a call number for a 'Meridian folio'"* — **even with zero competitors.** The same
low-sim question *held* (~0.8 neutral) on `tool_call_stream`, where the "I searched and
found X" framing made the model willing to bridge. **The folio-wrinkle is
structure-sensitive — far worse on prose.**

Because the control is broken, **diffuse ≈ neutral** here (both ~0.4–0.5; the folio floor
*masks* any competition effect). So this is **inconclusive, not a clean negative.**

The obvious fix — high-sim — would likely make diffuse **too easy**: the needle phrase
"catalog number for the Meridian manuscript" is a *unique, verbatim* match for a high-sim
question, and competitors name *other* manuscripts, so exact-phrase matching finds the
needle and diffuse can't bite. So `clean_essay` can't hit the "neutral-holds **and**
diffuse-collapses" zone that `tool_call_stream` low-sim did.

## The finding: structure × needle-similarity entanglement

The clean diffuse-collapse on `tool_call_stream` low-sim exploited a **structure-specific
sweet spot** — forgiving on the folio-wrinkle in the neutral *control*, yet vulnerable to
competition in *diffuse*. Porting to prose breaks it from both ends (low-sim wrecks the
control; high-sim defeats the competition). **The effect's cross-structure /
cross-provider generality is therefore not established with the current needle.**

This does **not** undercut the headline within its regime — `tool_call_stream` × low-sim
on Anthropic is real and reproducible (`results.md`). It bounds the *generality* claim.

## Disposition

- **§1.8 stays 78** + an explicit **generality caveat**: the diffuse collapse is
  established in the `tool_call_stream` × low-sim regime; cross-structure /
  cross-provider generality is **not** established and is entangled with needle design.
  Clause (b) is **open and harder than anticipated** (needs a structure-invariant needle).
- **§3.8:** DeepSeek-flash adds a third failure mode under diffuse — **abstention**
  (empty/tool-call-retreat) — distinct from Haiku-confabulate and Sonnet-refuse-with-text.
  Recorded with the cross-family-confound + tool-call-leak caveats; does not on its own
  advance §3.8.
- **Not run:** DeepSeek `clean_essay` leg (no clean Haiku effect to replicate → would be
  non-information). The prompt-hardened `tool_call_stream` run (band-aid; introduces a
  prompt asymmetry; the empty-rate already shows the abstention signal).

## What would actually discharge clause (b) (deferred)

A **needle/question pair with structure-invariant findability** — moderately
synonymized (not pedantically rejected like folio↔manuscript, not verbatim-matchable
like high-sim), so a clean *control* holds **and** diffuse competition still bites on
both prose and tool-stream. Re-validate on Anthropic, then test DeepSeek (which, on a
prose structure, has no tool-call history to leak). A mid-similarity probe (~$3) is the
cheap first step; a full needle redesign is the thorough one.

## Cost (logged in `tasks/spend.md`)

DeepSeek `tool_call_stream` grid ~$1.30 (315 runs); Haiku `clean_essay` low-sim ~$8.17
(315 runs); + Step-0 gate ~$0.001. ~$9.5 total for the (inconclusive-but-informative)
cross-family attempt.

## Lessons (→ `tasks/lessons.md`)

- **§0.17** — cross-provider comparisons via a *tool-call-format* structure are confounded
  (the history primes provider-specific tool-call continuation; the no-tools fix is
  Anthropic-specific). Use a provider-neutral structure.
- **§0.18** — a needle/question tuned for one structure may not transfer; **verify the
  control holds before interpreting the treatment** (the low-sim folio-wrinkle wrecked the
  prose control while holding on tool-stream).
