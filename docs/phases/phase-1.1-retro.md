# Phase 1.1 — Tools (Module 2) — Retro

**Closed:** 2026-06-14 (experimental work concluded 2026-06-14)
**Branch:** `phase-1.1-tools` (based on post-PR#2 `main`)
**Critical phase boundary?** **YES** — three position commitments land here (#4 demoted/subsumed, #6→62, #3→78), and this close also absorbs the **deferred 1.0-ext three-reviewer pass** (the substrate decision §0.19). → three-reviewer pass required before merge.

## Summary

Phase 1.1 took Module 2 (tools) as the *spine's second vertebra*: build a real agentic tool-use harness (TDD), then use it to resolve three pre-registered tool-design positions. The harness landed first (domain/tools/loop/scorer/5 task tiers, `make check` green, 194 tests); the three positions then resolved **all in the direction of "the cautious instinct is right, but for a sharper reason than first stated."**

- **#4 (multistep self-inflicted rot) — demoted & subsumed.** Two clean nulls (chain sweep 55/55; binding A/B to 953k) said exact-key retrieval can't rot. The #4-v2 **rescue-progression** (five designs, each removing one escape) settled it: four high-discriminability designs held (0 mis-binds); the fifth (low-disc cue + same-type lures) collapsed — but **identically active vs passive**, i.e. the §1.8 identification failure acting provenance-blind. **#4 ⊆ §1.8**; #4(i) **60→25**, #4(ii) **parked** (untestable as posed). Self-generation is a *structural accessibility advantage* (fresh/recent/uniquely-labeled), not a new immunity — a near-tautology, not a separate mechanism.
- **#6 (return-format: offer choice vs fix) — resolved.** **Remove the choice; fix inline-detailed.** None of v4-flash/v4-pro/Sonnet spontaneously exploits an agent-set `response_format` choice (3 models, 2 families, ~7× span) — all default to `detailed` everywhere, even where `concise` is free. The choice is unexploited overhead; handle-block is pure overhead; concise-pruned breaks downstream. **#6 45→62.** Load-bearing evidence is **behavioral** (the token DV is call-count-confounded).
- **#3 (carry-vs-swap tool-set break-even) — resolved via predict→verify.** A break-even **exists** and is KV-cache-governed: carry-cost linear in superset size, swap-cost flat. Pre-registered N\* ≈ **5,111** tool-tokens (analytic cost model from the cache smoke); verified **6,461** on real DeepSeek (~26%; residual = swap floor +22% over nominal). **Qualifies §1.1's cache leg.** **#3 70→78.**
- **Carry-along (1.0-ext follow-on):** §1.8 length-extension confirmed **pillar B ("not length") cross-provider to ~1M** for capable models (v4-pro 1.00@94k, 0.67@758k) → **§1.8 78→80**. Rides this branch like the 1.1-prep rode the 1.0-ext branch.

## Decisions made

| Decision | Choice | Why |
|---|---|---|
| #4 disposition | **demote 60→25, subsume into §1.8** | rot is real but = §1.8 at the identification step; self-generation neither causes nor cures it |
| #4(ii) | **park** | the fix-lever needs a value-*rendering* collapse to fix; the only collapse was *identification* |
| #4 instrument | **rescue-progression** (remove discriminability, not length) | exact-key has no S/N gradient; the only way to induce a gradeable collapse is to remove the cue's uniqueness |
| #6 disposition | **45→62; remove the choice, fix inline-detailed** | choice unexploited across 3 models/2 families → overhead, not economy |
| #6 evidence basis | **behavioral (choice unexploited), not token totals** | token DV is call-count-confounded (ordering flips by model) |
| #3 method | **predict (B) then verify (A)** | derive the crossover analytically from the cache smoke, then confirm empirically — cheap, falsifiable |
| #3 disposition | **70→78, qualify §1.1 cache leg** | existence+cost-model cross-provider; location provider/TTL-dependent (Claude anchor deferred) |
| §1.8 | **78→80** (pillar B only) | length-leg cross-provider to ~1M; diffuse-collapse generality (clause b) still open |
| Three-reviewer pass | **run at this close** (covers 1.1 positions + deferred 1.0-ext substrate) | critical boundary = position commitments + framework adoption |

## Validation gate

| Gate | Status |
|---|---|
| All evaluation criteria met (controls fired/held; retractions adjudicated) | ✅ |
| Tests / `make check` (ruff + mypy --strict + pytest) | ✅ green, 194 tests |
| Reproducibility | numbers regenerate from committed scripts + pinned seeds/prices; `results-{3,4v2,6}.md`; `runs/` gitignored (regen, per spend.md); spend logged |
| Pre-registration | all three positions had priors + retraction criteria locked 2026-06-10 (plan §"Confidences + retraction") |
| Retro written | this file |
| `/learn` written | ⬜ next (append to `tasks/lessons.md`; §0.20–0.23 already filed in-flight) |
| Three-reviewer pass | ⬜ next (pre-merge; scope below) |

## Concept-stream output (synthesis-anchored)

- **§1.1 — carry-vs-swap break-even added (conf 78).** Quantitative qualification of the cache leg: "don't mutate tools" is cheapest *while the tool universe is small*; past N\* (config-/TTL-dependent), swapping a minimal per-task set wins despite busting cache. Existence + cost model cross-provider; the model-coherence leg is untouched. (`results-3.md`.)
- **§1.8 — 78→80** (pillar B cross-provider to ~1M). Diffuse-collapse generality (clause b) **still open** — unchanged by this phase. **#4 folds in here**: agentic self-generation does not escape it (provenance-blind). (`results-length-extension.md`, `results-4v2.md`.)
- **§3.8 — unchanged (45).** Touched only tangentially (abstention seen under length-stress in the length-extension; still confounded/caveated).
- **New tool-design positions (candidate, pre-2.0):** (a) *fix the return format, don't offer a choice* (#6); (b) *self-generation is an accessibility advantage, not an immunity* (#4, ≈§1.8). Both filed to `tasks/contribution-candidates.md`.

## Method wins (process-stream, → `tasks/lessons.md`)

- **§0.20** — competitor *presence* ≠ *rivalry*; the chain null was "manipulation bit on volume, not same-frame rivalry."
- **§0.21** — a pilot validates the *rig*, not the *curve*; verify the control at full seed-count (the 2-seed §1.8 artifact).
- **§0.22** — rescue-progression: corner an effect by removing escapes; for a self-generated needle, remove **discriminability** (not length) to test interference. (The load-bearing instrument of the whole phase.)
- **§0.23** — when the aggregate DV is confounded, lean on a confound-free **per-decision** signal (#6 behavioral finding).
- **predict→verify (#3)** — a cheap, falsifiable pattern worth promoting to a reusable method: pin the mechanism with a smoke, derive the prediction analytically (pre-register), verify empirically; the residual *is* the calibration audit (swap floor +22% explained the 26% miss).

## Friction (where discipline slipped / cost time)

- **Loop-guard idempotency assumption** — the duplicate-signature guard killed the recency tier (stateful `apply_adjustment` with identical args). Fixed (`loop_guard=False`), logged as a harness insight.
- **Gradeable/luring tradeoff** — sharper cues make the task gradeable but kill the lure (0/48 collapse); luring cues can't be cleanly graded. This is *why* #4(ii) parked and why a gradeable agentic collapse needs §1.8's unique-answer needle ported (the RAG-vs-grep frame, later).
- **Nominal-vs-actual token calibration (#3)** — the filler wasn't token-calibrated; first cross-N runs were cache-contaminated (shared prefix). Two clean re-runs needed (nonce-salting + actual-token recovery). The discipline (verify on real API, don't trust nominal) caught it.
- **Stale session-start git snapshot** — briefly mis-read the branch state; cost a detour. Resolved (branch was already correctly based on post-PR#2 main).

## Throughline property progress

- **No throughline *surface* advanced** — expected at Stage 1 (surfaces begin Stage 2); flagged per the gate, not a concern.
- **Property 3 (re-evaluation) exercised in spirit** — three positions re-evaluated against fresh evidence and **moved** (one demoted, two sharpened) rather than drifting; the anti-drift discipline (pre-registered retraction criteria) did real work — #4(i)'s retraction *fired* and was honored.
- **Property 4 (contribution)** — two new tool-design candidates filed; the rescue-progression instrument + the predict→verify pattern are reusable methodological assets.
- **Flag:** two consecutive concept-heavy phases (1.0-ext, 1.1) with **zero surface progress**. Acceptable at Stage 1, but Stage 2's first phase must move a surface or the sandbox-pull falsification test starts to bite.

## Carry-forward

- **#3 Claude anchor** — verify the crossover *location* moves as the cost model predicts under Anthropic's 10× discount / 5-min TTL (the 8-pt residual on #3=78 prices exactly this gap).
- **§1.8 clause (b)** — still open (structure-invariant needle); **the agentic re-visit is the RAG-vs-grep debate** (does tool-retrieval beat in-context disambiguation under diffuse competition?), using §1.8's unique-answer needle ported to the agentic frame — the only way to a gradeable collapse *rate*.
- **#4(ii) revival** — only with a return-shape-domain (value-rendering) collapse.
- **#6 economy-pressure probe** — does an explicit "use concise unless you need the ids" prompt make the choice *usable* (vs merely un-used-by-default)?
- **Three-reviewer pass scope** — covers the 1.1 position commitments **and** the deferred 1.0-ext substrate decision (§0.19). Prior-art set must include arXiv:2506.08184 (proactive interference) + RULER + the WM/τ-bench refs logged in the plan; read firsthand before the synthesis commits anything (§0.16).
