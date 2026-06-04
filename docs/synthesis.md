# Synthesis — Concept Stream

> Long-form draft for the substrate's concept stream. Holds candidate `Position` records, open tensions between sources, testable hypotheses, and reading notes per primary source. See `CLAUDE.md` § Two-Stream Discipline.
>
> **Migration path:** when the evidence-graph schema lands in Phase 2.0, structured `Claim` / `Evidence` / `Position` records migrate from §1 here into the graph. This file persists as the long-form prose layer that the eventual capstone synthesis report grows from. Until the schema exists, §1 is the holding pen.
>
> **Position record format** (per CLAUDE.md § Substrate Discipline):
> - **Stance** — the position itself
> - **Confidence** (0–100) — mandatory; point stances without uncertainty are insufficient
> - **Supporting evidence** — literature + experiment where feasible
> - **Retraction criterion** — what evidence would change my mind
> - **Status** — candidate / active / demoted (with reason)
> - **Date registered** — when it entered the graph
>
> All §1 entries are currently `candidate` status; we don't yet have the discipline of pre-registration since the schema isn't built.

---

## §0 — Scope and current focus

- **Current phase:** Phase 1.0 (Module 1, Context Engineering) — reading done; **Exercise A (context-rot) experiments complete** (`experiments/phase-1.0/results.md`, 2026-06-04). Exercise B (KV-cache) and the phase-close ritual pending.
- **Sources read:** Manus *Context Engineering: Lessons from Building Manus* (Ji, July 2025); Anthropic *Effective Context Engineering for AI Agents* (Sept 2025); Chroma *Context Rot* (Hong/Troynikov/Huber); arXiv:2603.10123 *Lost in the Middle at Birth* (Mar 2026).
- **Focus area for positions this phase:** how context is structured, sized, and shaped; what's stable vs. mutable; how to instrument and defend KV-cache hit rate.

---

## §1 — Active candidate positions

### §1.1 — Tool definitions should be stable across a run (no mid-loop mutation)

**Stance:** For Anthropic-API-served agents, the `tools=[]` parameter and its tool definitions should be set once at run start and not mutated mid-loop. State-dependent tool availability should be handled in the most-recent user message (and via `tool_choice` where the API supports forcing/restricting), not via mutating `tools` or `system`.

**Confidence:** 75.

**Preconditions (where this position is meant to apply):**
- **Pivot:** Inference uses KV-cache (Anthropic API, vLLM with caching, etc.) AND agent operates over ≥3 multi-turn iterations with shared prefix.
- **Cache economics matter:** Total run is long enough that cached-token discount exceeds the marginal cost of stable-prefix discipline (typically ~10+ turns at meaningful token volume).
- **History preservation:** Loop preserves full history; if compaction routinely strips old turns including stale tool_use references, the model-coherence argument weakens.
- **Provider scope:** Anthropic-served Sonnet/Opus/Haiku family. Other providers (OpenAI, open-weight models, future Anthropic versions) may have different cache mechanics or train models more robust to stale tool refs.

**Supporting evidence:**
- Literature: Manus, *Context Engineering: Lessons from Building Manus* (July 2025) — both KV-cache and model-confusion arguments.
- Mechanistic: tool block sits at the front of the prefix; mutating it invalidates everything after. Stale tool_use references in history can confuse the model when current tools list disagrees.

**What evidence would update this (and by how much):**
- **Down 20–30 (toward retraction):** Controlled measurement on Anthropic showing lexically-changing tools mid-run produces no measurable cache-hit-rate degradation AND no model-coherence degradation; OR Anthropic exposes state-conditioned tool masking as a first-class API feature.
- **Down 5–10 (soften scope):** Evidence that the coherence problem is much smaller than the cache problem — would suggest caring about tool mutation for cache reasons only, with weaker normative force on smaller deployments.
- **Up 5–10:** Empirical demonstration of severe coherence breakdown (hallucinated tool names, repeated failed calls referring to removed tools) under mid-loop mutation.
- **Conditionally generalizes only to:** Anthropic-served multi-turn agents with full history retention. Other providers / single-turn agents / heavily-compacted agents need fresh experiments.

**Mechanism data to capture in any experiment:**
- Per-turn cache-hit rate (Anthropic surfaces cached input tokens in `usage`).
- Per-turn input cost broken down by cached/uncached.
- Model behavior when stale tool references exist: does it try to call removed tools? hallucinate new names? successfully ignore?
- Rate of tool-name validation errors under different mutation patterns.

**Status:** candidate (pre-2.0). Registered 2026-06-01. Preconditions added 2026-06-01.

---

### §1.2 — Failures are high-signal tokens; compaction should preserve them

**Stance:** Failure events in agent trajectories (tool errors, model refusals, malformed outputs) carry high information density per token. Compaction strategies should *preserve* failure events (or treat them as priority preservation candidates) and *condense* successful intermediate work — not the reverse. The standard "summarize old history into a paragraph" pattern is an anti-pattern when applied uniformly to failures.

**Confidence:** 65.

**Preconditions (where this position is meant to apply):**
- **Pivot:** Multi-turn agent loops AND failure events actually occur in the workflow (if everything succeeds first try, the claim is vacuous).
- **Model class:** Frontier-class models trained for in-context behavioral adaptation (RLHF + instruction-tuned). Doesn't transfer to weaker models that don't update behavior from in-context feedback.
- **Failure quality:** Error messages are structured/informative enough for the model to extract a behavioral signal ("rate limit exceeded, retry after 60s" works; bare "Error" does not).
- **Context pressure:** Compaction is actually in play or imminent — if context never gets pressured, "preserve vs. summarize" never arises.
- **Failure rate:** Non-trivial but non-dominant — roughly 1-in-20 to 1-in-3 turns. Extremely rare → vacuous. Dominant → context rot eats the signal value.

**Supporting evidence:**
- Literature: Manus, *"keep the wrong stuff in"* pattern (July 2025).
- Mechanistic: model performs in-context Bayesian-like update from failure → action distribution shift; discarding the failure discards the supervision signal.
- Analogous patterns: incident post-mortems, test failure reports, medical case notes — all preserve failure events at high fidelity while compressing routine successful operations.

**What evidence would update this (and by how much):**
- **Down 20–30 (toward retraction):** Empirical demonstration that failure-preserving compaction does NOT improve goal adherence vs. failure-summarizing compaction on multiple representative task suites, AFTER controlling for failure rate and error-message quality.
- **Down 5–10 (soften scope):** Evidence that *summarized-but-flagged* failures (e.g., "5 retries on search failed with rate limits — try alternative tools") work equally well as verbatim preservation. Would shift the position to "preserve the SIGNAL, not necessarily the FORMAT" — a more efficient version of the same claim.
- **Up 5–10:** Empirical demonstration in our own setup that failure-preserving compaction significantly outperforms (≥10% goal-adherence delta) failure-summarizing on a failure-prone task suite.
- **Conditionally generalizes only to:** multi-turn agents on frontier-class models with non-trivial-but-non-dominant failure rates AND structured error messages AND context pressure forcing compaction. Doesn't transfer to single-shot agents, near-zero-failure setups, weaker models, or pipelines where failures are unstructured noise.

**Mechanism data to capture in any experiment:**
- Per-failure type: what failure happened; was it preserved in some form; was it referenced (explicitly or implicitly) in subsequent decisions.
- Recurrence rate: how often the same failure mode repeats with vs. without preservation.
- Token cost: how much context budget is consumed by preserved failures vs. summarized vs. dropped.
- Goal-adherence metric: external task-completion judgment (LLM-as-judge rubric or deterministic check).
- First-try success rate after a preserved failure vs. blind retry.
- Model behavior signals: does the reasoning text reference prior failures? (Qualitative tag.)

**Related tension:** See §2.1 (Manus vs. Chroma — failure-keeping vs. context rot). The resolution sketch there — that signal density matters, not just token count — is load-bearing for the normative force of this position.

**Confound with §1.7:** keeping an error in is *also* a diversity injection (it breaks the uniform-success pattern), so a naive "keep errors in" test cannot separate this position's informational value from §1.7's pattern-break value. The three-arm design in §3.5 disentangles them. Both are instances of the §5.1 "context as in-context training set" framing (errors = hard negatives).

**Tool-result clearing (Anthropic corroboration + §1.2 refinement):** Anthropic recommends tool-result clearing as "the safest, lightest-touch compaction" — once a tool is called deep in history, the raw result is spent. This corroborates §1.2's "condense successes." **But §1.2 refines the blanket version:** clear spent *successes* (pure distractors, §5.2); preserve a compact *failure* signal (the corrective lesson). Tension with Anthropic's default framing ("why would the agent need the raw result again?") — for a *failure*, per §1.2, it might. Reconciled by §1.2's down-5–10 softened form: clear the raw payload, keep a failure summary. Tested in §3.7.

**Status:** candidate (pre-2.0); directly testable in Phase 1.0 exercise 2 (compaction). Registered 2026-06-01. Preconditions added 2026-06-01.

---

### §1.3 — Active-attention curve in long contexts is asymmetric (J-shape, not symmetric U)

**Stance:** The "lost in the middle" U-shape (Liu et al. 2023) describes *retrieval accuracy* by needle position. For **active reasoning influence** — how strongly content at a position shapes the current decision — in long agent loops (≥30K tokens accumulated, multi-turn), the curve is better modeled as a J: beginning has medium-low active influence (attention diluted by length; mediated through downstream representations), middle is lowest, end is highest. Recency dominates beginning for current-step decision-making, even though both are "high attention" in the U-shape retrieval sense. Recitation works by moving goal content into the high-end of the J.

