# Curriculum Coverage Ledger

> **Anti-lapse discipline (lessons §0.26).** A soft-deferred item that is *also* a filed/pre-registered
> position can lapse unnoticed — it happened three times (compaction, tool-selection, the Module-6
> eval mislabel) before the Module 0–2 fidelity audit (2026-07-27) caught it. This ledger tracks every
> curriculum exercise + filed-but-untested position with a **target phase**.
>
> **The rule:** when a `DEFERRED`/`GAP` item's target phase opens (or passes), it must be **run** or
> **explicitly re-deferred** (new target + reason). A deferred item whose target phase has *passed*
> with no re-defer is a **[STALE]** flag — check this ledger at every phase boundary (it's the
> short-horizon complement to the throughline-property gate).
>
> Statuses: **COVERED** (run, positioned) · **PARTIAL** (built/positioned but not fully measured) ·
> **DEFERRED** (not started, has a home) · **GAP** (contested debate or dependency neither positioned
> nor cleanly deferred — the dangerous kind).

## Curriculum exercises

| item | module | status | target | note |
|---|---|---|---|---|
| raw agent loop (~50 lines) | 0 | COVERED | 0.0 | `src/stance/loop.py` |
| workflow patterns (5) | 0 | PARTIAL (skim) | — | evaluator-optimizer ≈ reflection (done 2.0); orchestrator-worker → 2.4 |
| context-rot curve (Ex1) | 1 | COVERED | 1.0 | `rot/` + §1.8 — exceeded spec |
| KV-cache break/restore (Ex4) | 1 | COVERED | 1.0-ext | Exercise B; §1.1 / §3.3 |
| compaction + fresh-window (Ex2) | 1 | **COVERED** | 1.2 | `compaction.py` (TDD) + loop hook; §1.2 candidate 74; the *fresh-window* half → M7/8 memory (deferred) |
| SELF-ROUTE RAG-vs-LC (Ex3) | 1 | DEFERRED | 3.3 (M8) | clean, homed |
| tool-selection + namespacing (#2) | 2 | **COVERED** | 1.2 | §1.10 candidate **78**; lexical verb-capture (not count), cross-provider (DeepSeek+Haiku), verb-swap causal. Path to active: 2nd template/verb-pair |
| **held-out tool eval set** | 2 | **GAP** | **2.1** | curriculum-required; the eval-mislabel twin |
| return-a-reference (large payload) | 2 | PARTIAL | future | #6 tested small-id only — wrong scope; "handle=overhead" ≠ "ref doesn't help" |
| loop-guard / terminal-state *effect* (#7) | 2 | PARTIAL | future | mechanism built + unit-tested; effect unmeasured |
| logit-masking over mutation (#1) | 2 | DEFERRED | future | stack-gated (needs a prefill smoke) |
| tool granularity (#5) | 2 | DEFERRED | future | flagged to drop |
| eval-driven tool-dev (agent rewrites descriptions) | 2 | DEFERRED | 2.1 | → eval module |
| **eval methodology** (det-vs-prob verifiers, trajectory eval, observability, judge-validation) | 6 | **GAP** | **2.1** | the mislabel; our grader is all-probabilistic + unvalidated |

## Filed positions needing own-substrate evidence

| position | status | target | note |
|---|---|---|---|
| §1.2 keep-errors-in | **candidate (74)** | 1.2 | own-substrate (Haiku); conditional on ephemeral reasoning; verbatim>signal; persist-null cross-provider. To *active*: non-reasoning 2nd provider + downstream DV |
| §1.4 recitation | literature-only (60) | future | cheap standalone (hypothesis §3.2) |
| §1.7 diversity | literature-only (50) | future | §3.5 three-arm; the compaction diversity_placebo touches it |
| §1.6 filesystem-as-context | tension §2.3 | 3.0/3.1 | Garry vs Manus — memory phases |

## [STALE] — deferred items whose target phase has passed with no re-defer

*(none — this ledger's creation clears the backlog. Re-check at every phase boundary.)*
