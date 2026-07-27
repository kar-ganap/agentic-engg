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

### §0.20 — Competitor PRESENCE ≠ competitor RIVALRY (verify discrimination pressure, not just volume)
**Trigger:** *Without this, a retrieval-collapse experiment can produce a "null" that's actually uninterpretable — the manipulation moved volume + competitor *presence* but not genuine *discrimination pressure*. The Phase 1.1 #4 chain sweep got 55/55 correct-use with the needle buried under ~186k tokens and 8 same-format competitors present (so the manipulation bit on volume + presence), because the competitors were passing ticket-mentions, not same-frame rivals for "the holder of order O" — the agent never faced a real "which of these candidates" choice. With this, you confirm the stimulus offers plausible same-frame alternatives (the §0.18 sweet-spot, now about RIVALRY) before reading a null as a refutation.*
- A null where competitors are present-but-not-rivals is **inconclusive, not a refutation** (cf. §1.8 clause (b), the clean_essay control). Generalizes §0.18 from static haystacks to agentic tasks.
- Bonus hypothesis surfaced: **agentic self-production may immunize** — when the agent *fetched* the needle via a labeled tool call (vs. a passively-dumped value), it recalls it under heavy burial. A contribution candidate, but confounded with the rivalry gap; an active-vs-passive A/B + same-frame rivals are needed to separate them.