**Confidence:** 55. (Lowered from 60 on refinement: synthesized model aggregating several real phenomena, with a non-trivial measurement-validity risk — see below.)

**Preconditions (where this position is meant to apply):**
- **Pivot:** Context long enough for positional effects to exist (≥~20K tokens, multi-turn accumulation). At short context the distinction is moot.
- **Measured quantity:** The claim is specifically about *active reasoning influence* (effect on the current decision), NOT retrievability (can the model answer a question about it if asked). The two diverge; conflating them voids the claim.
- **Regime:** Long-horizon agent loops with accumulated history between the anchor (goal/plan) and the current decision point — not single-shot QA.
- **Model scope:** Frontier autoregressive transformers as of 2026. Architectural changes (explicit memory mechanisms, non-uniform positional schemes) could change the curve.

**Supporting evidence:**
- Literature: Liu et al. (2023) U-shape for *retrieval*; Chroma context-rot (general length-related degradation); Manus recitation pattern (production validation of recency-foregrounding as a fix).
- Mechanistic: attention is the mechanism by which past content shapes current output; weak attention → weak active influence; mediated influence (anchor → intermediate response → current) degrades through chains of representations.
- Analogous: serial-position effects in human free recall skew toward recency.

**Note — Chroma (and NIAH generally) is a *lower bound* on this position:** needle-in-a-haystack benchmarks measure *retrievability* (can the model find a needle when asked) — the **easier** quantity that §1.3 explicitly distinguishes from *active influence* (does distant content shape the current decision unprompted). Since active influence is the harder operation, retrieval-degradation results are a lower bound: if retrievability already degrades with length/noise, active influence plausibly degrades *at least as much*. So Chroma corroborates the *direction* of §1.3 without overstating it — if anything it understates the agentic problem. (Application of the contrived±asymmetry, `tasks/lessons.md` §0.8: a contrived negative on the *easier* quantity → robust lower bound on the harder one.)

