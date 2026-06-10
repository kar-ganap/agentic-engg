# Phase 1.1 (Module 2 — Tool Use & Function Calling) — Plan DRAFT / Pre-registration capture

> **STATUS: DRAFT, captured mid-reading** of Anthropic *Writing Effective Tools
> for AI Agents* (2026-06-09). This is the backpocket — accumulated position
> seeds + the eval-data-model menu — parked in one place so it survives context
> compaction. **Not the finalized plan.** To finalize at Phase 1.1 entry:
> the eval record schema (user-owned design decision), the exercise spec,
> per-position confidences + retraction criteria, TDD sequencing, and the
> three-reviewer-pass decision. Detailed planning happens *then*, not here
> (CLAUDE.md: "only plan the current phase in detail").

## Terminology (deliberately *not* the blog's)

The Anthropic blog says **"evaluation agent"** for the agent that exercises the
tools — but the field's dominant convention uses "evaluation agent / evaluator"
for the **judge** (the scorer), the opposite meaning. The category point: in
*tool* evaluation the **tools** are the object under test and the agent is just
the *instrument*. To avoid the collision we use:

- **tool-exercising agent** (a.k.a. **AUT**, agent-under-test) — runs tasks *using* the tools (the blog's "evaluation agent").
- **judge / verifier** — the expected-vs-actual scorer (code and/or LLM).
- **eval harness** — the framework around both.

We avoid bare "evaluation agent" entirely.

## Why this phase / bridges from Phase 1.0

Module 2 is where Phase 1.0's findings stop being curiosities and become
load-bearing:

- **KV-cache finding (§1.1/§3.3): tools are the cache root** (`tools → system →
  messages`; tool mutation = 7× cost, `results-exercise-B.md`). Module 2's
  "stable tool sets + logit-masking over mutation" (Manus) is the *design
  response* to exactly that measurement.
- **Context-rot finding (§1.8): diffuse competition collapses retrieval.**
  Resurfaces here as **multistep self-inflicted rot** — accumulated tool returns
  become the diffuse competitors (position #4 below).

**Framing (substrate discipline):** the deliverable is **defended positions** on
the tool-design debates, not just the curriculum's tool suite. The curriculum
exercise is the *instrument*; the positions are the *output*. Inherit the
questions from Anthropic/Manus — **not their confidence levels**.

## Pre-registered positions (backpocket — finalize confidence + retraction at entry)

1. **Masking-vs-swap envelope.** Logit-masking dominates tool-swapping for
   cache + correctness, *but only inside* {masking available on the stack, fixed
   superset, fits the window}. Outside that envelope, swapping / dynamic-loading
   wins. **Retraction:** a measured regime where masking loses on cost *inside*
   its claimed envelope. *(Availability is a **3-tier ladder** — corrected against
   Manus's actual infra, read firsthand 2026-06-09 (§0.16): **(i)** self-hosted
   (vLLM + logits processor) → arbitrary subset masking; **(ii)** hosted with a
   **prefillable text-format** tool call → tool-**group** masking via Manus's
   response-prefill + tool-name-prefix trick (`<tool_call>{"name":"browser_`),
   "without stateful logits processors"; **(iii)** hosted with only structured
   `tool_choice` (Anthropic; likely DeepSeek structured FC) → single-tool force /
   auto·any·none, NO group or subset masking. **Our substrate is tier iii**, so the
   gap is real but the cause is "no prefillable tool-call format," not "no raw
   logits." **Entry smoke-test:** does Anthropic/DeepSeek allow assistant-prefill
   into a *partial tool name*? Yes → tier ii unlocks, envelope widens; no → masking-
   vs-swap is *forced* on our stack.)*
2. **Masking ≠ selection quality.** Keeping all tool definitions in the prefix
   fixes *illegal* selection but not selection-*confusion* (the descriptions stay
   in view). **Falsifier:** pruning the visible set shows no selection-accuracy
   gain on the deliberate-overlap suite.
3. **Swap break-even is a ratio.** Swap-cost ÷ carry-cost = (downstream context
   invalidated) ÷ (tool-def bulk shed); it **crosses over task lifetime**
   (swapping cheap early/short, masking decisive late/long). **Measurable**
   directly on the Exercise B cache instrumentation.
4. **Multistep failure = self-inflicted context rot (the §1.8 bridge).** At
   depth, the dominant multistep failure mode is not the model's chaining
   capability but accumulated tool returns becoming diffuse competitors →
   return-shape (references vs. payloads) is a larger lever than per-tool
   description quality once chains exceed a few steps. **Falsifier:** pruning
   return *size* doesn't shift task success at depth, but rewriting descriptions
   does.
5. **Tool granularity is the upstream error-reduction lever.** How much
   computation is folded into each tool dominates *both* description quality (#2)
   and return-shape (#4), with a **reliability-vs-flexibility frontier** (too fine
   → orchestration burden + selection ambiguity; too coarse → inflexible /
   monolithic, can't recombine for novel tasks). The right cuts are *discovered
   from eval traces* (consolidate the multi-call workflows agents actually repeat),
   not designed up front. **Falsifier:** a coarse task-aligned toolset doesn't beat
   a fine-grained primitive one on the four error modes *at equal flexibility on
   held-out novel tasks*. *(Proposed but not yet explicitly ratified — flag to drop
   if not wanted.)*
6. **Removing the return-format choice beats handing it to the agent.** An
   agent-controlled `response_format` enum (concise/detailed) does **not** beat a
   *"concise prose + always-attached compact handle block"* return on the
   tokens-per-success frontier — because agents mis-predict downstream need often
   enough that under-request (wasted re-call) + over-request (token waste) exceeds
   the savings from selective verbosity. The blog's concise-vs-detailed framing
   can't see this third design (remove the choice; always include the handle
   cheaply). **Falsifier:** the agent-controlled enum Pareto-beats the always-attach
   design on success-vs-tokens; **or** the handle-block overhead is large enough
   that always-attach loses to a fixed arm.
   - **Experiment (4-arm; chaining tasks where step B needs step A's id, e.g.
     `search_user(name) → send_message(id)`):** A = always-detailed · B =
     always-concise · C = agent-controlled enum (the blog) · D = concise prose +
     always-attached compact handle block. **Metrics:** task success, total tokens,
     redundant-call rate, and (arm C only) **format-selection accuracy** (did it
     request `detailed` exactly when a downstream call needed the handle?).
   - **Mechanism sub-claim (also falsifiable):** C beats the fixed arms (A/B) only
     *above* a format-selection-accuracy threshold; below it a fixed strategy wins.
     Falsifier: C's advantage is flat w.r.t. selection accuracy.

**Synthesis hypothesis (UNTESTED — induce from #1/#5/#6, do *not* pre-register as
its own experiment).** #1 (masking=structure), #5 (granularity=structure), and #6
(always-attach=structure-removing-a-choice) are all instances of *prefer
deterministic structure over asking the non-deterministic agent*. The umbrella
claim — "structure steers more reliably than prompt-steering (instructions,
error-text nudges)" — is **near-obvious on its own** (decoration by the
rule-admission test) and **too broad to test cleanly**, so we let it *emerge* from
the three specific results in the report rather than running a separate experiment.
The sharper, non-obvious sub-claim worth watching (also untested): *prompt-steering
fails silently and input-distribution-dependently, whereas structural constraints
fail loudly or not at all → prompt-steering is more dangerous even at comparable
average reliability* (ties to §3.8 "dangerous failures don't throw"). Promote to a
numbered position only if a distinct experiment is later justified.

**Candidate micro-experiments (decide which are run vs. reading-only at entry):**
- Reasoning-first vs. response-first block ordering → tool-selection accuracy
  (the autoregression/CoT-ordering claim).
- Interleaved-thinking on/off → task success × total tokens × time-to-first-token
  (independent evidence positive but task-conditional; arXiv:2505.19640 is
  *trained* interleaving, distinct from the inference-time feature — don't
  transfer those numbers).
- **Description-refinement → tool-use success** (direction only). NOTE: the widely
  repeated **"40% faster from rewritten descriptions"** number is **NOT in the
  blog** — verified firsthand 2026-06-09 (§0.16). It is a fabricated/mis-attributed
  quote in our own `Agentic_Engineering_Curriculum.md:88`. The blog's *actual*
  claim is **qualitative**: refining descriptions → SOTA on SWE-bench Verified +
  "dramatically reducing error rates" (no number); agent-rewrites-tools is
  described but unquantified. So the experiment reproduces the **direction**
  (agent-rewritten descriptions improve tool-use success on the overlap suite),
  not a phantom 40%.

## Eval data model (design decision — USER OWNS the schema)

We have **no tool-use eval data model yet**. We do have the idiom to extend:
`TurnBudget`/`BudgetLogger` (append-only JSONL, **raw `usage` stored, cost
derived** from pinned prices, persistence-only) and the `Tool` abstraction
(`TOOLS` already a frozen tuple → Manus stable-toolset discipline encoded,
`tools.py:88`).

**Principle A — store raw events, derive every metric in scoring.** Don't persist
`accuracy=0.8`; persist a per-call event stream + a per-task summary of raw
fields, compute all derived metrics with a *re-pointable* scorer (lesson §0.7).
Mirrors what `TurnBudget` already does for cost. Keeps "numbers regenerate";
lets us add metric definitions later without re-running.

**Principle B — eval records map to `Evidence` on a `Position`, not a silo.** Each
eval run carries the **pre-registered position it tests** as a field, so its
metrics flow into the synthesis graph as Evidence (e.g., masking-vs-swap A/B →
Evidence on position #1). This is the anti-sandbox-pull discipline: an eval
artifact that doesn't feed the graph dies at Week 16.

**Shape (proposed, user to commit):** two append-only JSONL streams — a
**per-call event** and a **per-task summary** — raw fields only; resist a
heavyweight schema (Code Rules: simplicity first).

**Metrics menu** (blog baseline = ★; our additions diagnose the failure modes our
positions are about):

| Metric | Grain | Diagnoses |
|---|---|---|
| ★ accuracy (task success — record richly, not bool) | task | top-line |
| ★ runtime (per call & per task) | call/task | latency |
| ★ tool-call count | task | workflow / consolidation |
| ★ total tokens | task | cost |
| ★ tool errors | call | failure surface |
| wrong-tool rate + **confusion pairs** | call | selection failure under overlap (namespacing target) |
| right-tool-wrong-args | call | description-fix vs. param-doc-fix |
| **first-error depth + cascade flag** | task | compounding vs. cascade (#1/#2) |
| **context-growth trajectory + per-return payload size** | task | self-inflicted rot — the §1.8 lever (pos #4) |
| confidence / abstention / hedge of final answer | task | confident-wrong vs. abstain (committed/lenient, §3.8); reuse `HEDGE_MARKERS` |
| redundant-call count (duplicate (tool,args)) | task | soft-terminal-state → loops (loop-guard target) |
| recovery rate (success after an error/empty) | task | recovery vs. give-up |
| cache_read vs cache_creation across the loop | call | masking-vs-swap cost (pos #1/#3) |
| cost (usage × pinned price) | task | accuracy-vs-cost frontier |
| harvested feedback blocks (tagged to tool) | task | tool-improvement **leads** (behaviorally verified, not trusted) |

**Headline *derived* metric — efficiency, not raw accuracy.** Most positions
(esp. #4/#6) are judged on a cost-vs-capability tradeoff, so the comparison metric
is **tokens-per-success** (`total tokens ÷ #successes` — failures cost tokens, yield
none) as the regenerable/model-agnostic headline, and **dollars-per-success** (via
`pricing.cost`, which weights input/output/cache correctly) as the real one;
report on the **success-vs-cost frontier** (Pareto), since a great ratio at low
absolute success is worthless. Latency (TTFT, per-call runtime) is a separate axis,
not folded in. This is the cost-aware-accuracy framing (arXiv:2601.02663) — raw
accuracy in isolation is the thing to avoid.

## Environment discipline (carryover — the eval is part of the measurement)

- **Controlled sandbox to isolate mechanism + realism check to bound magnitude**
  (§0.13). Anthropic warns against superficial sandboxes; we also paid for the
  *other* end (confounded-realistic, broken-control) — need both.
- **Verify the control holds before interpreting the treatment** (§0.18): confirm
  the agent selects correctly on a no-overlap control before reading the
  deliberate-overlap treatment, else a low score = bad tools, not overlap biting.
- **Seeded, deterministic data with known answers** → verifiable responses (the
  prompt/response-pair structure: task + checkable end-state, graded by code
  and/or judge).

## Open gates / smoke tests (run before building the suite)

- **DeepSeek declared-tools smoke test** — does the Anthropic-compat endpoint
  handle *declared* tools cleanly, or leak DSML markup? Fall back to DeepSeek's
  native OpenAI-format client if it leaks (§0.17/§0.19). *This is the Module 2
  entry gate baked in from the Phase 1.0-ext finding.*
- Does DeepSeek carry reasoning across the tool loop (interleaved-thinking
  transfer)? Determines whether the interleaved-thinking micro-experiment is
  feasible on the primary substrate.
- **Partial-tool-name prefill test** (bears on position #1) — does Anthropic /
  DeepSeek allow assistant-prefill into a *partial tool name* (Manus's tier-ii
  group-masking trick), or are we tier-iii (structured `tool_choice` only)? Decides
  whether masking-vs-swap is *forced* on our stack.

## Substrate

Per §0.19 (DeepSeek-primary / Claude-anchor): tool use is **not** a Claude-only
feature → **DeepSeek v4-flash primary**, Claude spot-anchor — *after* the
declared-tools smoke test passes. (Prompt-caching mechanics, if we measure
masking-vs-swap cache cost directly, are Claude-anchored — Exercise B's caching
semantics are Anthropic-specific.)

## Finalized design decisions (locked 2026-06-10)

**Scope — Focused core.** Experiments: **#4** (multistep=rot) + **#6** (return-format
4-arm); **#3** (break-even) rides the same cache instrumentation. Masking (#1/#2)
**gated** on the partial-tool-name prefill smoke test (record swap-vs-stable+coarse
if tier-iii). **#5 (granularity) deferred** to a follow-up. Curriculum exercise is
the instrument.

**Domain — customer-support** (not pure sales-CRM): clean discrete entities
(users/orders/tickets → verifiable grading + #6 id-handles) **plus** naturally
large/messy **conversation transcripts** as the non-contrived large-output source
for the return-a-reference leg (#4). Decisive dims were gradeable-truth (§0.18
control must hold), native id-handle chaining (#6), and avoiding re-import of the
Phase 1.0 needle×structure confound (rules out research/docs).

**Overlap structure — a competition-density axis** (reuses §1.8's diffuse-competition
design on *tool selection* instead of retrieval → cross-modality replication):
- Density knob **N ∈ {0, 1, 3, 5}** confusable siblings (finer = dose-response).
- **Namespacing tier:** cross-entity (`search_users`/`search_accounts`/`search_tickets`)
  + sharp synonyms (`find_user`/`lookup_user`/`search_users`). Refactor = rename to
  `{entity}_search`, **descriptions held fixed** (§0.13 isolate names XOR descriptions).
- **Loop-guard tier:** broad `search(q)` catch-all **quarantined here** (scope overlap;
  namespacing can't fix it).
- **Control:** unique actions (`create_ticket`, `send_message`) = zero-competition (§0.18).
- §0.18 sweet-spot: synonyms must be *confusable but resolvable* (a discriminating
  signal exists) — else selection is a coin-flip and the control breaks.
- Realism check (§0.13): natural overlap (generic `search`+domain searches) vs.
  engineered synonyms degrade selection the same way?

**#4 task design — the §1.8 rot experiment ported to a self-generated trajectory**
(haystack = the agent's own accumulated tool returns; needle = an opaque id produced
early, needed late; competitors = similar ids in intervening returns). Three
**decoupled** axes (scoped cells, NOT full grid — §0.13):
- **depth** {2, 4, 8, 12} calls → compounding/cascade
- **absolute fill-at-use** {low ~5k, mid ~50k, high ~150k} → rot (THE axis that
  isolates volume from step-count → makes #4 falsifiable)
- **relative position** {0.1, 0.5, 0.9} of dependency-use → needle-depth analog,
  **decoupled** from fill (control total accumulated volume separately, à la Phase
  1.0 LENGTH×DEPTH; else position silently varies fill)
- **fraction-of-window kept LOW** for mechanism cells (§1.8: collapse is competition-
  driven, far below the limit) — proximity-to-limit is a *separate optional* axis
  (and a cross-model hazard: 200k Haiku vs 1M DeepSeek).
- DV: correct-use / wrong-id-confabulate / re-fetch-recovery / error (committed-lenient
  bracket transfers). Log **fill-at-use** (mechanism) vs **peak/total fill** (cost/#3)
  separately.
- Trajectory control: **task-structure-induced** (data-dependency graph forces
  depth+span; agent stays free) for the clean cell; **free-trajectory** for the
  realism leg.

## Run-config (locked 2026-06-10) — becomes a versioned `run_config.py` (#5)

**Control granularity:** **per-tier** — each tier's zero-point (selection N=0; #4
zero-competition+low-fill; #6 low-fill) is run and **must hold before its treatment
is read** (§0.18). Falls out of the axes' zero-points; near-free.

**#4 — anchor `A0 = {depth8, fill-mid~50k, pos0.9, comp-many, return-large}` + one-factor sweeps** (≈12 distinct cells; A0 shared):
- Fill {low~5k, mid, high~150k} @ depth8/pos.9/comp-many — **headline: rot vs compounding**
- Depth {2,4,8,12} @ **fill-low**/pos.9/comp-many — compounding baseline (also **#3** cache x-axis)
- Position {0.1,0.5,0.9} @ depth8/fill-mid/comp-many — needle-depth analog *(secondary)*
- Competition {0,few,many} @ depth8/fill-mid/pos.9 — §1.8 dose-response; **N=0 = control**
- Return-shape {large, reference} @ depth8/**fill-high**/pos.9/comp-many — return-a-reference

**#6 — 4 arms {A,B,C,D} × fill {low, high}, depth=2** = 8 cells. High-fill = discriminator (does D−C gap widen?). Id must be opaque & only-in-detailed (§0.18 sweet-spot).

**Selection** — density N∈{0,1,3,5} × {pre-, post-namespace} = 8 cells + 2 realism (engineered vs natural overlap @ N=3) = 10. Refactor varies **names only**, descriptions fixed (§0.13).

**Loop-guard** — {loop-guard on/off} × {terminal-state crisp/soft} = 4 cells.

**Seeds:** **5/cell throughout** (the 3-on-secondary cut rejected — false economy; under-powers curve shapes for ~$2).
**Fill control:** via injected customer-support **transcript** returns (diffuse competitors — other users' ids — live inside them). Targets are *fill-at-use*. **High capped at ~150k** so the Claude(Haiku-200k) spot-anchor runs without window-edge effects; fraction-of-window stays quarantined.
**Substrate:** DeepSeek v4-flash primary (post declared-tools smoke test) + 3–4 headline cells spot-anchored on Haiku/Sonnet.
**Scale/cost:** ≈170–180 DeepSeek runs + anchors ≈ **$12–15** (well under the $75 cap; we're at ~$39 reproducible).
**Deferred to v2:** description-refinement micro-experiment (2 cells, direction-only); §5 granularity (#5).

## Eval record schemas (v1)

### Per-call event (RAW, append-only; one row per loop turn) — locked 2026-06-10

Unit = **per-loop-turn** with an `is_tool_call` flag (complete trajectory incl. the
final-answer turn). Store **raw facts only**; everything evaluative is scorer-derived.
Big payloads (reasoning, response) stored as **hash/ref** to a side transcript
(recoverable via deterministic generation); only *sizes* inline.

- **Identity:** `run_id, cell_id, task_id, seed, model, turn_index, timestamp, is_tool_call`
- **Selection:** `tool_called` (null if not a call), `tool_expected` (null where undefined), `arguments`, `args_valid`
- **Reasoning/feedback:** `reasoning_ref`, `feedback_ref` (refs; nullable)
- **Response:** `response_ref`, `response_size_tokens`, `response_format` (#6: returned + requested-for-arm-C), `is_error`, `error_type`, `truncated`, `extracted_ids` (**comprehensive — ALL ids the call surfaced**, enables mis-bind∈pool vs. fabricate∉pool)
- **Accounting:** `usage {input, output, cache_creation, cache_read}`, `context_size_at_call` (fill-at-use), `latency_ms`
- **Loop:** `stop_reason` / `is_final`
- **NOT stored (scorer-derived):** wrong-tool, is_redundant, args_correct, cost_usd, cascade, first-error-depth, is_critical_step, the #4 DV classification, tokens-per-success
- **Reproducibility:** transcripts/competitor-ids generated deterministically from seed+config (ids unique, no needle↔competitor collision — Phase 1.0 collision-filter discipline); `response_ref` hash = integrity check; raw logs append-only.

### Per-task summary (DERIVED scorer artifact; one row per run = task×seed) — locked 2026-06-10

**It is the first *derived* layer, not a runtime log** — regenerable by re-running the
scorer over the raw events + run-record + task config (re-pointable evaluator §0.7;
#5 numbers regenerate). New metric idea later → re-derive, don't re-run.

**Raw companion the harness writes (robust to crash, in a finally-block) — the run
record:** `run_id, cell_id, task_id, seed, model, started, ended, terminal_status ∈
{complete, max_turns, crash, timeout}, final_answer_ref`. (Events alone can't capture
terminal_status — a crash skips the `is_final` turn.) So the **raw layer = per-call
events + this run record**; the **derived layer = the per-task summary** below.

Per-task summary fields (all derived; per-run scalars):
- **A. Identity & cell coords:** `run_id, task_id, cell_id, seed, model`; **intended IVs**
  (depth, fill-level, position, competition-N, return-mode, #6 arm, namespace-cond, tier);
  **achieved IVs** (`achieved_depth`=#tool-calls, `peak_fill`, `fill_at_use`,
  `competitors_surfaced`) — **bin by achieved**, not intended (free-trajectory).
- **B. Outcome:** `success`, `assertions_passed`, `final_answer_hedge` (committed/lenient).
- **C. #4 DV:** `critical_outcome` ∈ {correct-use, mis-bind (∈pool), fabricate (∉pool), re-fetch, error}.
- **D. Failure-shape:** `first_error_depth`, `cascade`, `redundant_call_count`, `recovered`.
- **E. Selection (selection-tier):** `wrong_tool_count`, `confusion_pairs`.
- **F. Cost/efficiency:** `total_tokens`, `total_output_tokens`, `total_cache_read`,
  `total_cache_creation` (#3), `total_cost_usd`, `peak_fill`, `sequential_round_trips`
  (= achieved_depth; the **reproducible latency proxy**). **`wall_clock_ms` dropped as a
  result-metric** — provider-infra noise, not cross-provider comparable, non-reproducible
  (violates #5); kept at most as operational metadata (hang-detection), never a comparison.
- **G. #6-specific:** `arm`, `format_selection_accuracy` (arm C), `handle_available`
  (did the format deliver the id?), `handle_used` (did the agent thread it?).

Field notes:
- **`peak_fill` vs `fill_at_use`:** peak = max context across the trajectory (cost +
  window-limit-proximity check); fill_at_use = context *at the critical step* (the #4
  mechanism quantity). peak ≥ fill_at_use.
- **`handle_available`/`handle_used`** decompose #6 — the **format's** job (availability)
  vs. the **agent's** job (use). The (available=true, used=false) outcome *undercuts D's
  premise*. Not redundant with #4's `critical_outcome` (format mechanism vs. competition
  mechanism; each is meaningless in the other's tier).
- **Latency** is reported via `sequential_round_trips` + `total_output_tokens`
  (reproducible, provider-comparable) — not wall-clock.

**Analysis layers (COMPUTED, not stored schemas):** event (raw) → task-summary (derived)
→ **cell aggregate** (one condition × 5 seeds → a rate = one point) → **sweep/curve/
frontier** (across cells along an axis → dose-response, success-vs-cost frontier). A
curve's *points* are cell-level; the *curve* spans a sweep. Rates/curves are generated
into `results.md` (Phase 1.0 precedent), not stored as records.

## To finalize at Phase 1.1 entry (decisions deferred — mostly user-owned)

- [x] Which positions get full experiments vs. stay reading-only. → **Focused core** (above).
- [x] Exercise spec — domain + overlap design. → **customer-support + competition-density** (above); held-out eval set still TBD.
- [ ] The two eval record schemas + the raw-field set (**user-owned**).
- [ ] Confidence (0–100) + retraction criterion per committed position (#4/#6/#3) (**user-owned**).
- [ ] Held-out tool eval set (curriculum requirement).
- [ ] TDD sequencing (failing tests first); `make check` gate.
- [ ] **Three-reviewer pass applies** — Phase 1.1 closes with position commitments → critical boundary.

## Out of scope (Phase 1.0-ext leftovers, headline only)

Structure-invariant needle redesign (§1.8 clause b), §3.8 affordance-control
test, §5 relatedness/density sweeps, `research_doc_stream`. These are context-rot
follow-ups, not Module 2.
