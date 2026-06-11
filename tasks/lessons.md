# Lessons (Process Stream)

> Process journal — discipline that outlives the curriculum. Distinct from the **concept stream** (which lives in the evidence graph + `docs/synthesis.md`). See CLAUDE.md § Two-Stream Discipline.
>
> Append-only by convention. Entries follow `/learn` ritual at phase close: What worked / What caused friction / Rule changes ([ADD]/[MODIFY]/[DELETE]) / Synthesis cleanup / Tool-permission additions / Throughline property progress.

## §0 — Canonical lessons (carry-forward, terse)

These are the rules that survive across phases. Curated; not append-only. Anything not pulled up here from a `/learn` entry remains a phase-specific note below.

### §0.1 — Two-stream discipline is non-negotiable
**Trigger:** *Without this, concept and process work bleed into each other; positions get cluttered with tooling notes, and process learnings get lost inside paper-bound retros. With this, each stream has a clean lifecycle.*
**Operationalization:** concept content → evidence graph + `docs/synthesis.md`; process content → here.

### §0.2 — Learning-first overrides velocity
**Trigger:** *Without this, the project drifts toward shipping the artifact and skips the load-bearing learning, defeating the user's stated primary goal. With this, every phase's design tradeoff is examined, not bypassed.*
**Operationalization:** user writes the load-bearing parts (raw loop, schema design, position-formation logic, all design tradeoffs). Claude scaffolds plumbing. See memory `feedback-learning-first`.

### §0.3 — Throughline-property gate at every phase boundary
**Trigger:** *Without this, the substrate quietly slides into a curriculum-companion sandbox that dies at Week 16. With this, the four-property scaffolding is actively maintained.*
**Operationalization:** Stage 2+ retros must report which of {ingest, query, re-evaluation, contribution} moved this phase. Zero progress two phases in a row → re-evaluate.

### §0.4 — Real-API smoke tests catch what unit tests can't
**Trigger:** *Without this, layers that touch an external API harbor wiring or protocol-validation bugs that any number of unit tests using permissive fakes will miss; the bug surfaces only in production. With this, one slow real-API smoke per API-touching layer catches the contract drift cheaply.*
**Operationalization:** every PR that changes how we call an external API should add or update a `@pytest.mark.slow` smoke test that exercises the change end-to-end. Run `make test-all` before declaring a phase done. Phase 0.0 worked example: 26 unit tests green, the slow smoke caught a per-message isolation-counting bug that 400'd against `count_tokens` because the SDK validates conversation structure, not just tokenizes.

### §0.5 — Fakes should be at least as strict as the thing they fake (where cheap)
**Trigger:** *Without this, a permissive test fake silently masks real-API rejection paths; bugs slip through unit tests and only surface against the real service. With this, fakes that can cheaply replicate the real validation do — closing the gap between unit-test green and production-correct.*
**Operationalization:** when a fake is introduced (`FakeCounter`, `_CompleteSpy`, etc.), document what aspects of the real thing it does and does **not** replicate. If a behavior would be cheap to simulate (e.g., rejecting an unmatched tool_use block), simulate it; if not, ensure a smoke test covers the gap.