**Note — Chroma found NO position effect for NIAH retrieval (sharpens, doesn't refute):** across 11 needle positions Chroma reports "no notable variation in performance" for the NIAH retrieval task; repeated-words shows a *primacy* effect (best near the beginning); Liu et al. (2023) found a U for multi-doc QA. So position-effects are **task-dependent**, not universal — which (a) sharpens §1.3's preconditions (the J/U shape is regime-specific) and (b) *supports* the retrievability-vs-active-influence distinction: retrieval shows no position effect here, so if a position effect appears it's in the harder active-influence quantity, exactly as §1.3 claims. Does not move §1.3's confidence (Chroma measures the wrong quantity for it) but validates the framing's central distinction.

**Note — candidate *architectural* mechanism for position bias (Lost in the Middle at Birth, arXiv:2603.10123, Mar 2026; primary source read 2026-06-04, §4 entry):** the paper reports a **U-shaped Jacobian-norm *sensitivity*** (how much the output moves with a token's *position*, content fixed) present at **initialization** (random weights), attributed to causal masking + positional encoding (RoPE) + softmax + depth; training is reported to **mitigate** it (not "never erase" — that was an inflated secondhand summary we corrected by reading the source). **Three reasons to hold this loosely for §1.3, not promote it:** (i) it measures *sensitivity*, not *accuracy* — the paper itself flags Jacobian norm as "one lens; task performance may not fully reflect it," which is exactly §1.3's sensitivity≠active-influence≠retrievability distinction; (ii) "training mitigates" reconciles cleanly with Chroma's task-dependence (no universal accuracy-U) — *against* any immutable-blind-spot reading; (iii) it's not testable on our Anthropic-API behavioral setup (needs open-weights interpretability tooling — same regime as the §1.3-v2 open problem). **Net for §1.3:** a primary-source-grounded *reason the shape is regime-specific* (architectural sensitivity bias at birth, modulated by training → task/model-dependent observed curves). Strengthens the "regime-specific shape" precondition; does **not** license a universal accuracy-U; does not move confidence (wrong quantity + untestable here). Attribution detail is via a fast-model PDF summary — verify the actual sections before citing the softmax/depth decomposition precisely.

**What evidence would update this (and by how much):**
- **Down 20–30 (toward retraction):** Controlled measurement on long-context agent loops showing beginning-position content drives current decisions *as strongly as* end-position content (collapsing J back to symmetric U for the active-influence quantity).
- **Down 10–15 (measurement-invalidity):** If "active reasoning influence" cannot be operationalized distinctly from retrievability — every measurement we design actually measures retrievability — the position is unfalsifiable as stated and must be reformulated or demoted.
- **Down 5 (magnitude-too-small):** Asymmetry confirmed but so small it has no design consequence (recitation/positioning don't measurably help).
- **Up 5–10:** Direct measurement (ablation of identical content at beginning vs. end of a long context, measuring decision change not recall) confirms end > beginning for active influence on our models.
- **Conditionally generalizes only to:** frontier autoregressive transformers, long-context multi-turn regime, active-influence quantity. Does not transfer to short contexts, retrieval-style tasks, or future architectures with explicit memory.

**Mechanism / experiment design:**

*The core methodological challenge is operationalizing "active influence" vs. retrievability.* The design must deliberately construct a situation where the two can give different answers — if they always move together, the position is unmeasurable as stated (triggers the down-10–15 update).

**v1 design (runnable now):** Bury a **default-opposing, deterministically-checkable directive** at varying positions in a fixed-length long context.
- *Setup:* place a directive whose compliance is mechanically checkable (e.g., "every Python function must use single-quote strings only") at beginning / middle / end of a fixed-length context. Then give an end-task that requires the behavior but does NOT mention the directive ("write a config parser").
- *Active-influence probe:* does the produced output spontaneously comply? (deterministic check — no LLM judge in the core loop).
- *Retrievability probe (separate run, same position):* after the same context, ask "what formatting rules did I give you?" — does it recall?
- *Critical control — measure lift, not absolute:* first establish the base rate of the behavior with no directive; choose a directive that OPPOSES the default so any compliance is attributable to the directive. Active influence = compliance − base rate.
- *Signature:* retrievability roughly flat across positions BUT active compliance high-at-end / low-at-middle / medium-at-beginning ⇒ confirms the J-shaped dissociation. Active compliance ≈ retrievability everywhere ⇒ refutes (measurement-invalidity). Active compliance equal at beginning and end ⇒ refutes the J specifically (symmetric U).

**Threats to validity (pre-register):**
1. Single-directive idiosyncrasy → use a *set* of directives (quotes, indentation, naming, banned-import, output-format); effect must replicate across them.
2. Task-difficulty confound → end-task identical across position conditions; only the directive's position moves.
3. Priming leakage → run active-influence and retrievability probes as *separate* conversations, never sequentially.
4. Length confound → run at multiple context lengths; the J should flatten toward uniform at short lengths (confirms the length precondition).
5. Recency-of-task artifact → task is always at the end (always "recent"); we vary the *directive's* position, holding task position constant.

**v2 (open methodological problem — NOT a runnable plan):** separating *direct* positional influence (turn N attends back to position 1) from *mediated* influence (position 1 shaped an intermediate turn that is now recent, so turn N inherits it secondhand). The obvious design — compare inert-filler vs. real-work intervening content at matched token-distance — has a **known, unresolved confound**: the two arms differ in more than mediation (natural re-invocation of the directive by real work; attention competition; semantic relatedness), so the clean subtraction is contaminated. Candidate fixes (directive-neutral intervening work; activation-patching via interpretability tooling on open-weights models) are each either insufficient or out of scope for our Anthropic-API behavioral setup. **Recorded as an open problem, not a design.** Note: a clear v1 result may obviate v2 entirely — if the dissociation is strong, recitation (§1.4) is justified without decomposing the mediation share. Do not pay the v2 cost speculatively.

**Relationship to other entries:** Load-bearing for §1.4 (recitation) — the recency factor of recitation *is* moving content into the high-end of this J. If §1.3 collapses to a symmetric U, §1.4 weakens on that factor but survives via its content-richness and role-attribution factors (independent of positioning). See §1.4's revised three-factor mechanism.

**Status:** candidate (pre-2.0). Registered 2026-06-01. Preconditions + experiment design added 2026-06-01. Confidence lowered 60→55 on refinement (measurement-validity risk surfaced).

---

### §1.4 — Recitation is a context-engineering primitive, not UX

**Stance:** For long agent loops (~20+ turns or 30K+ tokens accumulated), explicit periodic re-emission of the goal/plan via an agent-rewritten artifact (e.g., `todo.md`) measurably reduces goal drift, and the token cost is paid back. Treat it as a first-class context-engineering technique, not a UI flourish.

**Confidence:** 60.

**Mechanism (revised 2026-06-01 — three token-mediated factors, NOT a distinct "act of reconciliation"):**
Recitation's benefit decomposes into three factors, all mediated by tokens in context:
1. **Content richness** — the rewritten artifact encodes a *computed progress state* (done / pending / next / blocked) that the bare original goal lacks.
2. **Recency** — that richer content sits in recent, high-active-influence positions (the §1.3 mechanism).
3. **Self-authored role attribution** — the artifact is an `assistant`-role message, and the model is trained (RLHF / instruction-tuning on chat format) to treat its own prior assistant content as commitments to stay consistent with.

**Mechanistically retired:** an earlier draft posited a distinct "reconciliation" mechanism — that the *act* of the agent generating the synthesis does something beyond the result. This does not survive contact with statelessness: a transformer at inference has no memory of having generated anything; each forward pass sees only the token sequence, and the KV cache is provenance-blind (prefix caching across the generate/inject boundary proves this). If the synthesis text and its role marker are held identical, self-generated vs. externally-injected are **indistinguishable** to the model. The practical value of having the agent self-reconcile is simply that it guarantees a high-quality, full-context progress synthesis lands in context — not a separate cognitive act.

**Preconditions (where this position is meant to apply):**
- **Pivot:** Long-horizon multi-turn task where drift actually occurs (~20+ turns, or any length where unaided goal adherence measurably degrades).
- **Drift exists to fix:** If the model maintains goal adherence without recitation on the task class, the technique is moot.
- **Affordability:** Token cost of periodic re-emission is acceptable relative to task value. (Cache stays intact — recitation is an append, paying uncached cost only for the new tokens.)
- **Stable re-emission:** The model can re-emit the goal without corrupting it (see telephone-game sub-hypothesis below).

**Supporting evidence:**
- Literature: Manus (production claim; no published quantification).
- Mechanistic: content + recency (§1.3) + role-conditioned treatment, all token-mediated.
- Analogous: human practice (restating the question, standups, spaced repetition).

**What evidence would update this (and by how much):**
- **Down 20–30 (toward retraction):** Controlled experiment showing no measurable goal-adherence delta from recitation on a representative long-horizon task, across cadences.
- **Down 10 (cost-exceeds-benefit):** Adherence improves but token cost outweighs the gain at realistic task lengths/prices.
- **Down 5–10 (mechanism-scope):** Benefit shown to come entirely from content-richness, with no recency or role component — would narrow the mechanistic claim and decouple from §1.3.
- **Up 10 (telephone-game absent + clear benefit):** Adherence improves measurably AND re-emission doesn't introduce goal corruption over many cycles.
- **Conditionally generalizes only to:** long-horizon multi-turn agents on tasks where unaided drift occurs. Does not transfer to short tasks or tasks the model already holds without aid.

**Mechanism data to capture in any experiment:**
- **Cadence sweep:** every turn / every 5 / every 10 / never. Goal-adherence metric × token cost at each. (= hypothesis §3.2.)
- **Factor isolation (two clean comparisons):**
  - *Content-richness:* re-append the bare original goal (recent) vs. re-append a progress-annotated synthesis (recent). Isolates factor 1.
  - *Role attribution:* inject the *same* synthesis as an `assistant`-role message vs. a `user`-role message. Isolates factor 3. (Same-content, same-role, self-generated-vs-injected is a **null by construction** — do not run it.)
- **Telephone-game check:** over many recitation cycles, does the re-emitted goal drift from the original? (semantic similarity of recited goal to original over time.)
- Goal-adherence metric (LLM-judge or deterministic, depending on task).
- Token cost of recitation vs. adherence gain (payback calculation).

**Telephone-game sub-hypothesis (own confidence ~35 — plausible, not established):** repeated self-rewriting could *cause* goal drift if each rewrite slightly mutates the goal (iterative-summarization-drift analog). **Mitigation:** the original goal persists at context position 1, available as ground truth. **But this mitigation is itself conditional on §1.3:** if §1.3 holds (distant content has low active influence), the model effectively rewrites from the *recent* prior todo rather than the position-1 original, recreating telephone-game conditions; and if compaction (§1.2) removes the original, the ground truth is gone entirely. So the same low-active-influence property that makes recitation *necessary* (factor 2) also makes it *risky*. Links §1.2 / §1.3 / §1.4 mechanistically.

**Relationship to other entries:** Depends on §1.3 for the recency factor (factor 2). Robust to §1.3's partial failure via factors 1 and 3 (content + role), which are independent of the J-shape. The telephone-game sub-hypothesis is, conversely, *worsened* if §1.3 holds.

**Status:** candidate (pre-2.0); cadence sweep is hypothesis §3.2. Registered 2026-06-01. Mechanism revised + "reconciliation as distinct act" retired 2026-06-01.

---

### §1.5 — Skillify as a first-class agentic-engineering primitive

*Deferred — to be filed after the Anthropic + Chroma reads. See §2.3 for the framing and the Garry-Tan source. Decision 2026-06-01.*

---

### §1.6 — Token-frugality is a re-examinable 2013 instinct, not a law

*Deferred — to be filed after the Anthropic + Chroma reads. See §2.3 for the framing and the Garry-Tan source. Decision 2026-06-01.*

---

### §1.7 — Controlled context diversity counteracts pattern-rut brittleness

**Priority: LOW.** *Rationale: the failure mode it addresses (repetition loops) has a more reliable, deterministic countermeasure we're already committed to building — the loop-guard + explicit-terminal-states primitives (Module 2 / Phase 1.1; Module 6 / Phase 2.1). Diversity is a soft, probabilistic mitigation of a problem we'll have a hard tool for. Its load-bearing regime is also narrow (see preconditions). Invest experimental effort here only after the higher-priority positions and the deterministic guards are in place.*

**Stance:** In long agent loops where the accumulated action/observation stream is artificially uniform, the model can "few-shot itself into a rut" — continuing the surface pattern even when correctness requires diverging. Introducing *small, structured* variation into newly-appended actions/observations (alternate serialization templates, phrasing, minor ordering/formatting jitter) breaks the pattern and reduces this brittleness.

**Confidence:** 50. (EMERGING/CONTESTED practitioner heuristic; the underlying "uniform→brittle, diverse→robust" principle now has a second independent source — Anthropic, via few-shot — but the *specific* "small structured serialization variation nets positive" claim remains unquantified, and the benefit is partly subsumed by deterministic loop-guards. Nudged 45→50 on the second source.)

**Preconditions (where this position is load-bearing — narrow):**
Load-bearing only in the **intersection** of:
- **Rut can form:** loop is long/repetitive enough for many near-identical cycles to accumulate (~Manus-scale, not 1–5 calls).
- **Pattern ↔ correctness diverge:** correct behavior requires breaking the surface pattern (e.g., stop searching and synthesize; pivot a failed fix-class; exploration→exploitation transition). If continuing the pattern *is* correct, the position **inverts** — see below.
- **No cheaper guard:** no loop-guard / deterministic verifier / terminal-state enforcement already catches the repetition. (If those exist — and we're building them — the diversity intervention is largely redundant.)
- **Actions artificially uniform:** the task doesn't already produce heterogeneous actions (endogenous diversity needs no intervention).

**Inverted regime (do NOT apply — variation actively harms):** genuinely homogeneous batch tasks where repetition IS the goal (process N files/records/papers identically). Here the "rut" is correct behavior; variation adds noise, risks inconsistent outputs, and breaks cache for no benefit. *In our own substrate: ingest loop and experiment-runner are batch-uniform (inverted); position-formation reasoning is divergent (load-bearing).*

**Supporting evidence:**
- Literature: Manus "increase diversity" / "don't few-shot yourself into a rut" (July 2025) — practitioner claim, unquantified.
- Literature (second, independent — partial): Anthropic *Effective Context Engineering* (Sept 2025) on few-shot — "do not [stuff] a laundry list of edge cases... curate a set of diverse, canonical examples." This corroborates the *underlying* principle (uniform→brittle, diverse→robust) but via **example-coverage diversity** (span the behavior space), not §1.7's **anti-rut serialization diversity** (break the pattern in the appended stream). Partial corroboration of the principle, not the specific claim.
- Mechanistic: induction heads / in-context learning — uniform context strongly upweights pattern-continuation; the agent's own history functions as an implicit few-shot prompt; attention entrenchment on near-identical tokens lets the model autopilot the template instead of reading each observation. (Same ICL mechanism as §1.2, pointed the wrong way: uniform *successes* teach a brittle groove the way failures teach useful avoidance.)
- Analogous: human skill-rut / habituation.

**Consistency note (resolves an apparent contradiction):** §1.7 says "don't few-shot yourself into a rut" (uniform *history* is bad) while Anthropic endorses few-shot prompting. These are consistent: the bridge is *diversity*. Diverse few-shot examples are good; a uniform laundry-list of near-identical examples is exactly the rut-inducing pattern §1.7 warns about. Both say uniform context is brittle.

**Compatibility with cache discipline (resolves an apparent contradiction with §1.1):** "deterministic serialization" (§1.1) governs how *old* content is re-rendered each turn — it must tokenize identically or the cached prefix is invalidated. The diversity principle governs *new* appended content. Appending varied new items is **cache-neutral** (the prefix cache is unaffected by appends; new tokens are processed fresh regardless). Rule: *deterministic in how you reproduce the past; varied in how you render the present.* Variation must live in the appended action/observation stream, NOT in the stable prefix (system/tools) — varying the prefix would break cache.

**What evidence would update this (and by how much):**
- **Down 15–25 (toward retraction):** Controlled experiment in a divergent-reasoning long loop showing structured variation produces no measurable reduction in repetition-loop rate or improvement in task success vs. uniform serialization.
- **Down 10 (subsumed):** Loop-guards + terminal-state enforcement shown to catch essentially all the repetition the diversity intervention would, making diversity redundant where guards exist.
- **Down 5 (net-negative from noise):** Variation measurably degrades parsing reliability or output consistency more than it helps.
- **Up 10:** Clear reduction in repetition-loops / improvement in pivot-timing on a divergent long-horizon task suite, beyond what loop-guards alone provide.
- **Conditionally generalizes only to:** long divergent-reasoning loops with artificially uniform actions and no deterministic repetition guard. Does NOT transfer to short tasks, heterogeneous tasks, guarded loops, or (inverted) homogeneous batch tasks.

**Mechanism data to capture in any experiment:**
- Repetition-loop rate (duplicate/near-duplicate action signatures) under uniform vs. varied serialization.
- Pivot-timing: turns-to-strategy-change on tasks requiring a pattern break.
- Task success / goal-adherence delta.
- Parsing-error / output-inconsistency rate introduced by the variation (the downside check).
- Marginal value over a deterministic loop-guard baseline (the "subsumed?" check — run with guard-only, diversity-only, both).
- Cache-hit rate (confirm appended variation is cache-neutral; confirm no accidental prefix variation).

**Relationship to other entries:** Same ICL mechanism as §1.2 (in-context history shapes behavior), opposite valence. **Confounded with §1.2 in experiments** (errors are also diversity injections) — see §3.5 for the three-arm disentangling design. Competes with — and is likely partly subsumed by — the deterministic loop-guard / terminal-state reliability primitives (Module 2/6). Compatible with §1.1 once the deterministic-past / varied-present axis split is applied. Both §1.2 and §1.7 are instances of the §5.1 "context as in-context training set" framing (anti-uniformity / hard negatives).

**Status:** candidate (pre-2.0); LOW priority. Registered 2026-06-01.

---

### §1.8 — Signal density, not token count, governs context-rot onset

**Stance:** the onset and severity of context rot is governed primarily by the *signal-to-noise ratio* of the context, not by raw token count. At fixed length, adding semantically-similar competing content (distractors) sharply degrades performance; at fixed signal density, length matters far less. "Context is a finite resource" is more precisely "*high-signal* context is a finite resource."

**Confidence:** 80 (raised 70→80, 2026-06-04, on own-substrate experimental confirmation — Phase 1.0 Exercise A). Both literature (Chroma) and now our own measurements support it; cross-model replicated (Haiku + Sonnet). Mechanism-level → generalizes; magnitudes setup-specific (§0.8).

**Retraction criterion (the actual commitment):** demote if **(a)** any model shows a *neutral* (no-competition) knee *below* its diffuse knee — i.e. pure length rots before competition does, restoring token-count as primary — or **(b)** diffuse competition *fails* to collapse confident retrieval in a different model family. Clause (b)'s *within-family* leg is discharged (Sonnet 4.6 replicates the collapse); the *cross-family* leg (DeepSeek) is pending (§3.6 deferred check).

**Preconditions:**
- Retrieval or reasoning over long context (the regime where rot occurs at all; ≥ ~knee length).
- A meaningful signal/noise distinction exists (there IS competing/irrelevant content to vary). All-signal or all-noise context → claim vacuous.
- Frontier autoregressive models (Chroma's tested class).

**Supporting evidence:**
- **Experiment (own substrate, direct — Phase 1.0 Exercise A, `experiments/phase-1.0/results.md`):** at matched length, **diffuse** competition (pervasive task-related distractors, count ∝ L) collapsed confident retrieval to 0 by ~10–20k (Haiku) / ~5k (Sonnet), while **neutral** (topic-unrelated filler) and **localized** (fixed distractor count) held flat to 100k. Length held constant in the neutral arm produced *no* knee through 100k → competition, not token count, drives onset. The cleanest separation we have between the two candidate drivers, and it replicated across two models.
- Literature (direct): Chroma *Context Rot* — distractor experiments (semantically-similar competing content destroys the free budget at fixed length); needle-question-similarity (higher signal → later knee). See §4 Chroma, §5.2.
- Literature (consistent): Anthropic "smallest set of high-signal tokens"; Manus (signal-dense failures worth keeping, §1.2).
- Mechanistic: attention is finite and competitive; semantically-similar distractors compete with the needle for attention more than dissimilar filler does. The **diffuse** regime adds a length-coupled noise term the **localized** regime lacks (competitor mass ∝ L) — see §3.6 pre-registration; confirmed by the diffuse-collapses / localized-holds split.

**What evidence would update this (and by how much):**
- **Down 20–30 (toward retraction):** a setup where, at fixed signal density, length *alone* governs degradation (S/N held constant, length varied, large effect) — restores token-count as primary.
- **Down 5–10 (scope):** some task class (e.g., pure long-form generation) where token count dominates regardless of S/N.
- **Up 5–10 (banked 2026-06-04):** replication on our own agentic substrate (§3.6) showing S/N predicts the knee better than length — *realised*; this is the 70→80 move.
- **Further up (toward 85):** cross-family replication (DeepSeek) confirming the same competition-driven collapse — discharges the retraction criterion's clause (b) fully.
- **Conditionally generalizes to:** any long-context retrieval/reasoning regime with a signal/noise distinction. Direction transfers (mechanism); magnitudes don't.

**Mechanism data to capture:** at matched length, vary S/N (distractor count/potency, needle-question similarity) → S/N should predict accuracy better than length; at matched S/N, vary length → smaller effect. (This is the Chroma design; §3.6 re-runs it on agentic structures.)

**Relationship to other entries:** promoted from the §2.1 resolution sketch on direct Chroma evidence. Underlies §2.4 (the knee/budget is set by S/N), §5.2 (parameterized response), §1.7 (uniformity is one form of S/N degradation), §1.2 (failures are high-signal). The "data quality > quantity" row of §5.1.

**Status:** candidate (pre-2.0). Registered 2026-06-01. Confidence 70→80 on own-substrate experimental confirmation 2026-06-04; retraction criterion added.

---

## §2 — Open tensions

### §2.1 — Manus "keep the wrong stuff in" vs. Chroma context rot

**The tension:** Manus argues failures should accumulate in context as supervision signal. Chroma's empirical context-rot work shows performance degrades with total input length. Both can't be uniformly true.

**Sketch of a resolution:** failures are **high signal-to-noise tokens** — their information density per token is high, so the marginal context-rot penalty is "worth it." Generalizes to: token-budget questions should be **signal-density-weighted, not just token-count-minimized**. Compaction's job is to evict *low*-signal content, not all old content uniformly.

**Open empirical question:** At what point does failure accumulation cross over from useful supervision to rot? Plausibly depends on task length and total turn count.

**To test:** In Phase 1.0 exercise 1 (context-rot curve), include a variant where the padding is *failure-shaped tokens* (synthetic tool_use → error pairs) vs. random text. Does the curve shape differ?

---

### §2.2 — Failure-preserving accumulation vs. multi-agent isolation

**The tension:** Manus's "keep the wrong stuff in" argues failures across the conversation give the agent supervision signal. Anthropic's multi-agent research system (M4 reading, ~8 weeks out) advocates isolated context windows per subagent — failures in subagent A don't propagate to subagent B.

**Implication if both are correct:** multi-agent isolation systematically loses the cross-subagent error-recovery signal. This is a **previously-unconsidered argument for the Cognition position** in the contested M4 debate ("don't build multi-agents"), specifically for tasks where error-recovery matters most.

**To test:** when we hit Phase 2.4 (Module 4), include this in the isolation-boundary measurement. Does a single-agent variant outperform multi-agent specifically because it accumulates failure context?

---

### §2.3 — How much infrastructure to build around the model (Garry-school vs. Manus-school)

**The tension:** Two credible practitioner camps disagree on how much deterministic scaffolding an agent needs.
- **Manus-school (build careful infrastructure):** KV-cache discipline, stable prefixes, deterministic serialization, append-only context, error preservation, logit masking. The discipline *is* the product. (Manus, July 2025.)
- **Garry-school (trust the model; build minimal code):** "Stop building Foxconn factories for your agents." The economic inversion (tokens cheap, code expensive-to-maintain) means you should instruct the model in natural language and let it write the minimal code actually needed. Guardrails/validators/retry-loops are "an inch of cage bolted onto a worker who can already do the job." Markdown-as-program; the "skill pack" (markdown skill + minimal code + tests + eval + resolver) as a systems primitive. "Skillify." Tokenmaxxing. (Garry Tan, *540,000 Lines of Code I Didn't Need*, 2026, X/blog.)

**Sketch of a resolution:** likely **domain-dependent**, and the two camps are partly looking at different problems.
- One-shot creative / generative work (Garry's hackathon-judge example) → low infrastructure pays off; let the model cook.
- Long-horizon production loops with real, recurring failure modes (Manus's setup) → infrastructure earns its keep; the discipline is load-bearing.
- The **locus of disagreement is task length × failure rate × reuse rate** — exactly the axes our preconditions framework (§0.6) is built to expose.

**Caveat this tension repeatedly invokes:** the "Foxconn-factory" premature-abstraction risk. Cited by `tasks/lessons.md` §0.7 and `docs/conceptual.md` (positions-ship-with-evaluators invariant) as the reason generality should accrete along *proven* axes of variation rather than being built up front. Garry's piece is the canonical statement of this failure mode for agent infrastructure.

**Nuance to preserve (don't let the manifesto flatten it):** Garry is *not* anti-test — skill packs bundle unit tests + LLM evals + integration tests + resolver evals. The argument is against *the wrong tests on the wrong code* (validators/sanitizers/retries policing a capable model), not against verification. Stripping this nuance yields "skip tests," which is a wrong takeaway and would conflict with our own TDD discipline.

**Related candidate positions (pending, to file after Anthropic + Chroma reads):** §1.5 (skillify as a first-class primitive) and §1.6 (token-frugality as a re-examinable 2013 instinct). Deferred per decision 2026-06-01 to see how the Anthropic context-engineering post and Chroma context-rot study shift the landscape first.

**To test:** when skills are in hand (Phase 3.0/3.1), compare a heavy-infrastructure version of one of our tasks vs. a thin-skill version, across a one-shot task and a long-horizon task. Which wins where? Also: the §1.5 skillify reuse-rate experiment directly informs this.

---

### §2.4 — Context-assembly strategy: upfront vs. just-in-time vs. hybrid

**The tension:** three competing strategies for getting the right tokens into context, all aimed at the same established premise (curation beats dumping — follows from context rot):
- **Upfront retrieval (RAG):** fetch relevant chunks before the model runs.
- **Just-in-time agentic retrieval:** the model assembles context layer-by-layer at its own discretion via lightweight identifiers (glob/grep/read), maintaining only what's needed.
- **Long-context / full-dump:** stuff it in, let the model sort it (SELF-ROUTE, Li et al. arXiv:2407.16833 — LC and RAG agree on >60% of queries).

**Status of the debate — the source itself won't commit.** Anthropic's context-engineering post *sounds* like it endorses just-in-time, then hedges to "hybrid, task-dependent, do the simplest thing that works." So the mechanism (JIT-superiority) is **EMERGING, not established** — when the primary source hedges, that's evidence the field hasn't settled. (The *premise* — curation > dumping — is ESTABLISHED and is just our spine restated.)

**Sketch of a resolution — the decision variable is content dynamism × stability × value.** Anthropic's own worked example (Claude Code) decomposes cleanly: `CLAUDE.md` is dropped in **upfront** (static, always-relevant, high-value, stable); files are fetched **just-in-time** via glob/grep (dynamic, situational, would go stale if indexed — "bypassing stale indexing and complex syntax trees," the pro-grep evidence cf. Module 6B). So the defensible claim is not "JIT good" but: *static + always-relevant + high-value → upfront; dynamic + situational → JIT; mix per content type.* The hybrid framing suits less-dynamic domains (legal/finance) better.

**Temporal caveat (important — built-in expiry).** Anthropic predicts the boundary *drifts over time*: "as model capabilities improve, agentic design will trend towards letting intelligent models act intelligently, with progressively less human curation." So the right mix is conditional not just on task but on **model generation** — "curate aggressively" may be right in 2026 and wrong in 2028 on the identical task. This is the canonical case for **Property 3 (re-evaluation cadence)**: file with a *short* review timer; confidence in any fixed boundary should decay with time-since-measurement. First position we've hit that carries an explicit "re-test me, I have a shelf life" flag.

**To test:** the SELF-ROUTE replication (Module 8 / Phase 3.3) resolves the per-query RAG-vs-LC piece empirically. The just-in-time vs. upfront mix per content-type is testable earlier once we have real ingest content (Phase 2.3+). The persistence sub-layer (note-taking / filesystem-as-memory) is a *separate* CONTESTED question → §1.5 / §1.6 / Module 8.

**Source caveat:** Anthropic house view favors JIT + filesystem-as-context (it's how Claude Code works); curriculum flags selection bias toward Anthropic/OpenAI/LangChain/Manus. Corroborate against independent evidence before adopting.

---

## §3 — Testable hypotheses (Phase 1.0 exercise candidates)

### §3.1 — Compaction-preserves-failures vs. compaction-summarizes-failures

Implement two compaction strategies in `CategorizedContext`; run on a task suite that includes failure-prone scenarios; measure goal adherence + first-try-success rate.

→ Belongs to Phase 1.0 exercise 2 (compaction + fresh-window). Resolves §1.2 and partially §2.1.

### §3.2 — Recitation cadence sweep

Vary rewrite interval (every turn / every 5 / every 10 / never); measure token cost and goal adherence on a long-horizon task.

→ Phase 1.0 extension exercise (not in the strict three-exercise list). Resolves §1.4.

### §3.3 — KV-cache hit rate vs. anti-patterns

Implement controlled regressions: timestamp injection into system prompt, tools mutation mid-loop, content-shape mixing (string vs. block-list). Measure cache-hit-rate degradation.

→ Phase 1.0 exercise 4 (KV-cache instrumentation). Resolves several sub-claims of §1.1.

### §3.4 — Failure-shaped padding vs. random padding in context-rot curve

Variant on the standard context-rot reproduction: pad context with synthetic tool_use → error pairs instead of random text. Compare curves.

→ Phase 1.0 exercise 1 (context-rot curve). Resolves §2.1.

### §3.5 — Disentangling §1.2 (errors-as-signal) from §1.7 (diversity) — three-arm design

**Motivation:** keeping an error in context is *also* a diversity injection (it breaks the uniform-success pattern). So a naive "keep errors in" test confounds two mechanisms: the failure's *informational/corrective content* (§1.2) and the mere *pattern-break* (§1.7). They cannot be separated by a two-arm (clean vs. errors-kept) design.

**Three-arm design (on a failure-prone, divergent long-horizon task):**
| Arm | Context contains | Isolates |
|---|---|---|
| 1. Clean | uniform success stream, failures stripped | baseline |
| 2. Content-free deviation | pattern broken by *uninformative* noise (formatting jitter / placeholder deviations carrying no corrective info) | §1.7 pure pattern-break value |
| 3. Errors kept in | real failures preserved verbatim | §1.2 + §1.7 combined |

- `arm2 − arm1` = pure-diversity contribution (§1.7).
- `arm3 − arm2` = informational contribution of errors (§1.2), net of the diversity they also inject.
- `arm3 − arm1` = the total "keep errors in" effect (what a naive test would measure, undifferentiated).

**Shares machinery with §3.4** (the content-free-deviation arm resembles §3.4's random-text padding). **Shared tension:** both §1.2 and §1.7 add tokens for robustness → both weighed against context-rot (§2.1). Instance of the §5.1 framing (context as in-context training set: hard negatives vs. anti-uniformity).

→ Phase 1.0 exercise 2 (compaction) + extension. Resolves the §1.2/§1.7 confound.

### §3.6 — Context rot on realistic agentic haystack structures (bounded taxonomy)

**Motivation:** Chroma characterizes context rot on *contrived* haystacks (PG essays / arXiv, coherent vs. shuffled). The *realistic agentic-structure* case — what actually accumulates in an agent loop — is less studied and is what our substrate cares about. Sharpens Phase 1.0 exercise 1 from "reproduce Chroma's curve" to "reproduce on realistic agentic structures."

**Bounded taxonomy (NOT the universe — §0.7 discipline):**
- *Structure (format/arrangement):* `clean_essay` · `tool_call_stream` · `research_doc_stream`. Plus homogeneous ↔ heterogeneous (§1.7), coherent ↔ interleaved (Chroma's axis).
- *Competition (relatedness distribution — the key axis, added 2026-06-03):* `neutral` (topically-unrelated filler — Chroma's bulk) · `localized(n)` (a few discrete similar-but-wrong distractors in neutral bulk — Chroma's distractor design) · `diffuse(density)` (the *whole* haystack task-related, so competition is pervasive — the **real agentic regime**, which Chroma did NOT test). The localized↔diffuse distinction is itself a contribution: Chroma measured localized; agentic contexts are diffuse.
- *Relatedness level:* per-competitor similarity to the needle/question (the §1.8 signal/noise knob; sweepable / sensitivity-checkable).
- *Needle-question lexical similarity (added 2026-06-03):* `high` (question reuses needle wording → lexical-match shortcut, Chroma's easy bin) vs `low` (synonymized question → forces **semantic routing**, the step our H_B mechanism attacks). Sweep high/low in *validation* cells (clean essay); **fix `low` for the agentic-novelty cells** (semantic routing is the regime our claim is about, and where rot shows within budget). Caveat: low-sim synonyms must preserve question *specificity* — distinct from the distractors' concepts (e.g., "call number" stays distinct from the same-manuscript "storage box number") so the answer remains unique.

**Domain note (2026-06-03):** materials are in a benign **archive/catalog** domain (needle = "catalog number for the Meridian manuscript is QX-7793-LK"), NOT the original security framing (vault / authorization code). The real-API smoke test showed the security framing triggered **safety refusals** — the model found the needle but refused to report it, which would have measured refusal rate, not rot. See `tasks/lessons.md` §0.9.
- *Grounded in 2–3 task classes:* research agent (retrieved docs + reasoning) · coding agent (tool calls + file contents + errors) · conversational/memory agent (turns + recalled memory).

**PRE-REGISTRATION (locked 2026-06-03, before running) — localized vs. diffuse competition:**

*The fork:* does diffuse-but-pervasive competition spread distracting attention thinly so the needle keeps its edge (**H_A, benign**), or does the aggregate mass of many moderate competitors dilute the needle's relative weight (**H_B, malign**)?

*First-principles (softmax) reasoning → H_B.* Needle weight = `exp(s_n) / [exp(s_n) + Σ_competitors exp(s_d) + Σ_filler exp(s_f)]`. Key asymmetry in how the denominator scales with length L:
- *Localized:* competitor count **fixed** (k=1–4), high-similarity → competitor term `k·exp(s_high)` is **constant in L**.
- *Diffuse:* competitor count **∝ L** (density ρ of the whole haystack), moderate → competitor term `ρL·exp(s_mod)` **grows linearly in L**.
So diffuse carries a **length-coupled noise term localized lacks** → faster `w_needle` decay → steeper rot, earlier knee. Reinforced by (a) attention flattening in long context (softer softmax → moderate competitors matter more) and (b) diffuse raising the similarity *floor* (lower needle contrast — the §1.8 driver). Chroma corroborates: distractor-count monotonicity (1→4 worse) = the aggregate-mass mechanism; similarity-contrast governs rot.

*Counter-mechanism (H_A pocket):* the unique-string needle (`QX-7793-LK`) may be exact-match-robust via retrieval heads. **But** the *question* is semantic ("the **Meridian** manuscript's catalog number") — semantic *routing* to the right region precedes exact extraction, and routing IS vulnerable to diffuse competition. So H_B holds via the routing step. (Design consequence: distractors **share the needle's structure** — other manuscripts' catalog numbers, plus same-manuscript different-attribute distractors — so discrimination hinges on a fine semantic detail.)

*Pre-registered predictions:*
- **P1 (primary, conf ~70):** diffuse > neutral in rot at matched length; gap **widens with L** (earlier knee, steeper slope than neutral).
- **P2 (sharpest, conf ~60):** diffuse slope **steeper than localized**; diffuse **overtakes localized at long L** (diffuse competition scales with L; localized is fixed). Possible **crossover** — localized worse at short L.
- **P3 (conf ~65):** harm scales with per-competitor relatedness; at very low relatedness, diffuse ≈ neutral (the H_A pocket).
- **P4 (conf ~65):** discrimination hardest when distractors share the needle's structure.

*Key DV:* does a passband exist per (structure × competition), or decline from the start? Plus `(ceiling, knee, slope)` per §5.2. **Flips toward H_A if:** diffuse curves track neutral (no length-coupled extra decay) — would weaken the §5.2 agentic prediction (retrieval heads make unique-string needles robust to diffuse semantic competition).

**OUTCOME (2026-06-04, `experiments/phase-1.0/results.md`) — H_B confirmed; scored committed (key present, unhedged) + lenient (key present), 5-seed Haiku to 100k + 3-seed Sonnet to 20k, `tool_call_stream` / low-sim:**
- **P1 (diffuse > neutral, gap widens with L) — CONFIRMED, strongly.** Haiku diffuse committed `1.00→0.27(10k)→0.00(20k+)`; neutral & localized held flat to 100k (~0.7–0.9, *no* knee). The gap doesn't just widen — neutral has no knee in range at all, so it's qualitative. Length-alone (neutral arm to 100k) produced no decay → competition, not token count, is the driver (banks §1.8 70→80).
- **P2 (diffuse steeper than localized; crossover) — SUPPORTED, QUALIFIED.** Diffuse ≫ localized confirmed (localized held to 100k; diffuse dead by 20k). **No crossover observed** — localized never rotted in range, so it was never "worse at short L." The length-coupled-noise mechanism is supported by the *split*, not by a crossover.
- **P3 (harm ∝ relatedness; H_A pocket at low relatedness) — UNTESTED.** Relatedness not swept this phase (fixed at the structural-distractor design). Deferred.
- **P4 (hardest when distractors share needle structure) — UNTESTED directly,** but consistent with the observed binding-failure mode (model confuses Meridian's catalog number with other manuscripts' catalog numbers and with Meridian's other attributes). Deferred for a clean test.
- **Mechanism refinement (new, → §3.8):** the collapse is **discriminability loss** (can't bind needle→entity among competitors), expressed two ways — **confabulation** (Haiku states/lists wrong-or-multiple numbers) vs. **refusal** (Sonnet says UNKNOWN / "inconsistent and unreliable"). Committed→0 precedes lenient→0 (Haiku): discriminability fails *before* outright burial.
- **Validation spot-checks:** *Sonnet* — **DONE 2026-06-04**; replicates the collapse (zero by ~5k, earlier/harder than Haiku) → not a Haiku artifact; discharges the within-family leg of §1.8's retraction clause (b). *Realism* and *cross-provider (DeepSeek)* — still deferred (next phase).

**Cross-refs:** §3.4 (failure-shaped padding = one cell of this taxonomy), §1.3 (lower-bound), §1.7 (homogeneity), §2.1 (signal density), §5.1 (structure of the in-context training set).

**Dependency — verification attempted, UNRESOLVED (2026-06-01):** the paper's prose does not specify precisely enough whether coherent-vs-shuffled holds content+length constant and varies only *order* (interpretation B) or varies *topic-count* (1 essay vs. 3, interpretation A). As written, we cannot tell. Consequences:
1. **Rely on Chroma's structure finding only at the *mechanism* level** ("haystack structure affects retrieval somehow") — NOT the specific direction/magnitude, which the A/B ambiguity confounds (coherence vs. topic-count).
2. **§3.6 sidesteps it** by defining the coherence axis ourselves (content+length constant, vary only order). This turns the gap into an asset — a clean re-derivation *disambiguates* what Chroma left open (see strengthened contribution pitch).
3. **Optional escalation:** Chroma's released code/data (if available — they typically release) would resolve A vs. B definitively; primary artifact > prose. Not required since we sidestep.

**Validation spot-checks (de-risk the finding before leaning on it):**
- *Sonnet spot-check* — re-run the key cell (diffuse) on a stronger model (Sonnet 4.6). Per §0.8, confirms the *mechanism* transfers and calibrates how the knee shifts with capability (expected: later than Haiku's ~55k, possibly off-chart within 110k). NOT a magnitude claim.
- *Realism spot-check* — re-run diffuse near the knee with **LLM-generated** competitor lines instead of templated ones, to confirm the rot isn't an artifact of templated content (construct validity). One-cell, ~$2. (Filed 2026-06-04 — had been discussed but not recorded.)
- *Cross-provider replication (DeepSeek V4) — deferred* — replicate the diffuse-rot finding on a non-Anthropic model family to test §0.8 (mechanism transfers; magnitudes don't) and counter the Anthropic selection bias. Requires a provider adapter (OpenAI-format messages; token counting without a count_tokens endpoint) + re-validating the measurement on DeepSeek's behavior. Also the cheap workhorse for large future sweeps. Do AFTER the clean Claude P1/P2 is locked. (Filed 2026-06-04.)

→ Phase 1.0 exercise 1 (sharpened). Candidate Property-4 contribution (see `tasks/contribution-candidates.md`).

### §3.7 — Does tool-result clearing recover the agentic free budget? (failure-preserving vs. blanket)

**Motivation:** §5.2 predicts accumulated tool outputs are a dominant agentic distractor class that destroys the free budget; Anthropic's tool-result clearing (`clear_tool_uses_20250919`) removes them; §1.2 says failures carry signal and shouldn't be blanket-cleared. Tests whether targeted clearing recovers budget AND whether the §1.2 refinement (preserve failures) beats blanket clearing.

**Arms (on a failure-prone, tool-heavy long-horizon task):**
| Arm | Tool results in context | Tests |
|---|---|---|
| 1. No clearing | all kept (success + failure, raw) | baseline — distractor-rich; §5.2 predicts low budget |
| 2. Blanket clearing | all spent tool results cleared | Anthropic default; §5.2 predicts budget recovery |
| 3. Success-only clearing | clear spent successes, keep failures raw | §1.2 refinement |
| 4. Success-clear + failure summary | clear spent successes, replace failures with compact signal | §1.2 softened form |

- `arm2 − arm1` = does clearing recover budget (§5.2)?
- `arm3 vs arm2` = does preserving failures help (§1.2)?
- `arm4 vs arm3` = is a failure *summary* as good as raw failures (§1.2 down-5–10 softening)?

**Predictions:** arms 2/3/4 > arm 1 (budget recovery, §5.2); arms 3/4 ≥ arm 2 on failure-recovery tasks (§1.2); arm 4 ≈ arm 3 (signal not format, §1.2 softening).

**Cross-refs:** §1.2, §5.2, §1.8 (clearing raises signal density), §3.1 (compaction), §3.5 (failure disentangling) — shares machinery.

→ Phase 1.0 exercise 2 (compaction). Doubles as our hands-on comparison to the **first-party** compaction feature (`clear_tool_uses_20250919`) — which M1 exercise 2 calls for directly.

---

### §3.8 — Under diffuse competition, capability shifts the failure *mode* (confabulate → refuse) and pulls the knee *earlier*

**Stance (provisional, candidate hypothesis):** As model capability increases, the failure mode under diffuse competition shifts from **confident confabulation** (emit a wrong / multiple catalog number) toward **honest refusal** (decline / flag the records as conflicting), and the diffuse knee moves **earlier**, not later. A stronger model is a better *conflict-detector*, not a more robust *retriever*, under pervasive competition — so on a committed-accuracy metric it can look *worse*, while behaving more appropriately about its own uncertainty.

**Confidence:** 45 (provisional — single comparison, Haiku 4.5 vs Sonnet 4.6, n=9/point spot-check, one structure/similarity). Direction is clear in-sample; magnitude and generality are not.

**Evidence (Phase 1.0 Exercise A, `experiments/phase-1.0/results.md`):**
- Sonnet diffuse committed hits 0 by **~5k**; Haiku by **~20k** (knee ~4× earlier in the stronger model).
- Sonnet's *lenient* (mention) score also collapses fast (key often absent entirely) — it answers terse `UNKNOWN` even at 1k; Haiku keeps emitting the string (lenient stays higher) but hedges/errs. Same underlying discriminability loss, opposite surface behavior.
- Recorded answers: Sonnet — "inconsistent and unreliable", "cannot be reliably confirmed", `UNKNOWN`; Haiku — "found multiple catalog numbers: QX-7793-LK / BF-1573-NT…", commits-then-undercuts.

**Why it might be true (mechanism):** a stronger model more reliably *detects* that the needle is non-discriminating among competitors, and is better RLHF-aligned to refuse under detected ambiguity than to guess. Detection improves with capability faster than binding-under-competition does → earlier, more honest failure.

**Preconditions:** diffuse (pervasive, length-scaling) competition; a unique true answer exists (so refusal is a genuine binding failure, not appropriate caution); models in the same family/era (cross-family confounds capability with training/architecture).

**Retraction / update criterion:**
- **Down toward retraction:** a stronger model shows a *later* diffuse knee AND lower refusal rate than a weaker one (capability → genuine robustness, not earlier honesty) — would invert the claim.
- **Down (scope):** the refuse-vs-confabulate split is an artifact of the system prompt's "reply UNKNOWN if absent" instruction rather than capability — test by varying the refusal affordance.
- **Up:** a third model on the capability ladder (e.g. Opus, or DeepSeek tiers) continues the monotone "more capable → earlier-and-more-refusal" trend; and the split survives removing the explicit UNKNOWN affordance.

**Caveats (load-bearing — flagged for the reviewer pass):** (i) n=9/point, one (structure × similarity) cell; (ii) the "committed" metric *defines* refusal as failure — defensible only because the needle is the unique true answer (refusal = binding failure, not warranted caution), but the framing does the work and must be stated; (iii) the explicit `UNKNOWN` affordance in the answer prompt may inflate Sonnet's refusal rate (the scope-down test above).

**Relationship to other entries:** a refinement of §1.8 / §5.2 (the diffuse-collapse mechanism) along the capability axis; shares the discriminability mechanism with §3.6's H_B. Seed of a **Property-4 contribution candidate** (capability-dependent failure modes under pervasive competition) — logged in `tasks/contribution-candidates.md`.

**Status:** candidate hypothesis (provisional). Registered 2026-06-04 from the Phase 1.0 Sonnet spot-check. Needs a fuller test (ladder of ≥3 models, affordance control, ≥5 seeds, multiple cells) before any confidence above ~55.

---

## §4 — Reading notes per source (chronological)

### Manus — *Context Engineering for AI Agents: Lessons from Building Manus* (Yichao "Peak" Ji, manus.im/blog, July 2025) — read 2026-05-31 / 2026-06-01

**Headline:** KV-cache hit rate is "the single most important metric for a production-stage AI agent." Manus reports ~100:1 input-to-output token ratio in their production; cached vs. uncached input tokens differ ~10× in price.

**Stable-prefix discipline:**
- No volatile content (timestamps, version strings, build hashes) in the system prompt.
- Deterministic tool-schema serialization (no dict reordering between turns).
- Tool list should not mutate during a run — KV-cache invalidation AND model coherence (stale tool_use references in history that don't match current tools list confuse the model).
- Anthropic API supports up to 4 explicit cache breakpoints; place at known-stable boundaries (after system, after tools).

**Logit-masking over tool mutation:**
- Manus implements three function-calling modes via response prefilling: Auto / Required / Specified-by-prefix (uses Hermes-format models, NousResearch's `<tool_call>` template — i.e., self-hosted inference stack).
- Tools stay defined; mask which can be called per state.
- **Not directly accessible on Anthropic's API.** Closest equivalent: `tool_choice={"type": "any" | "tool"}` for the coarse "Required" / "Specified" modes. State-conditioned masking by prefix (`browser_*`, `shell_*`) is not available to Anthropic users.

**Recitation pattern:**
- Maintain a `todo.md` (or equivalent); agent rewrites it periodically.
- Pushes the goal into the highest-attention (most recent) position.
- ~50 tool calls per typical Manus task — drift is real at this scale.
- See §1.4 for the candidate Position.

**"Keep the wrong stuff in":**
- Failures (tool errors, malformed outputs, stack traces) are supervision signal, not noise to clean.
- Discarding failures and silently retrying throws away the in-context Bayesian update.
- See §1.2 for the candidate Position; §2.1 for the tension with Chroma; §2.2 for the M4 implication.

**Filesystem-as-context thread:**
- Briefly mentioned; defers to the broader "files are all you need" debate (M1/M7-8).
- To-revisit when reading Anthropic context-engineering post and CoALA/MemGPT in Module 7.

**Open follow-ups for the Anthropic / Chroma reads:**
- Does Anthropic's framing of context engineering ("smallest possible set of high-signal tokens") explicitly endorse or qualify Manus's "keep the wrong stuff in"? Both are Anthropic-adjacent thinkers.
- Does Chroma's context-rot measurement methodology differentiate signal-dense vs. signal-sparse padding?

### Anthropic — *Effective Context Engineering for AI Agents* (Sept 29, 2025) — read 2026-06-01

**Operational definition:** "good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome." Context = finite resource with diminishing marginal returns against an "attention budget." (= our spine; the established premise behind §2.4.)

**Just-in-time / self-managed context:** "Agents can assemble understanding layer by layer, maintaining only what's necessary in working memory and leveraging note-taking strategies for additional persistence." Decomposes into three claims of *different* status:
- Premise (curation > dumping) → ESTABLISHED (follows from context rot).
- Mechanism (JIT self-managed assembly) → EMERGING (one position in a live debate vs. upfront RAG and long-context).
- Persistence sub-claim (note-taking / filesystem-as-memory) → CONTESTED (Module 8 frontier).
→ Filed as tension §2.4.

**The hedge (the actual position).** The post later retreats from the confident-sounding JIT framing to: "the most effective agents might employ a hybrid strategy... The decision boundary for the 'right' level of autonomy depends on the task... 'do the simplest thing that works' will likely remain our best advice." Claude Code is the worked hybrid: `CLAUDE.md` upfront (static/stable), glob+grep just-in-time (dynamic). Plus a temporal claim: "as model capabilities improve, agentic design will trend towards... progressively less human curation."
- *Reading note (not a rule — too thin):* within one document, a confident topic-sentence followed by a later hedge — the **hedge is the position**, the lead-in is rhetorical. Don't extract the lead-in as the claim. When the primary source itself won't commit, treat the mechanism as unsettled.
- The temporal claim makes §2.4 the first position with a built-in expiry → short re-evaluation timer (Property 3).

**Tool design → context-management bridge:** "curating a minimal viable set of tools... can also lead to more reliable maintenance and pruning of context over long interactions." Weakly stated in the post but the mechanism is real and load-bearing: **tool definitions live in the context** (the tools block sits near the front of the prefix), so fewer/cleaner tools → smaller, more stable tool block → better KV-cache behavior + less context bloat. Direct Module-2↔Module-1 bridge; connects to §1.1 (tool stability). Carry into Phase 1.1 (Module 2, tool design).

**Few-shot / diversity:** "do not [stuff] a laundry list of edge cases... curate a set of diverse, canonical examples." This is the spine re-instantiated (high signal density over volume) and a second, independent source for the §1.7 underlying principle (uniform→brittle, diverse→robust) — see §1.7's updated evidence + consistency note. Confidence nudge applied (45→50).

**Compaction (captured 2026-06-01, post-first-read):** "the art of compaction lies in selection of what to keep vs. discard; overly aggressive compaction loses subtle but critical context whose importance only becomes apparent later." Tuning recipe: **maximize recall first, then improve precision** (safe default — adopt as our operational default for any compaction prompt). Tool-result clearing = "safest, lightest-touch" compaction (= `clear_tool_uses_20250919` on the Claude Developer Platform). → directly addresses the §5.2 agentic-distractor point; refined by §1.2 (preserve failures); tested in §3.7.

**Read complete.** Other threads (system-prompt structure, compaction vs. fresh-window, the sub-agent paragraph) read and consistent with the spine; added corroboration but no new positions filed.

### Chroma — *Context Rot: How Increasing Input Tokens Impacts LLM Performance* (Hong, Troynikov, Huber, 2025) — read in progress 2026-06-01

**Methodology ambiguity (haystack structure):** the coherent-vs-shuffled "haystack structure" experiment is **not written with enough precision** to tell whether it holds content+length constant and varies only sentence *order* (interpretation B, clean) or varies *topic-count* (interpretation A, confounded with topic-diversity). The figure shows windows (Original window = one essay; Shuffled window = three interleaved), which is consistent with B but doesn't prove it. → Downgrade reliance on the structure finding to mechanism-level only; resolve via Chroma's code if ever needed; §3.6 defines the axis cleanly ourselves regardless. (Per §0.8: a contrived result whose design is ambiguous gives mechanism, not magnitude.)

**Key findings (mechanism-level per §0.8; magnitudes are setup-specific):**
- *Length alone:* gradual degradation with length; a real plateau (free budget) exists in clean conditions (low-pass shape — §5.2).
- *Needle-question similarity:* high → longer plateau + gentler decline; low → earlier/steeper. Content *relationship*, not just position, drives retrieval.
- *Distractors:* semantically-similar competing content shrinks/eliminates the free budget (decline from the start). **Direct support for "signal density > token count."**
- *Distractor potency varies:* the potent distractor (D3) eliminates the passband; benign ones preserve some.
- *Repeated words:* **cliff** (not gradual) shape; strongly model-dependent (Sonnet 3.5 > Sonnet 4 / Opus 4 — newer ≠ more robust). Exception to the low-pass shape.
- *Structure (coherent vs. shuffled):* methodology too imprecise to use beyond mechanism level (see ambiguity note above).
- *Needle position/depth:* tested 11 positions for NIAH → **"no notable variation"** (no position effect for simple retrieval); repeated-words shows a *primacy* effect (best near beginning); Liu et al. (2023) found a U for multi-doc QA. Position-effects are **task-dependent**, not universal. → sharpens §1.3 (regime-specific shape) and supports its retrievability-vs-active-influence distinction. Method note: our context-rot harness uses a fixed depth grid {10/50/90%} averaged for the curve, decomposable by position (matches Chroma's multi-position approach; lets us detect a position effect in our novel agentic structures even though clean NIAH shows none).
- *Model capability:* lower-performing models rot earlier + steeper (earlier knee); but NOT monotonic in size/recency (Sonnet 3.5 > Sonnet 4 / Opus 4 on repeated-words) — long-context robustness is trained, not just scaled. → our Haiku-primary choice sees rot earlier/cheaper; magnitudes are Haiku-specific (§0.8), Sonnet spot-check calibrates the capability shift.

**What it moves:** grounds new framing §5.2 (parameterized response; passband conditional on S/N). Strongly supports the signal-density theme (underlies §2.1, §1.2, §1.7, §2.4) → candidate to promote signal-density to a standalone position (proposed §1.8). Reinforces the §1.3 *lower-bound* relationship (Chroma measures retrievability, the easier quantity) but does NOT directly test §1.3's position-asymmetry (these curves are length/similarity/distractor, not needle-depth) — so no direct §1.3 confidence change from these figures. Agentic prediction: distractor-rich agentic contexts → little/no free budget (→ §3.6).

**Read complete 2026-06-01.**

---

### arXiv:2603.10123 — *Lost in the Middle at Birth: Position Bias in Transformers* (Mar 2026) — read (primary source) 2026-06-04

**Headline:** a **U-shaped positional *sensitivity*** (Jacobian norm: how much the output moves with a token's *position*, content held fixed) is present at **initialization** (random weights), attributed to causal masking + positional encoding (RoPE) + softmax + depth. Training **mitigates** it (explored empirically) rather than erasing it; the paper flags Jacobian norm as "one lens — task performance may not fully reflect it," and scopes to autoregressive transformers.

**Why read it:** raised conversationally via a Gemini summary that overstated it ("*proved* a U-shaped *attention* bias that training *never erases* — an architectural *blind spot*"). Reading the source corrected three things — sensitivity (not accuracy/attention), training *mitigates* (not never-erases), "one lens" (not blind spot). Clean instance of secondhand-summary inflation (→ `tasks/lessons.md`, proposed verify-primary-source lesson).

**What it moves:** adds a candidate *architectural* mechanism to §1.3 (see the §1.3 note). Held **loosely**: it measures the sensitivity quantity (not §1.3's active-influence/retrievability), reconciles with Chroma's task-dependence via "training mitigates," and is untestable on our API-behavioral setup. Strengthens §1.3's "regime-specific shape" precondition without licensing a universal accuracy-U; no confidence change. **Caveat:** the attribution decomposition (softmax/depth shares) is via a fast-model PDF summary — verify the sections before citing precisely.

---

## §5 — Cross-cutting framings (candidate synthesis threads)

> Organizing lenses that span multiple positions/tensions — *not* positions themselves (no single stance/confidence) and *not* hypotheses (no single experiment). These are candidate scaffolds for the eventual capstone report: ideas that, if they hold up, give the synthesis its spine. Each carries known caveats so we don't over-run the analogy.

### §5.1 — The context window as an implicit in-context "training set"

**The lens:** the model learns from its context at inference time (in-context learning). So the accumulated context functions like a *training set* the model fits on the fly — and established good-training-set principles map onto context-engineering positions:

| Training-set principle | Context-engineering instantiation |
|---|---|
| Include hard negatives | §1.2 (keep errors in) |
| Avoid degenerate uniformity / don't overfit one mode | §1.7 (controlled diversity) |
| Curate quality examples | Anthropic "diverse canonical examples" (few-shot) |
| Data quality > quantity | §2.1 (signal density > token count) |
| Too much data isn't free | §2.4 / Chroma context rot |
| Recency / ordering matters | §1.3 (J-shape active influence) |
| Retrieval / sampling strategy | §2.4 (upfront vs. just-in-time assembly) |

**Mechanistic backing (not just analogy):** the in-context-learning-as-implicit-optimization line of work argues transformers performing ICL approximate meta-optimization over the context — so context genuinely shapes outputs in a manner structurally analogous to how training data shapes weights. The mapping above is therefore more than a mnemonic.

**Known disanalogies (caveats — the lens is useful, not a law):**
- **Transient.** ICL produces no weight update; the "learning" evaporates when the context does.
- **Order-dependent.** Real training shuffles data; context is strongly recency/position-weighted (§1.3). Order is load-bearing in a way it isn't for SGD.
- **Capacity-bounded.** More "training data" eventually *degrades* performance (context rot) — the opposite of the usual more-data-is-better prior.

**Why it's generative (the payoff):** if context is a training set, then *every* established ML-data practice becomes a candidate context-engineering position to test. Some we haven't considered:
- **Hard-negative mining** → deliberately curate the *most informative* failures to keep (not all failures equally).
- **Deduplication** → prune near-duplicate turns/observations (overlaps with compaction, but framed as redundancy removal).
- **Curriculum ordering** → sequence context easy→hard or general→specific where order is controllable.
- **Class balance** → avoid over-representing one action/observation type in history.

Each is a candidate §1/§3 entry the framing *predicts* before we've read a source advocating it — which is the test of whether the lens is doing real work or just relabeling.

**Status:** candidate framing (not a position). Registered 2026-06-01. Promote to a capstone-report section if it survives contact with the Phase 1.0 experiments and the later modules; demote if the disanalogies turn out to dominate (e.g., if the order-dependence and capacity-bound break the mapping more than they extend it).

### §5.2 — Context rot as a parameterized response; the free budget is conditional on signal-to-noise

**The lens:** accuracy vs. input length is well-summarized (for retrieval-style tasks) by a response with three parameters: **ceiling** (plateau/passband accuracy), **knee** (the length where decline begins = the empirical "context budget"), and **slope** (roll-off steepness). This makes context rot *quantitative*: each (task, model, condition) has a `(ceiling, knee, slope)` instead of a vague "accuracy drops with length."

**Key empirical finding (Chroma, 2026-06-01) — the passband (free budget) is conditional on signal-to-noise, not a fixed property:**
- Clean signal (no distractors; high needle-question similarity) → real passband; knee far right. [similarity & no-distractor curves]
- Distractors present (semantically-similar competing content) → passband shrinks or vanishes; decline from the start (knee → 0). [1- & 4-distractor curves]
- Distractor *potency varies*: benign distractors preserve some passband; the most potent (Chroma's distractor 3) eliminates it. [individual-distractor curves]
- Needle-question similarity shifts the knee: higher similarity → longer plateau, gentler decline. [similarity curves]

**Shape is task- and model-dependent — low-pass is NOT universal:** the repeated-words task shows **cliff** behavior (flat ~1.0 then sharp drop), not gradual roll-off, and is strongly model-dependent (Claude Sonnet 3.5 holds far longer than Sonnet 4 / Opus 4 — *newer ≠ more robust here*). So: low-pass (gradual) for clean retrieval; cliff for replication-style tasks; `(ceiling, knee, slope/cliff)` is a function of task × condition × model.

**Shape not mechanism:** "low-pass" / "cliff" describe shapes, not a frequency-domain process. Per §0.8: take the mechanism and direction, not Chroma's specific magnitudes.

**The agentic punchline (strong, actionable prediction) — now experimentally confirmed (2026-06-04):** real agentic contexts are **distractor-rich by nature** — accumulated tool outputs, related retrieved docs, prior similar reasoning all act as semantically-similar competing content. So per the conditional-passband finding + the §1.3 lower-bound (Chroma measures the easier *retrievability* quantity), **real agentic contexts likely have little or no free context budget** — they live in the "with-distractors, knee→0" regime, not the clean-needle regime. Aggressive context curation is therefore not optional hygiene for agents; there's no free plateau to coast on.

> **Confirmation (Phase 1.0 Exercise A, `experiments/phase-1.0/results.md`):** modelling the *diffuse* regime (whole haystack task-related — the agentic case) on `tool_call_stream`, the **free budget collapsed to ≈10–20k tokens (Haiku) / ≈5k (Sonnet)** — confident retrieval went to 0 — while the *neutral* control held a passband flat to 100k. So the agentic "knee→0" prediction holds on our own substrate: the diffuse free budget is small and sets in early, exactly where the prediction placed it. Re-promotes this framing from "Chroma-grounded prediction" to "own-substrate-confirmed." Caveat: a unique-string needle is a *retrievability ceiling* (the easier quantity, §1.3) — active-influence budget is plausibly ≤ this.

Directly motivates §3.6 (does a passband exist *at all* for realistic agentic structures? — answered: not under diffuse competition) and strengthens §2.1 / §2.4.

**Targeted countermeasure:** tool-result clearing (Anthropic's `clear_tool_uses`) removes exactly the dominant agentic distractor class identified above (spent tool outputs) → **prediction: clearing spent tool results recovers free budget in agentic contexts** (tested §3.7). Per §1.2, clear spent *successes* but preserve a *failure* signal.

**Status:** candidate framing, empirically grounded (Chroma) and **own-substrate confirmed** (Phase 1.0, 2026-06-04). Registered 2026-06-01. The agentic-no-free-budget prediction (the key testable claim) held: diffuse free budget ≈10–20k Haiku / ≈5k Sonnet (→ §3.6 outcome, §1.8).
