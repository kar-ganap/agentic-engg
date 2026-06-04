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
