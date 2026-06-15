# Phase 1.1 — Tools (Module 2) — Retro

**Closed:** 2026-06-14 (experimental work concluded 2026-06-14)
**Branch:** `phase-1.1-tools` (based on post-PR#2 `main`)
**Critical phase boundary?** **YES** — three position commitments land here (#4 demoted/subsumed, #6→62, #3→78), and this close also absorbs the **deferred 1.0-ext three-reviewer pass** (the substrate decision §0.19). → three-reviewer pass required before merge.

## Summary

Phase 1.1 took Module 2 (tools) as the *spine's second vertebra*: build a real agentic tool-use harness (TDD), then use it to resolve three pre-registered tool-design positions. The harness landed first (domain/tools/loop/scorer/5 task tiers, `make check` green, 194 tests). The three positions then resolved — **and the three-reviewer pass at close materially corrected two of them**, overturning over-claims that rested on pilot-grade or read-tools-only data. *That is the headline process result of this phase: the critical-boundary review did its job, catching two over-confident positions before merge.* Post-review state:

- **#4 (multistep self-inflicted rot) — demoted; INCONCLUSIVE (not demonstrated).** Three independent attempts (chain sweep 55/55; binding A/B to 953k; the #4-v2 rescue-progression of five designs) **all failed to induce an agentic collapse at full seed-count** (0 mis-binds everywhere at N=12). A 5-seed pilot of the low-disc design showed a seed-4 lure-capture (active=passive), banked as "#4 ⊆ §1.8 demonstrated" — but the **method-rigor reviewer caught that it does not replicate at 12 seeds** (§0.21 sprung on the very claim that cites §0.21). So **#4 ⊆ §1.8 is a structural argument** (self-generation = accessibility advantage; fetching ≠ wall-retrieval), **not a demonstration**; #4(i) **60→15**, #4(ii) **parked**. The agentic-interference question is genuinely untested (→ RAG-vs-grep, later).
- **#6 (return-format: offer choice vs fix) — reframed.** The original "remove the choice; it's unexploited overhead" was **falsified by the reviewer pass**: per-tool data shows all three models (v4-flash/v4-pro/Sonnet) **do** use the choice, *sensibly* — `concise` on the terminal `send_message` (return unused), `detailed` on the consumed reads. The "detailed everywhere" tally only counted the read tools. What survives is the **fixed-arm ranking** (A inline-detailed 100% > D handle-block overhead > B concise-pruned 0%): **if you fix one format, fix it to inline-detailed** — *not* "don't offer a choice." **#6 45→48** (near equipoise: the success discriminator never fired *and* the behavioral pillar inverted).
- **#3 (carry-vs-swap tool-set break-even) — resolved via predict→verify; survived the pass (strongest of the four).** A break-even **exists** and is KV-cache-governed: carry-cost linear in superset size, swap-cost flat. Pre-registered N\* ≈ **5,111** tool-tokens (analytic cost model from the cache smoke); verified **6,461** on real DeepSeek (~26%; residual = actual S/C/k > nominal, raising both the swap floor +22% **and** the carry intercept +19% — the carry *slope*, the mechanism, matched to <0.1%). **Qualifies §1.1's cache leg.** **#3 70→78** (prior-art citations to add per the pass).
- **Carry-along (1.0-ext follow-on):** §1.8 length-extension confirmed **pillar B ("not length")** on one capable cross-family model (v4-pro) out to **~758k** (1.00@94k, 0.67@758k — *holds to ~94k, decays mildly by 758k*; "to ~1M" would overstate) → **§1.8 78→80**.

## Decisions made

| Decision | Choice | Why |
|---|---|---|
| #4 disposition | **demote 60→15; INCONCLUSIVE** | no agentic collapse induced across 3 attempts at full N; the pilot "demonstration" didn't replicate (reviewer pass); #4 ⊆ §1.8 is a structural argument only |
| #4(ii) | **park** | the fix-lever needs a value-*rendering* collapse to fix; none was induced |
| #4 instrument | **rescue-progression** (remove discriminability, not length) | exact-key has no S/N gradient; the way to *attempt* a collapse is to remove cue uniqueness — but even that didn't fire at N=12 |
| #6 disposition | **45→48; reframe (NOT "remove the choice")** | per-tool data: all 3 models use the choice sensibly (concise on unused terminal returns); surviving claim = fix-to-inline-detailed via the arm ranking |
| #6 evidence basis | **per-tool behavioral + fixed-arm ranking** | the aggregate token DV is call-count-confounded (ordering flips by model); the "detailed everywhere" read was read-tools-only |
| #3 method | **predict (B) then verify (A)** | derive the crossover analytically from the cache smoke, then confirm empirically — cheap, falsifiable; survived the pass |
| #3 disposition | **70→78, qualify §1.1 cache leg** | existence+cost-model cross-provider; location provider/TTL-dependent (Claude anchor deferred) |
| §1.8 | **78→80** (pillar B only) | length-leg holds to ~94k / mild decay by 758k on one capable cross-family model; diffuse-collapse generality (clause b) still open |
| Three-reviewer pass | **ran at this close** (1.1 positions + deferred 1.0-ext substrate) | **materially corrected #4 + #6**; #3/§1.8 survived with citation/phrasing fixes — see § Three-reviewer pass outcome |

## Validation gate

| Gate | Status |
|---|---|
| Evaluation criteria adjudicated | ⚠️ **controls that should HOLD held (high-disc/neutral); the positive controls designed to FIRE did NOT** (binding-passive mis-bind; diffuse-low collapse at full N) — so the immunity A/Bs are read as *null/too-easy*, not *passed*. Retractions adjudicated honestly (this is *why* #4 is inconclusive). |
| Tests / `make check` (ruff + mypy --strict + pytest) | ✅ green, 194 tests |
| Reproducibility | numbers regenerate from committed scripts + pinned seeds/prices; `results-{3,4v2,6}.md`; `runs/` gitignored (regen, per spend.md); spend logged |
| Pre-registration | all three positions had priors + retraction criteria locked 2026-06-10 (plan §"Confidences + retraction") |
| Retro written | this file (updated post-review) |
| `/learn` written | ✅ `tasks/lessons.md` (§0.20–0.24; close-out entry; [DELETE] considered) |
| Three-reviewer pass | ✅ ran — **materially corrected #4 (60→15) + #6 (62→48)**; #3/§1.8 survived with fixes (see § Three-reviewer pass outcome) |

## Three-reviewer pass outcome (the load-bearing event of the close)

Three clean-context Opus reviewers (method-rigor / framing-stress / prior-art). The author **verified every empirical finding firsthand against the committed run data** before acting. Net: the pass caught two over-claims that pilot-grade / partial-view evidence had let through.

- **[method-rigor, conf 90 — CONFIRMED] #4's "demonstration" was a pilot artifact.** The seed-4 lure-capture (the sole basis for "#4 ⊆ §1.8 demonstrated, active=passive") **does not replicate**: at 12 seeds, low-disc active *and* passive are both 12/12 correct-use, 0 mis-binds. → #4 reframed to INCONCLUSIVE / structural-argument; **60→15** (author-set: "lower below 25").
- **[method-rigor, conf 82 — CONFIRMED + extended] #6's "detailed everywhere" is false.** All three models go `concise` on `send_message` (v4-flash 10/15, Sonnet 3/3, v4-pro 2/3) and `detailed` on the reads — they *use* the choice sensibly. → #6 reframed (not "remove the choice"); **62→48** (author-set).
- **[framing-stress, conf 80] stale #6 number (60) in `contribution-candidates.md`** — reconcile to the committed number.
- **[prior-art, conf 90/88] uncited reference classes:** #3 sits in the dynamic-tool-loading + prompt-cache-economics literature; #4's "self-generation advantage" is adjacent to the cognitive-psych *generation effect*. Citations to add (verifying each ID firsthand — the background verifier was blocked on web permissions).
- **#3 (conf 78) and §1.8 (80) survived** — #3 with a residual-wording fix (slope matched to <0.1%; intercept also +19%, not "fully swap floor") and prior-art; §1.8 with phrasing tightening ("to ~94k / mild decay by 758k", n=1 cross-family).

## Concept-stream output (synthesis-anchored, post-review)

- **§1.1 — carry-vs-swap break-even added (conf 78).** Quantitative qualification of the cache leg: "don't mutate tools" is cheapest *while the tool universe is small*; past N\* (config-/TTL-dependent), swapping a minimal per-task set wins despite busting cache. Existence + cost model cross-provider; model-coherence leg untouched. (`results-3.md`.)
- **§1.8 — 78→80** (pillar B, one capable cross-family model to ~758k). Diffuse-collapse generality (clause b) **still open**. **#4 is a *failed-to-induce* probe here**, not a clean fold-in: it neither raises nor lowers §1.8 (the pilot collapse didn't replicate). (`results-length-extension.md`, `results-4v2.md`.)
- **§3.8 — unchanged (45).** Touched only tangentially.
- **Tool-design contribution candidates (pre-2.0), both reframed by the pass:** (a) *fix the return format to inline-detailed* — NOT "don't offer a choice" (the choice is used sensibly) (#6); (b) *self-generation is a structural accessibility advantage* — a structural argument, **inconclusive** empirically, ≈§1.8 (#4). Both in `tasks/contribution-candidates.md`.

## Method wins (process-stream, → `tasks/lessons.md`)

- **§0.20** — competitor *presence* ≠ *rivalry*; the chain null was "manipulation bit on volume, not same-frame rivalry."
- **§0.21** — a pilot validates the *rig*, not the *curve*; verify at full seed-count. **This phase is its sharpest case yet:** the #4-v2 "demonstration" was a 5-seed pilot collapse that the three-reviewer pass + full-N run dissolved — the same trap as the 2-seed §1.8 artifact, but it reached a *banked position* before the full run caught it. **The §0.21 gate must run BEFORE banking, not after.**
- **§0.22** — rescue-progression: corner an effect by removing escapes; for a self-generated needle, remove **discriminability** (not length). The method is sound, but its tempting tell ("the n-th design *collapses* — that's the finding") is **subject to §0.21**: design-5's collapse was a pilot artifact, so the real finding was "all five *held*." Remove-escapes is valid; reading the collapse needs full-N confirmation.
- **§0.23** — when the aggregate DV is confounded, lean on a confound-free **per-decision** signal — *but verify the per-decision read is complete* (#6's "detailed everywhere" was a read-tools-only slice; the full per-tool view inverted it). A behavioral signal is only confound-free if you look at *every* decision, not a subset.
- **§0.24 (new) — predict→verify (#3):** pin the mechanism with a smoke, pre-register an analytic prediction, verify empirically; the residual *is* the calibration audit (actual S/C/k > nominal raised both swap floor +22% and carry intercept +19%; the carry *slope* — the mechanism — matched to <0.1%).

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
