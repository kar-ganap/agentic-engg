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
| compaction + fresh-window (Ex2) | 1 | **COVERED** | 1.2 | `compaction.py` (TDD) + loop hook; §1.2 **ACTIVE 78** (behavioral confirm, Thread C); the *fresh-window* half → M7/8 memory (deferred) |
| SELF-ROUTE RAG-vs-LC (Ex3) | 1 | DEFERRED | 3.3 (M8) | clean, homed |
| tool-selection + namespacing (#2) | 2 | **COVERED** | 1.2 | §1.10 candidate **74** (reviewer-adjusted from 78); name>description weighting (reframed off 'failure'), verb-swap causal, cross-provider. Path to active: 2nd template/verb-pair |
| **held-out tool eval set** | 2 | **COVERED** | 2.1 | B4: 60 selection tasks, reserved seeds 101-110 disjoint from dev (1-5), deterministic first-tool DV; `stance.eval.heldout` + surface |
| return-a-reference (large payload) | 2 | PARTIAL | future | #6 tested small-id only — wrong scope; "handle=overhead" ≠ "ref doesn't help" |
| loop-guard / terminal-state *effect* (#7) | 2 | PARTIAL | future | mechanism built + unit-tested; B6 reliability report is the *sensor* (silent-loop / terminal-status / silent-wrong), but the current 55-run corpus is all-clean so there are no fires to measure yet |
| logit-masking over mutation (#1) | 2 | DEFERRED | future | stack-gated (needs a prefill smoke) |
| tool granularity (#5) | 2 | DEFERRED | future | flagged to drop |
| eval-driven tool-dev (agent rewrites descriptions) | 2 | **COVERED** | 2.1 | B5: free-rewrite recovers held-out selection, but the isolation shows it's attractor-demotion not correct-tool-improvement → STRENGTHENS §1.10; `ev-eval-driven-dev` recorded, nudge deferred to reviewer pass |
| **eval methodology** (det-vs-prob verifiers, trajectory eval, observability, judge-validation) | 6 | **PARTIAL** | **2.1** | B1 verifier-split (det+prob, deterministic-first gate, correctives) + B6 reliability report + B7 feedback-loop attribution DONE; B2 judge-validation harness built (labels pending → §1.9); B3 OTel/Langfuse pending Langfuse keys |

## Filed positions needing own-substrate evidence

| position | status | target | note |
|---|---|---|---|
| §1.2 keep-errors-in | **active (78)** | 1.2 | own-substrate; behaviorally confirmed cross-provider (Haiku strip + deepseek-chat) → active. Leads with the null (persist-redundant); remaining cap: engineered task structure |
| §1.4 recitation | literature-only (60) | future | cheap standalone (hypothesis §3.2) |
| §1.7 diversity | literature-only (50) | future | §3.5 three-arm; the compaction diversity_placebo touches it |
| §1.6 filesystem-as-context | tension §2.3 | 3.0/3.1 | Garry vs Manus — memory phases |

## [STALE] — deferred items whose target phase has passed with no re-defer

*(none — this ledger's creation clears the backlog. Re-check at every phase boundary.)*