### §0.6 — Positions are conditional, not binary; update confidence in graded steps
**Trigger:** *Without this, a single experiment's null result over-generalizes into a universal claim and the trajectory of belief gets lost; or a positive result transfers uncritically to projects with different profiles. With this, each Position carries explicit preconditions, graded confidence-update rules (not retract-or-not), and conditional generalization scope — results are useful even when mixed, and only transfer to next-projects whose conditions match.*
**Operationalization:** every Position in `docs/synthesis.md` must specify (a) **preconditions** sourced via five heuristics (claim's own internal logic; inverted failure modes; analogous patterns; pivot conditions; locus of dispute); (b) **graded confidence updates** (down X / down Y / up Z) keyed to specific evidence patterns, not binary retract-or-not; (c) **conditional generalization scope** — what next-projects can inherit this confidence and which need fresh tests; (d) **mechanism data to capture** during any experiment, not just outcome. First experiments partly *discover* what conditions should have been pre-registered — refinement is part of the workflow, not a failure of pre-registration.

### §0.7 — Positions ship with re-pointable evaluators, not one-off scripts
**Trigger:** *Without this, each position's evidence is bound to the problem it was first tested on; evaluating it for a new problem means rebuilding the measurement from scratch, and the package's long-term value (plug-and-play position evaluation) never materializes. With this, a new problem can be matched against preconditions and run through the bundled evaluator with only its (task suite, model, metric) supplied.*
**Operationalization:** experiment code is parameterized over the axes we've seen vary (start: model, task suite, metric), exposes the position's mechanism-data spec as its output schema, and refuses gracefully when preconditions aren't met. **Generality accretes along proven axes — do NOT pre-build a universal evaluator (Foxconn-factory risk, cf. synthesis §2.3).** The first experiments may be problem-specific; the plug-and-play target is reached by refactoring along discovered axes, not by up-front universalization. Extends Substrate Discipline #5 (CLAUDE.md): the bar is *re-pointable at a new problem*, not merely *regenerable on the same one*. The §0.6 preconditions + mechanism-data structure IS this evaluator's interface contract — applicability-check as input gate, mechanism-data as output schema.

### §0.11 — Binary substring scoring is confounded by verbosity + truncation
**Trigger:** *Without this, a retrieval eval that substring-matches a free-form generation measures "did the answer appear in the first N output tokens of a verbose reply," not retrieval — verbose/cautious models bury or withhold the answer and score as failures that aren't retrieval failures, and a low max_tokens truncates before the answer. With this, the answer is constrained to a concise form and max_tokens set well above the answer length, so the deterministic scorer measures the intended capability.*
**Operationalization:** force a concise answer via a system prompt (e.g. "reply with ONLY the X, else UNKNOWN") and set max_tokens ≫ answer length (`runner.ANSWER_SYSTEM`, max_tokens 256). **Incident (2026-06-04):** the Sonnet spot-check showed Sonnet "rotting" catastrophically worse than Haiku (knee 3k vs 55k, hitting 0.00) — but diagnosis revealed *both* models hedge under diffuse competition ("Meridian has conflicting catalog numbers"); Haiku states the code early (scored hit), Sonnet editorializes and gets truncated at max_tokens=64 (scored 0.00). The apparent capability inversion was a **scoring artifact**. All pre-fix curves (item 2 + 3) conflate retrieval with answer-formatting and are not reportable. Caught by the spot-check before publishing. (Reinforces §0.4/§0.9: smoke/spot-checks catch what unit tests can't.)

### §0.10 — Secrets strictly from .env; the shell environment is a footgun
**Trigger:** *Without this, `load_dotenv()` (override=False default) lets a shell-exported `ANTHROPIC_API_KEY` (e.g. a work key in `.zshrc`) silently take precedence over `.env`, so the project spends on the wrong account. With this, secrets load via `stance.secrets` (`dotenv_values`, `.env`-only, no `os.environ` fallback, raises if absent) — the shell is never consulted, and a wrong/missing key fails loud instead of billing the wrong org.*
**Operationalization:** all API clients built with `api_key=stance.secrets.anthropic_api_key()`; never bare `anthropic.Anthropic()`; never `load_dotenv()` into `os.environ`. `.env` holds a project-scoped *personal* key — never a work/shared key. **Incident (2026-06-03):** a work key exported in `.zshrc` overrode `.env` (which happened to hold the same work key) and was used for ~$17 of personal experiments before the account hit its limit; surfaced only when the API returned a 400 credit-balance error. Fix: `.env`-only loading helper + CLAUDE.md security rule. **User action still required:** rotate the work key and put a project-scoped personal key in `.env`.

### §0.9 — Needle/task framing must avoid safety-refusal triggers (refusal ≠ failure)
**Trigger:** *Without this, a retrieval/agentic eval whose needle or task reads as a request for sensitive info (credentials, vault codes, a security audit) measures the model's REFUSAL RATE, not the capability under test — the model finds the needle but declines to report it, and every "miss" is ambiguous (retrieval failure vs. refusal). With this, benign-domain materials make accuracy reflect the intended capability.*
**Operationalization:** design needles/tasks in topically-benign domains (e.g., archive catalog numbers, not vault authorization codes). **Before any sweep, run a real-API smoke on an EASY cell and confirm the model both finds AND reports the needle** (hit on the trivial case) — not just that the harness runs. Worked example (2026-06-03): a "vault authorization code" needle triggered Haiku refusals ("would be a serious breach of security protocol") despite the model having located the code; swapped to "catalog number for a manuscript." The slow smoke test caught it before a ~$20 sweep that would have silently measured refusal. (Reinforces the smoke-tests-catch-what-units-can't lesson, §0.4 — here it's a *construct-validity* bug, not an API-shape bug.)

### §0.8 — Contrived-setup result asymmetry: negatives generalize downward, positives don't
**Trigger:** *Without this, we treat a contrived benchmark's positive result (model succeeds on a toy) as evidence of real-world capability — the classic "we pass needle-in-haystack at 1M tokens" trap — and/or dismiss a contrived negative result as "too artificial to matter." With this, we read contrived evidence directionally and extract what actually transfers.*
**Operationalization:**
- **Contrived + NEGATIVE (model fails/degrades) → take it as a robust lower bound** — *provided the contrived task is no harder than reality.* Real is messier/harder, so a failure on the simplified case implies failure at least as bad in the wild. ("If it breaks even here, it breaks in the wild.")
- **Contrived + POSITIVE (model succeeds) → distrust as a generalization.** Success on an easy toy says nothing about the harder real task; demand a realistic eval before believing it.
- **Always check the difficulty direction first.** The asymmetry's validity depends on contrived ≤ real difficulty. If the contrivance is *adversarially harder* than reality (e.g., hand-crafted worst-case distractors), the negative result is *mechanistic evidence* (the failure mode exists) but NOT a clean lower bound on real magnitude.
- This is the formal version of Module 6 benchmark skepticism (cf. the rigorous-benchmarks paper, arXiv:2507.02825 — trivial agents scoring well = contrived positives that don't generalize). Worked example: Chroma context-rot is a *contrived negative*, which is exactly why its contrivance is acceptable (see synthesis §1.3 lower-bound note).

### §0.12 — Log spend at run time, not retroactively
**Trigger:** *Without this, debugging-iteration spend goes un-itemized — only the final committed runs are reconstructable — and the running tally drifts from reality (we believed ~$42 spent; reconstruction from committed run files showed ~$16, with the rest un-attributable overwritten iteration). With this, every API run is logged when it happens, so spend is accurate, attributable, and regenerates (Substrate Discipline #5).*
**Operationalization:** append a `tasks/spend.md` row per run batch at run time; capture exact `response.usage` (incl. cache fields) rather than `count_tokens` estimates × a placeholder price (Exercise B builds this). Run files that get overwritten on re-run are NOT a spend ledger — the ledger is the ledger.

### §0.13 — Don't over-read a comparison condition: isolate one factor, and characterize the asymptote
**Trigger:** *Without this, a comparison yields a wrong conclusion two ways — (a) it silently varies a second factor, or (b) a mid-curve value is mistaken for a final one. Both happened in the realism check (2026-06-05): the v1 LLM-competitor pool varied phrasing AND relatedness (only 15% of lines were actually high-relatedness), so the vanished collapse looked like a "templating artifact refutation" when it was a relatedness confound; and v2's 0.80@20k was called a "plateau" until extending to 100k revealed a delayed collapse to 0.20. With this, the realism finding came out right: natural-phrasing potent competition DOES collapse (knee ~50k), composition sets the knee not the floor.*
**Operationalization:**
- **Verify the manipulation before trusting the result.** When generating a comparison condition, *measure* that it matches the baseline on every axis except the one under test (we classified the pool's relatedness composition before re-running). A check that moves two variables answers neither.
- **Never call a value a plateau without data past the knee.** Extend the sweep until the curve is flat or zero; a single mid-curve point is a way-station, not a floor. (Cheap to check; expensive to get wrong in the synthesis.)
- Corollary to §0.7: a re-pointable evaluator makes "match composition / extend length" a one-flag re-run, not a rebuild.

### §0.14 — Conditions that share a stateful backend (e.g. the KV-cache) must be isolated
**Trigger:** *Without this, experimental conditions run back-to-back contaminate each other through shared server state, and you measure the bleed instead of the effect. In Exercise B the prompt cache is shared server-side for ~5 min, so five cache policies run in sequence reused each other's cached prefixes (identical canonical tools, rotations, history) — `tool_reorder` spuriously hit `stable`'s cache; `restore` hit the standalone `tool_reorder` run. Three re-runs to diagnose. With this, each condition gets a unique prefix so its cache is independent and the per-condition number is intrinsic.*
**Operationalization:**
- Give each condition a **unique nonce in the prompt**, and put it where it actually isolates: the cache invalidation hierarchy is `tools → system → messages`, so a `system` nonce does NOT isolate the `tools` root — to isolate fully, vary content **at or before the cache root** (a per-condition tag in a tool definition).
- Prefer **steady-state** readings (t≥1) over t=0, which is most exposed to cross-condition warmth; and fire a condition's turns back-to-back within the TTL so *intended* within-condition caching still works.
- General form of §0.13: any shared mutable backend (cache, rate-limit state, a warmed model, a DB) is a hidden second factor; isolate it or measure it.
- Cost note: the cache also makes the experiment cheap (reads at 0.1×) — isolation doesn't change that, it just makes the numbers mean what you think.

### §0.15 — Post-hoc findings inherit the pre-registered design's affordances; they need a dedicated control before being claimed
**Trigger:** *Without this, an emergent (post-hoc) finding is reported as if it were measured cleanly, when it actually inherited prompt/design choices made for a different, pre-registered question. §3.8 (capability shifts confabulate→refuse) emerged from the data, but the answer prompt's explicit "reply UNKNOWN" affordance — correct for the pre-registered rot finding (it fixed the §0.11 verbosity confound) — is a live alternative explanation for the stronger model's refusal. With this, the post-hoc finding is held provisional and gated on a control that varies exactly the inherited choice.*
**Operationalization:**
- The right prompt for the *pre-registered* question is usually wrong for an *unanticipated* one — and you can't pre-empt findings you didn't expect (YAGNI). So don't blame the original design; instead treat post-hoc findings as **exploratory**, and design a **confirmatory control** that toggles the suspected inherited factor (here: re-run with the UNKNOWN affordance removed).
- Keep the post-hoc confidence low (§3.8 at 45) and state the control as a *gating* criterion, not a nicety.
- This is the exploratory-vs-confirmatory distinction (a refinement of §0.6): pre-registered = confirmatory and clean; emergent = exploratory and needs its own pre-registered re-test.

### §0.16 — Verify primary sources even when a reviewer (or subagent) hands you the citation
**Trigger:** *Without this, you treat a reviewer's or subagent's cited reference as ground truth — but the reviewer's gloss is itself secondhand. In the Phase 1.0 three-reviewer pass, reading the cited sources firsthand corrected the reviewer THREE times: the §1.3 paper's mechanism (geometric causal+residual, NOT softmax/RoPE; training does NOT mitigate — two reversals from a fast-model summary), the fallback paper (it CONTRADICTS §3.8 rather than pre-empting it — opposite scaling direction, different regime), and KVFlow (eviction/scheduling, not the prefix-cache mechanism it was cited for). With this, every load-bearing citation is read at the source before it shapes a position or a contribution claim.*
**Operationalization:**
- A citation that changes a confidence, a contribution claim, or a position's framing must be **read firsthand** before it's applied — WebFetch the abstract/sections, don't trust the one-line gloss (reviewer, subagent, or web summary).
- Generalizes §0.13 (verify the primary source): the *source of the secondhand claim* doesn't matter — Gemini, a fast-model PDF summary, an Opus reviewer, **or our own in-repo / seed docs** are all secondhand. (2026-06-09: `Agentic_Engineering_Curriculum.md:88` presented a quoted *"40% decrease in task completion time"* as from Anthropic's *Writing Effective Tools for AI Agents*; reading the blog firsthand showed the number is **not in the source** — the blog's claim is qualitative. The fabricated quote in our own seed doc propagated into conversation **and** the Phase 1.1 buffer before the user caught it. A trusted in-repo doc is *not* a primary source.) The firsthand read paid off every time this session.
- Cheap exception: low-stakes "acknowledge prior art" citations where the mechanism is textbook-established (RadixAttention, PagedAttention) can be cited from settled knowledge; the agent-specific / near-cutoff ones (KVFlow) get read.

### §0.17 — Cross-provider comparisons need a provider-neutral *structure*; tool-call-format history confounds
**Trigger:** *Without this, a cross-provider replication uses a structure that triggers provider-specific behavior, and you measure the behavior difference instead of the effect. Porting the `tool_call_stream` rot harness to DeepSeek (via its Anthropic-compatible endpoint) failed because DeepSeek emits its internal tool-call markup as text — the tool_use/tool_result history primes it to *continue calling the tool* rather than answer. The §0.11 "remove the tools param so it must answer" fix is Anthropic-specific and does not transfer. With this, cross-provider tests use a structure with no provider-specific priming.*
**Operationalization:**
- For cross-provider work, prefer a **provider-neutral structure** (plain prose / single user message) over tool-call-formatted histories, which prime provider-specific continuation.
- An "Anthropic-compatible endpoint" reuses the *wire format*, not the *behavior* — re-run the measurement-validity checks (detector phrasings, response shape, tool-call leakage) on the new family before trusting any number (§0.16's sibling at the behavior level).
- The same effect can surface as a *different failure mode* across families (Haiku confabulates, Sonnet refuses-with-text, DeepSeek abstains/empties) — categorize the failure, don't just score accuracy.
- **Confirmed by a paired 2×2 (2026-06-10, `experiments/phase-1.1/smoke_dsml_factorial.py`):** the DSML leak is **conjunctive** — `tool_call_stream × no-tools` = 3/30, all of {stream×tools, flat×none, flat×tools} = 0/30. Both the tool-call *priming* AND the missing *tools channel* are necessary; declaring tools (real agent operation) eliminates it. The Module 2 harness builds safely on the Anthropic-compatible endpoint.

### §0.18 — Verify the *control* holds before interpreting the *treatment*; a needle tuned for one structure may not transfer
**Trigger:** *Without this, you read a treatment-vs-control contrast where the control itself is broken, and conclude nothing (or the wrong thing). The diffuse-collapse on `tool_call_stream` low-sim relied on the neutral control *holding* (~0.8). Porting to `clean_essay` prose, the same low-sim question broke the control — the model refuses to bridge folio↔manuscript in a reading-comprehension framing and answers UNKNOWN even with zero competitors, so neutral fell to ~0.4 and the diffuse effect was masked. High-sim would have made diffuse too easy (verbatim exact-phrase match). The clean effect lived in a structure-specific sweet spot. With this, you check the control is intact in each new regime before interpreting the treatment, and you treat "clean effect in regime X" as regime-bound until shown otherwise.*
**Operationalization:**
- In every new structure/model/regime, **confirm the no-treatment control behaves as expected** (here: neutral holds) before reading the treatment (diffuse). A broken control makes the contrast uninterpretable, not negative.
- Effects can be **entangled with the stimulus design** (needle-question similarity) × structure: a needle that yields a clean effect in one structure may be unfindable (too-low similarity) or trivially findable (too-high / verbatim) in another. A cross-context claim needs a **stimulus whose findability is structure-invariant** (mid-similarity), validated per regime.
- Don't over-generalize a single-regime clean result; state its regime explicitly (a generality caveat) until a structure-invariant replication exists.

### §0.19 — Substrate flipped to DeepSeek-primary / Claude-anchor (cost + cross-provider validity)
**Trigger:** *Without an affordable primary substrate, a years-horizon curiosity-driven curriculum can't be fully explored — Haiku at $1/$5 per MTok makes broad sweeps cost-prohibitive — and an all-Anthropic evidence base carries the selection bias the prior-art reviewer flagged. With DeepSeek-primary (v4-flash $0.14/$0.28, ~7–18× cheaper) + Claude spot-anchors, exploration is affordable AND positions are cross-provider by construction.*
**The decision (2026-06-05, end of Phase 1.0 ext):** the full convention is a CLAUDE.md Code Rule (§ Experiment substrate). Process-stream rationale + caveats recorded here:
- The DSML tool-call-leak that confounded the cross-family rot run was a **contrived-no-tools artifact** (tool history + no `tools` param), not a general DeepSeek problem — real agent work (Module 2+) *declares* tools → structured tool calls. Smoke-test the declared-tools path at Module 2 entry; native OpenAI-format client is the fallback (§0.17).
- The needle-similarity entanglement (§0.18) is **provider-independent** (it bit Haiku too) — orthogonal to the substrate choice.
- This *inverts* the Phase 1.0 tiering (Haiku-primary + Sonnet-spot → DeepSeek-primary + Claude-spot); it improves §0.8 cross-provider grounding rather than weakening it.
- Standing cost: per-experiment measurement re-validation on DeepSeek (§0.16/§0.17), and Claude-only-feature experiments stay on Claude.

---

## Phase-specific notes (chronological)

### Phase 0.0 — Foundations (closed 2026-06-01)

**What worked**
- **Dependency injection for `count_fn` and `complete_fn`.** Made everything testable without burning API quota; enabled the smoke test as a clean swap of the same hooks.
- **Template adoption wholesale from epibench / ccupa.** Zero hours spent reinventing project hygiene. Stage/Phase model, validation gates, two-stream discipline all worked out of the box.
- **Deliberate step-by-step build with explicit OK gates.** User caught design questions early (integer vs number, conftest hoist, LLM-call abstraction) before they ossified. Slower per turn, but no rework.
- **Real-API smoke test paid back the same day it was written** — caught a per-message isolation-counting bug that 26 unit tests using a permissive `FakeCounter` had missed. See §0.4.

**What caused friction**
- **Pyright diagnostics noise from IDE not pointing at `.venv`.** Cosmetic but accumulated; resolves by pointing the editor's Python interpreter at `.venv/bin/python`. Not actioned this phase.
- **`uv sync` initially stuck searching for Python 3.12;** the user's `uv 0.5.4` (Nov 2024) doesn't auto-install missing Pythons. Resolved with `uv python install 3.12`. Worth upgrading `uv` (`brew upgrade uv`) when convenient.
- **Per-message isolation counting in `CategorizedContext.append_message` failed against the real API** because Anthropic's `count_tokens` validates conversation structure (assistant `tool_use` must be followed by matching `tool_result`). Required redesign to cumulative + delta with deferral on incomplete states. ~30 minutes recovery. See §0.4.

**Rule changes proposed**
- **`[ADD]` §0.4** — Real-API smoke tests catch what unit tests can't (promoted; see above).
- **`[ADD]` §0.5** — Fakes should be at least as strict as the thing they fake, where cheap (promoted; see above).
- **`[MODIFY]`** — none.
- **`[DELETE]`** — none. Stage 0 just established the rule set; nothing has yet proven decoration.

**Synthesis cleanup proposed**
- None — no concept-stream output this phase.

**Tool / permission allowlist additions**
- None.

**Throughline property progress**
- None. Stage 0 is foundation; properties begin advancing in Stage 2.

### Phase 1.0 — Context Engineering (closed 2026-06-05)

**What worked**
- **The competition axis (neutral / localized / diffuse).** Turning Chroma's contrived "distractors" into a *competition-density* axis cleanly separated the two candidate drivers — the neutral arm (length only) had no knee to 100k, so competition, not token count, owns the onset. The single best design decision of the phase.
- **committed / lenient bracket.** The *gap* became a result (discriminability collapses before burial; capability-dependent failure mode → §3.8), not just a scoring choice.
- **Close-batch robustness checks each earned their keep.** Baseline validated the instrument (reproduced Chroma); realism caught both a templating/relatedness confound *and* an overclaim (the "plateau"); Sonnet produced §3.8. None were ceremony.
- **Pre-registration before runs (§3.6 P1–P4, Exercise B P-B1–P-B4).** Made the outcomes honest — P2 came out *qualified* (no crossover) and we recorded that, rather than retrofitting.
- **Reading the primary source.** The arXiv paper and the caching docs each corrected a secondhand error — the latter fixed a *wrong mental model* (system-first hierarchy) that would have mis-ordered the whole Exercise B prediction.

**What caused friction**
- **Spend went un-itemized** (~$42 belief vs ~$16 reconstructed from run files) → §0.12.
- **Realism v1 confounded realism × relatedness; v2's 20k value misread as a plateau** → §0.13. Several re-runs.
- **KV-cache cross-condition bleed** → three `cache_run` re-runs to diagnose; the `tools` cache-root stayed shared even after a system nonce, leaving restore (P-B4) only directional → §0.14.
- **Pyright `.venv` noise** persisted (carry-forward from 0.0; editor-interpreter fix still not actioned — purely cosmetic, ignored during `make check`).

**Rule changes proposed**
- **`[ADD]`** §0.12 (log spend at run time), §0.13 (isolate one factor; characterize the asymptote before naming a plateau), §0.14 (isolate conditions sharing a stateful backend). All filed.
- **`[MODIFY]`** CLAUDE.md "Current State" → Phase 1.0 closed (housekeeping, not a governance change). §0.13's principle **kept in `lessons.md`**, *not* promoted to Substrate Discipline (decided: it's a specific operationalization; the pre-registration rule already carries the constitutional weight).
- **`[DELETE]`** **none.** Considered merging §0.11 into §0.13 and rejected: they are distinct failure modes — §0.11 is *scorer-validity* (the instrument misreads response form), §0.13 is *comparison-design* (the comparison varies two factors / a partial curve is misread). All current rules remain load-bearing.

**Synthesis cleanup proposed**
- None to demote or merge — every position moved coherently on measured evidence. §3.8 is correctly provisional (45). §5.2 was *qualified* (knee is potency-dependent), not deleted — the walk-back trajectory is itself the learning (Substrate Discipline #2).

**Tool / permission allowlist additions**
- None. (WebFetch for the paper + caching/pricing docs was already available and is the right tool for primary-source verification.)

**Throughline property progress**
- **Contribution (Property 4) advanced.** Two candidates now have data: localized↔diffuse rot regime + potency dose-response, and capability-dependent failure modes (§3.8). Logged in `tasks/contribution-candidates.md`. Ingest / query / re-evaluation: not this phase.

### Phase 1.0 Extension — Cross-Provider Validation + Substrate (closed 2026-06-10)

> Retro: `docs/phases/phase-1.0-extension-retro.md`. Inconclusive cross-family attempt + the DeepSeek-primary/Claude-anchor substrate adoption. No new position committed → no three-reviewer pass (deferred to Phase 1.1 close).

**What worked**
- **Anthropic-compatible endpoint → reuse the whole pipeline unchanged.** The `complete_fn`/`count_fn` DI seams paid off again: cross-family wiring was a `--provider` flag, not a rewrite. Byte-identical message structures = no format-translation confound.
- **Reading sources firsthand** (DeepSeek format spec → "DSML" is leaked internal markup, *not* a documented format; the §1.3 paper re-read). §0.16 held every time.
- **Honest inconclusive.** Recorded "clause (b) open + harder" + the structure×similarity entanglement rather than forcing a result from a confounded run (Substrate Discipline #2).
- **Substrate decision shipped with a trigger statement + carve-out** (Claude-only-feature experiments stay on Claude) — passes the rule-admission test.

**What caused friction**
- **DSML tool-call leak** confounded the cross-family `tool_call_stream` run (a contrived-no-tools artifact; the no-tools fix is Anthropic-specific) → §0.17.
- **`clean_essay` control broke** (low-sim folio-wrinkle wrecks the neutral control on prose) → §0.18. The clean effect lived in a structure-specific sweet spot.
- ~$9.5 spent on an inconclusive (but informative) attempt — the entanglement finding is the yield.

**Rule changes proposed**
- **`[ADD]`** §0.17 (cross-provider needs a provider-neutral structure), §0.18 (verify the control holds before interpreting the treatment), §0.19 (substrate flip → DeepSeek-primary/Claude-anchor). All filed.
- **`[MODIFY]`** CLAUDE.md: Code Rules += "Experiment substrate: DeepSeek-primary, Claude-anchor"; Current State updated; subagent model-tiering clarified as distinct from the experiment substrate.
- **`[DELETE]` none.** Considered merging §0.17 and §0.18; rejected — §0.17 is a *provider-format* confound, §0.18 is *control-validity per regime*. Distinct failure modes.

**Synthesis cleanup proposed**
- §1.8 generality caveat added (cross-structure/provider generality NOT established; clause (b) open). §3.8 abstention added as a 3rd failure mode (caveated; stays 45). §3.6 cross-provider row (inconclusive). No demotions or merges.

**Tool / permission allowlist additions**
- None. (WebFetch already available; used for the DeepSeek spec + Manus infra re-read.)

**Throughline property progress**
- **No surface advanced** (Stage 1 — expected). **Property 3 (re-evaluation) exercised in spirit:** §1.8/§3.8 re-evaluated against cross-family evidence, held-with-caveat rather than drifting. The substrate decision improves cross-provider grounding (feeds Property 4 later).
