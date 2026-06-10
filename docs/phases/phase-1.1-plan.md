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

## To finalize at Phase 1.1 entry (decisions deferred — mostly user-owned)

- [ ] The two eval record schemas + the raw-field set (**user-owned**).
- [ ] Which positions get full experiments vs. stay reading-only.
- [ ] Confidence (0–100) + retraction criterion per committed position.
- [ ] Exercise spec: tool-suite domain, # tools (curriculum: 10–15), overlap design, held-out eval set.
- [ ] TDD sequencing (failing tests first); `make check` gate.
- [ ] **Three-reviewer pass applies** — Phase 1.1 closes with position commitments → critical boundary.

## Out of scope (Phase 1.0-ext leftovers, headline only)

Structure-invariant needle redesign (§1.8 clause b), §3.8 affordance-control
test, §5 relatedness/density sweeps, `research_doc_stream`. These are context-rot
follow-ups, not Module 2.
