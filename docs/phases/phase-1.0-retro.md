# Phase 1.0 — Context Engineering (Module 1) (Retro)

**Closed:** 2026-06-05
**Branch:** `phase-1.0-context-engineering`
**Critical phase boundary?** **Yes** — context-engineering spine + position commitments (§1.8, §1.1) → three-reviewer pass required before merge.

## Summary

First experimental evidence on our own substrate, turning Module 1's theory-only positions into measured ones. Two exercises:

- **Exercise A — context rot under competition (VERY DEEP).** Built a re-pointable rot evaluator (`haystack`/`runner`/`accuracy`/`score`) and measured retrieval vs. input length across a **competition** axis we introduced (`neutral` / `localized` / `diffuse`). Finding: **diffuse competition (pervasive, length-scaling) collapses confident retrieval; neutral & localized hold a passband to 100k → competition, not token count, drives context-rot onset.** Cross-model (Haiku + Sonnet), harness-validated (clean-essay reproduces Chroma), construct-validated (LLM-generated competitors → not a templating artifact).
- **Exercise B — KV-cache anti-patterns (DEEP).** Built exact cost instrumentation (`pricing`, `usage`-capture, `with_cache_breakpoints`) and measured cache degradation under prefix anti-patterns. Finding: **a positional cost gradient set by the `tools → system → messages` hierarchy — tool changes are worst (cache root, 7× a stable prefix).**

## Decisions made

| Decision | Choice | Why |
|---|---|---|
| Rot independent variable | **competition** axis: neutral / localized / **diffuse** | Chroma tested localized (fixed distractors); agentic contexts are diffuse (count ∝ L) — the gap worth measuring (§3.6). |
| Scoring | **committed** (key present, unhedged) primary + **lenient** (key present) bracket | The gap *is* a result (discriminability vs burial, §3.8); committed measures usable answers (§0.11). |
| Scorer refinement | drop roleplay-preamble markers; `"multiple"` → `"multiple catalog"`/`"different catalog"` | Preamble ≠ hedge; audited every flip (§0.13). Sharpened the contrast, didn't manufacture it. |
| Realism check design | **choice B** (LLM owns names+codes) + collision filter, **relatedness-matched (v2)** | Cleanest construct-validity test; v1 confounded realism×relatedness (§0.13). |
| Cache DVs | **hit-rate + $/turn (exact, from `usage`)**; latency **dropped** | Only `usage`-derived numbers regenerate; latency is network/decode-confounded, non-reproducible. |
| Cache condition isolation | per-policy prefix nonce | Shared 5-min server cache bleeds across conditions (§0.14). |
| Model tiering | Haiku 4.5 primary; Sonnet 4.6 spot-check | Rots earlier/cheaper; §0.8 — magnitudes Haiku-specific, Sonnet calibrates capability. |
| Budget | soft cap 50→75 (lifted) | Close batch (baseline + realism + Exercise B) needed headroom; soft = warning. |

## Validation gate

| Gate | Status |
|---|---|
| Tests pass | **86/86** (`make test`); +real-API smokes (`make test-all`) |
| Lint / typecheck clean | `make check` green (ruff + mypy `--strict` + pytest) |
| Pre-registered before runs | §3.6 (P1–P4, 2026-06-03), Exercise B sub-plan (P-B1–P-B4, 2026-06-05) |
| Reproducibility | numbers regenerate from committed code + pinned seeds/prices; raw runs gitignored but regenerable; realism pool pinned |
| Retro written | This file |
| `/learn` written | **pending** (raw lessons §0.12–§0.14 filed; structured rule pass next) |
| Three-reviewer parallel pass | **pending** (critical boundary — run before merge) |

## Concept-stream output (synthesis-anchored)

This is the paper-relevant yield. Each position moved on *measured* evidence:

- **§1.8 (signal density, not token count) 70→78** (trimmed from 80 in the reviewer pass — one structure × one family; the +8 is licensed by the neutral-arm length-only null, not replication breadth). Own-substrate confirmation: at matched length, diffuse competition collapses retrieval while neutral (length-only) shows no knee to 100k. Cross-model within-family. Retraction criterion added; monotone potency dose-response (realism v1<v2<templated) corroborating. *The phase's headline position.*
- **§5.2 (agentic free budget) — own-substrate confirmed, then QUALIFIED.** The collapse is real, but the *knee is potency-dependent*: ~10–20k for templated/saturated competition, ~50k for natural mixed competition (still collapsing by 100k). The "≈10–20k budget" is the saturated case, not universal — an honest walk-back surfaced by the realism check.
- **§3.6 (rot on agentic structures) — OUTCOME recorded.** P1 confirmed (strong); P2 supported-qualified (no crossover — localized never rotted); P3/P4 untested. Sonnet + realism spot-checks done; DeepSeek deferred.
- **§3.8 (capability shifts failure mode) — NEW, conf 45.** Sonnet collapses earlier/harder and fails by *refusal* where Haiku *confabulates* → a stronger model is a better conflict-detector, not a more robust retriever. Provisional (n=9); seed of a contribution candidate.
- **§1.3 (J-shape active-attention) — mechanism note added.** arXiv:2603.10123 (*Lost in the Middle at Birth*): architectural positional-sensitivity bias at init, modulated by training → regime-specific shape. Held loosely (sensitivity≠accuracy; untestable on our API setup). No confidence change. Primary source corrected an inflated secondhand summary.
- **§1.1 (tool/prefix stability) 75→80** (trimmed from 82 in the reviewer pass; sub-split cache-leg ~90 / coherence-leg ~65). Exercise B confirmed the *cache-economics* leg: tools are the cache root; mutating them is the worst anti-pattern (7× stable cost). The *model-coherence* leg remains literature-only (untested) → not fully closed.
- **§3.3 (cache hit-rate vs anti-patterns) — CONFIRMED + sharpened.** Positional cost gradient B1(tools)>A1(system)>C1(messages)>stable, with cardinal `cache_read` fractions matching the documented hierarchy.