### §0.21 — A pilot's job is to validate the *rig*, not to read the *curve*: verify the control at full seed-count before narrating a shape
**Trigger:** *Without this, a low-seed pilot produces a clean, compelling, but spurious curve that gets over-read. The §1.8 length-extension 2-seed pilot showed DeepSeek v4-flash neutral retrieval at a tidy `1.00 → 0.50(94k) → 0.17(758k)` and it was narrated as "pure length collapses retrieval — the falsifying shape." At 5 seeds it evaporated: ~0.4–0.7 across all lengths, including 0.67 at 10k (the control itself wasn't solid) — seeds 1–2 were the lucky draws. With this, the pilot is read only for what it can support (does the rig run? does the control hold at the FULL seed-count? does the top-end complete?), and curve shape is claimed only from the solidified run.*
- **The control must hold at the seed-count you'll interpret at, not the pilot's.** The pilot's 10k=1.00 (n=2) became 10k=0.67 (n=5) — a control that "held" at 2 seeds was shaky at 5. §0.18 says verify the control; §0.21 adds: *at full N*.
- **Don't narrate a shape from n=2.** Three points × two seeds is a rig check, not a measurement. State direction tentatively or not at all until the curve is filled in + seeded.
- **What saved it:** pre-registration + the standing "don't move confidence yet" rule. The dramatic read never reached the synthesis; the solidification run (1+2) corrected it before commit. The discipline worked as designed — log the near-miss, keep the discipline.
- The *real* result survived: v4-pro + Haiku (the capable models) hold the neutral null to ~94k; a mild length effect appears only at ~758k. The clean signal came from the capable instruments, not the noisy one.
- **Run the §0.21 gate BEFORE banking, not after (sharpened 2026-06-14).** A second, worse instance: the #4-v2 low-disc "collapse" (seed-4, n=5, active=passive) reached a **banked position** ("#4 ⊆ §1.8 demonstrated") before the full run; at 12 seeds it was **0 mis-binds**, gone. The three-reviewer pass caught it post-bank. Pilot results are not bankable — gate at full N first. (No temperature control made the single draw look real.)

### §0.22 — Corner an effect by removing escapes; a self-generated needle carries an accessibility advantage you must *remove* (not bury) to test interference
**Trigger:** *Without this, you keep building agentic "rot" tasks that don't rot and mis-read the chain of nulls as "no effect" — when in fact every task handed the needle an accessibility advantage that §1.8's collapse regime specifically lacks (exact-key / most-recent / distinctive-cue / fresh-self-fetched-result). The #4-v2 arc ran FIVE designs, each removing the prior's escape; **all five held (0 mis-binds) at full seed-count** — including the fifth (low-DISCRIMINABILITY cue) built to collapse. (A 5-seed pilot of #5 showed a seed-4 lure-capture, banked as "demonstrated ⊆ §1.8"; it did NOT replicate at 12 seeds — §0.21.) With this, you read the chain as "the reason they keep holding IS the finding" (#4 ⊆ §1.8 as a **structural argument**: self-generation is a near-tautology, fetching ≠ wall-retrieval), and you know which knob would test agentic interference — but you also know the chain produced **no induced collapse**, so the agentic question stays *untested*, not resolved.*
- **Rescue-progression as method.** Remove one escape per design (exact-match → recency → small-N → burial → discriminability). When the n-th design still holds, the *reason it holds* is the result. Cheaper and more conclusive than one big factorial. **Caveat (2026-06-14): the tempting "the n-th design *collapses* — that's the finding" tell is subject to §0.21** — design-5's collapse was a pilot artifact; the real finding was "all five held." Reading a collapse needs full-N confirmation before banking.
- **To induce agentic interference, lower cue-DISCRIMINABILITY — do NOT add length or burial.** Length/burial only pressure the *passive* sub-components (the prompt-resident cue→item map); the self-generated needle is a fresh/recent tool result, structurally unburiable by prompt-fill. We confirmed this (rolebind held to 37k burial; the diagnosis ruled out 740k a priori).
- **The §1.8 gradeable/luring tradeoff (reinforces §0.18).** On fuzzy-semantic cues there is no clean sweet-spot for a collapse *rate*: gradeable cues (clear unique answer, e.g. two-attribute) ⇒ no lure (0/48); luring vague cues ⇒ fuzzy answer (the "mis-bind" is a defensible alternative) **and don't reliably lure across seeds** (the seed-4 pilot capture didn't recur at N=12). A gradeable collapse *rate* needs §1.8's own unique-answer needle (clear answer + low-sim question + same-type distractors) ported to the frame — not a quick re-pilot.
- **Loop-guard assumes idempotent tools.** A stateful tool (identical `(tool,args)`, different result each call — e.g. recency's `apply_adjustment`) trips the duplicate-signature loop-guard at the 2nd call; turn it off (or make it signature-aware) for such tiers. → relevant to the #7 loop-guard tier.
- **Bonus reusable artifact:** the **stem-checker** (`shared_stems`) — a cue-leak guard + lure-construction validator that caught two real leaks before they ran.

### §0.23 — When the aggregate DV is confounded, lean on a confound-free *per-decision* signal
**Trigger:** *Without this, you commit a verdict to a noisy aggregate. #6's token DV is total cost, but in a stateless tool loop total tokens ≈ Σ(return_size × remaining_turns) — dominated by the **number** of tool calls the agent happens to make (variable `get_ticket` re-reads), not the format policy under test (A-fhigh made 12 `get_ticket` calls vs C-fhigh's 9 → that alone explained the "C cheaper than A" gap). So you fall back to the **per-decision behavior**. BUT (sharpened 2026-06-14, three-reviewer pass): the per-decision read must be **COMPLETE**. The first #6 read — "arm C goes `detailed` everywhere, the choice is unexploited" — was a **read-tools-only slice**; the full per-tool view shows all three models go `concise` on the terminal `send_message` (return unused) and `detailed` on the consumed reads — i.e. they DO use the choice, sensibly. The partial view inverted the verdict (from "remove the choice" to "the choice is used; fix-to-inline-detailed is the surviving claim"). A per-decision signal is confound-free only if you look at **every** decision, not a subset.*
- **Stateless re-send makes call-count, not per-return size, the dominant token lever** — a return of size S arriving at turn t costs ~S×(remaining turns). Control the call sequence (or measure per-return) before reading totals as a format/efficiency DV.
- **A uniform-success cell is a non-discriminating DV, not a clean win.** #6's A/C/D all hit 100% because the task was easy → success couldn't separate the arms; only the (confounded) tokens differed. Note when the *intended discriminator* fails to discriminate, and fall back to the mechanism signal.
- **Tabulate the behavioral signal across ALL tools/decisions before reading it.** The "detailed everywhere" error came from tallying only the read tools. One `groupby(tool) × response_format` would have caught the `send_message` concise usage immediately. Aggregate-by-subset is its own confound.
- **Capability-anchor a behavioral claim, not just a magnitude.** The §0.8 Claude anchor confirmed a *behavior* across a ~7× gap — but note the corrected behavior: Sonnet/v4-pro *also* go concise on `send_message` (the choice is used cross-family), not "default to detailed."

### §0.24 — Predict→verify: pin the mechanism, pre-register an analytic prediction, then verify empirically — the residual is the calibration audit
**Trigger:** *Without this, you either (a) trust an analytic cost/scaling model unverified and ship a number reality never meets, or (b) run a blind empirical sweep with no falsifiable target and rationalize whatever curve appears. #3's carry-vs-swap break-even ran (1) a smoke to pin the mechanism (DeepSeek caches tool defs; mutating them busts the suffix), (2) an analytic predictor pre-registering N\* ≈ 5,111 tool-tokens from that mechanism + known rates, (3) a real-API sweep that verified 6,461 — and the 26% miss decomposed cleanly into calibration (actual S/C/k > nominal raised both the swap floor +22% and the carry intercept +19%), while the carry *slope* — the mechanism — matched to <0.1%. With this, the prediction is falsifiable before the spend, and the prediction-vs-measurement gap localizes exactly which assumption was off (here: token calibration, not mechanism) instead of "close enough" hand-waving.*
- **The residual is a feature, not noise.** A predict→verify gap points at the wrong assumption — decompose it (here: actual S/C/k overshoot nominal → both swap floor +22% and carry intercept +19% rose; the slope/mechanism matched) before reporting the match. Don't attribute the whole gap to one term without checking the others.
- **Measure in the currency you predicted in.** #3's first apparent "miss" (3,802 vs 5,111) was a nominal-vs-actual token mismatch — the filler wasn't token-calibrated. Recover the real currency (actual tool-tokens from turn-1 input) before comparing.
- **Cross-condition cache contamination flattens the curve you're measuring.** Conditions sharing a filler prefix get cross-condition cache hits (DeepSeek TTL hours-days) — salt each condition + add a per-run nonce so every cell is cold. (Generalizes the Phase 1.0 Exercise-B cross-condition cache confound to the scripted setting.)
- **Cheap + conclusive.** The whole #3 arc was ~$0.22 because the prediction told us exactly which N to bracket — pre-registration narrows the sweep.

### §0.25 — To induce competition, distractors must be ON-AXIS + non-decisive-by-flaw; a "silent-on-the-axis" distractor guarantees triage-ability
*(The phase-2.0 plan + pool headers tagged the silent-distractor red line "§0.22" — a loose cross-reference error; lessons §0.22 is the unrelated rescue-progression lesson. The silent criterion was never a formal §0.x; §0.25 is its corrected replacement.)*
**Trigger:** *Without this, distractors built to be topically-related-but-SILENT-on-the-axis are trivially triaged as off-topic — no competition is induced, the phenomenon under test (§1.8 diffuse-collapse) can't fire, and the arm comparison collapses into who-triages-best. The first §1.8 reasoning sweep exposed it: plan_execute read exactly the 3 targets (reads=3, 96% target citations) at every N∈{4,12,24} and baseline held a flat stance-correctness (~3.5), because the targets were specific empirical findings and the distractors were generic off-axis mechanisms — separable by RELEVANCE at a glance. With this, distractors ENGAGE the axis (may even lean to the wrong answer) but carry an EXPLICIT decisiveness-defeating flaw (confound / underpower / mixed result / metric fragility): untriageable by topic, non-decisive by construction, so the model must actually reason about each flaw.*
- **The cause is relevance-triage, not specificity.** Off-axis = recognizably-not-the-answer; making the targets vaguer wouldn't help. The fix is on-axis distractors, full stop.
- **The tension it resolves:** non-decisiveness (needed for a fixed correct answer) vs selection-confusability (needed for competition). An explicit flaw defeats decisiveness *without* changing the correct answer — the only way to have both.
- **Multiplier corollary:** near-duplicate variants (one-word slots) read as obvious filler; vary the numbers *and the flaw itself* so variants look like distinct studies. And update the grading KEY to name the discount-the-flawed-evidence move, or the DV won't reward flaw-detection.
- Generalizes **§0.20** (presence ≠ rivalry): silent-on-axis distractors are *present* but non-rival by construction.

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

### Phase 1.1 — Tools (Module 2) (closed 2026-06-14)

**What worked**
- **The three-reviewer pass earned its keep — it caught two over-claims before merge.** This is the phase's headline process result. The method-rigor reviewer (verified firsthand against the run data) found that (a) #4's "demonstrated ⊆ §1.8" was a non-replicating 5-seed pilot artifact (0 mis-binds at 12 seeds), and (b) #6's "detailed everywhere / choice unexploited" was a read-tools-only slice (all 3 models actually go concise on `send_message`). Both had been *banked*. The critical-boundary review is exactly the gate that should catch pilot-grade/partial-view banking — and it did. → #4 60→**15** (inconclusive), #6 62→**48** (reframed).
- **Rescue-progression (§0.22) as a method still holds** — removing one escape per design is the right way to corner an agentic effect. The correction: its tempting "the n-th design *collapses* → that's the finding" tell is subject to §0.21; design-5's collapse didn't survive full N, so the honest finding was "all five *held* → no collapse induced → #4 ⊆ §1.8 is a structural argument, not a demonstration."
- **Predict→verify (§0.24, new) on #3.** Smoke-pinned mechanism → analytic pre-registration (N\* ≈ 5,111) → empirical verification (6,461), residual decomposed (slope matched <0.1%; intercept + swap-floor both +~20% from nominal). ~$0.22 because the prediction told us which N to bracket. A reusable method; survived the pass cleanly.
- **Pre-registered retraction criteria did real work.** #4(i)'s retraction *fired* (correct-use flat) across all five designs and was honored (60→15) — anti-drift working, not theater. Confidences moved only with the user, after the data + the review.
- **Capability-anchoring behaviors across families (§0.8).** The corrected #6 behavior (all of v4-flash/Sonnet/v4-pro use concise on `send_message`) is itself a cross-family behavioral fact; #3's existence+cost-model is mechanism-general.
- **TDD harness held across five new tiers.** `make check` green (194 tests) the whole arc; stash-proofed scorer normalization; the isolated-tier pattern (per `run_binding`) kept the chain runner untouched.

**What caused friction**
- **Two positions were banked on under-powered/partial evidence (caught only at review).** #4 ⊆ §1.8 was banked "demonstrated" on a 5-seed pilot collapse that didn't replicate at 12 seeds (§0.21 sprung post-bank); #6 "remove the choice" was banked on a read-tools-only tally that the full per-tool view inverted (§0.23). Discipline slip = **banking before the §0.21 full-N gate and before the complete per-decision tabulation**. The fix is procedural, now in §0.21/§0.23: gate at full N and tabulate across *all* decisions *before* banking, not at the reviewer pass. (Cost: a confident retro/`/learn`/commit that then needed a correction pass — avoidable.)
- **Loop-guard assumed idempotent tools** — stateful `apply_adjustment` (identical args, different result) tripped the duplicate-signature guard at call 2, sending the recency tier to $0.003 no-ops. Fixed (`loop_guard=False` for that tier); logged (§0.22).
- **Gradeable/luring tradeoff** blocked a clean agentic collapse *rate* — sharper cues become gradeable but kill the lure (0/48); vague cues lure but aren't cleanly gradeable. This is *why* #4(ii) parked; a gradeable agentic collapse needs §1.8's unique-answer needle ported (the RAG-vs-grep frame, later).
- **Nominal-vs-actual token calibration + cross-condition cache contamination (#3)** — two clean re-runs needed before the verification was trustworthy (§0.24). The discipline (verify on real API; don't trust nominal) caught it.
- **Stale session-start git snapshot** briefly mis-read the branch state (thought we were on `phase-1.0-ext-deepseek`); minor detour, resolved (branch was already correctly based on post-PR#2 main).

**Rule changes proposed**
- **`[ADD]`** §0.20 (presence ≠ rivalry), §0.21 (pilot validates the rig at full seed-count), §0.22 (rescue-progression; remove discriminability not length), §0.23 (lean on the confound-free per-decision DV), §0.24 (predict→verify; residual = calibration audit). All five **filed** in §0.
- **`[MODIFY]`** §0.21 **sharpened** by the review — *run the full-N gate BEFORE banking, not after* (the #4 slip). §0.23 **sharpened** — *the per-decision read must be COMPLETE (all tools/decisions), not a subset* (the #6 slip). CLAUDE.md Current State updated (post-review numbers).
- **`[DELETE]` none.** Considered whether §0.20 (reading a presence-only null) is now subsumed by §0.22 (rescue-progression) — **rejected**: distinct failure modes (reading a null vs. *inducing* the effect), the same way 1.0-ext kept §0.17/§0.18 separate. Nothing has yet proven to be decoration; the rule set is still young.

**Synthesis cleanup proposed** (post-review numbers)
- **§1.1** — carry-vs-swap break-even qualification added (conf 78; #3); residual-wording fix + prior-art (dynamic-tool-loading / prompt-cache-economics) to add. **§1.8** — 78→80 (pillar B, one capable cross-family model to ~758k; "to ~1M" tightened) + #4 recorded as a *failed-to-induce* probe (no confidence change), not a clean fold-in. **#4(i)** — demoted 60→**15** (INCONCLUSIVE; the "demonstration" didn't replicate — §0.21); #4 ⊆ §1.8 is a structural argument; stays in the graph with its retraction reason (Substrate Discipline #2). **#6** — 45→**48** (reframed: the choice IS used sensibly; surviving claim = fix-to-inline-detailed via the arm ranking, NOT "remove the choice"). Two tool-design candidates filed (both reframed by the pass). No merges.

**Tool / permission allowlist additions**
- None. (AskUserQuestion used for the two user-owned calls — #3 confidence + synthesis placement; no new permissions.)

**Throughline property progress**
- **No surface advanced** (Stage 1 — expected; first scheduled surface is Phase 2.1 / Property 3). **Property 3 exercised in spirit** (three positions *moved* with retraction criteria firing, not drift). **Property 4:** two contribution candidates + two reusable methodological assets (rescue-progression, predict→verify).
- **FLAG (carried to the retro):** two consecutive concept-heavy phases (1.0-ext, 1.1) with **zero surface** progress. On-schedule for Stage 1, but **Phase 2.1 must ship a runnable surface slice** (Property 3 staleness scheduler) — the gate's first real test against sandbox-pull. Manual re-evaluation discipline ≠ the built surface.