*Methods/Results live in* `experiments/phase-1.0/results.md` *(Exercise A)* *and* `results-exercise-B.md` *(Exercise B).*

## Process-stream output

- **§0.12** log spend at run time (the ~$42-vs-$16 reconstruction).
- **§0.13** isolate one factor in a comparison; characterize the asymptote before calling a plateau (the realism v1 confound + the v2 "plateau" misread).
- **§0.14** isolate conditions sharing a stateful backend (the KV-cache cross-condition bleed; 3 re-runs to diagnose).

## Out of scope (deferred to specific later phases)

- `research_doc_stream` (2nd agentic structure) → Phase 1.0 extension (DeepSeek workhorse)
- §5 relatedness sweep (choice B) + density sweep → extension (previewed by realism dose-response)
- Cross-provider replication (DeepSeek) → extension; discharges §1.8 retraction clause (b)
- §3.8 fuller test (≥3-model ladder, refusal-affordance control) → extension
- §1.1 **model-coherence** experiment (does mutation degrade behavior, not just cost?) → Phase 1.1
- §3.7 (tool-result clearing / compaction) + §3.4 (failure-shaped padding) → Phase 1.0 ext / 1.1
- Clean restore-isolation (per-policy tool-content uniqueness) → if P-B4 needs hardening

## Throughline property progress

**Contribution (Property 4) advanced** — two contribution candidates now have data: (1) context rot on agentic structures, sharpened to the **localized↔diffuse regime distinction + potency dose-response**; (2) capability-dependent failure modes (§3.8). Logged in `tasks/contribution-candidates.md`. Ingest / query / re-evaluation: not this phase (Stage 2+).

## Three-reviewer pass record (2026-06-05, critical boundary)

Three Opus reviewers, clean context, ≥80-confidence filter. Method-rigor and framing-stress returned **no ≥80 issues** (method-rigor independently regenerated every headline number; scorer verified non-circular via the lenient curve). Prior-art returned **three ≥80 findings**; all dispositioned by reading the cited sources **firsthand** (which corrected the reviewer's gloss three times — logged as a lesson):

| # | Finding (sev) | Disposition |
|---|---|---|
| 1 | **RULER (arXiv:2404.06654) uncited; pre-empts localized↔diffuse *count* axis** (88) | **Accepted, reframed.** Read firsthand: RULER's Multi-key NIAH spans fixed (≈localized) → full-haystack (≈diffuse) distractor count, same headline. Dropped "localized↔diffuse is a contribution"; kept the verified delta RULER lacks — **relatedness/potency dose-response, agentic substrate, committed-vs-mentioned collapse**. (§3.6, contribution-candidates) |
| 2 | **§3.8 re-derives the fallback literature** (82) | **Partially rejected, reframed sharper.** Read firsthand: *From Loops to Oops* (2407.06071) + OpenAI find the **opposite** scaling (stronger → more hallucination/less abstention) in the *parametric* regime — so §3.8 **contradicts**, not re-derives. Framed as a candidate **regime-dependent reversal**; affordance-control now mandatory; conf held **45**. (§3.8) |
| 3 | **KV-cache gradient is documented mechanics, not novel** (80) | **Accepted.** Read KVFlow firsthand — it's *eviction/scheduling*, not the mechanism. §3.3 labeled "confirms documented prefix-cache mechanics, pedagogical not novel"; cited RadixAttention/SGLang + vLLM-APC/PagedAttention; KVFlow as an accurate parenthetical. |

**Appendix (author-judgment) actions taken:** §1.8 80→**78**, §1.1 82→**80** (both jumped a full step on one-structure / one-leg evidence); §1.3 paper ref + mechanism **corrected** (geometric causal+residual, not softmax/RoPE; training does *not* mitigate — committed in `dc51a8a`); `results.md` slogan + cache-headline disclosures softened; lessons §0.15–§0.16 added (post-hoc affordance-control; verify reviewer-supplied citations).

**Net:** no finding blocked merge; the headline claims survived with two confidence trims and three citation/reframe fixes. Clear to merge.

## Key references (in-repo)

| Path | Role |
|---|---|
| `docs/phases/phase-1.0-plan.md` | Phase plan |
| `docs/phases/phase-1.0-exercise-B-plan.md` | Exercise B sub-plan + locked pre-registration |
| `docs/phases/phase-1.0-extension-plan.md` | Next-phase (DeepSeek + deep sweeps) plan |
| `experiments/phase-1.0/results.md` | Exercise A results |
| `experiments/phase-1.0/results-exercise-B.md` | Exercise B results |
| `src/stance/rot/` | rot evaluator (haystack / runner) |
| `src/stance/instrumentation/pricing.py` | exact cost model |
| `src/stance/context.py` | `with_cache_breakpoints` + token bookkeeping |
| `docs/synthesis.md` | concept stream (§1.1, §1.3, §1.8, §3.3, §3.6, §3.8, §5.2 updated) |
| `tasks/lessons.md` | process stream (§0.12–§0.14 added) |
