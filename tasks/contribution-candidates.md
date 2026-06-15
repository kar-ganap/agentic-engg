# Contribution Candidates

> `[CANDIDATE-CONTRIBUTION]` notes for the Property-4 export pipeline (Weeks 11–12 / Phase 3.1). Each entry is a candidate for export as blog post, paper section, OSS package, or skill — pending pipeline build-out.
>
> Format: title + 2-sentence pitch + audience + dependencies + status.

---

## [CANDIDATE-CONTRIBUTION] Disciplined Research-Software-with-AI Engineering

**Pitch:** The `crit-thinking → synthoracle → epibench` template lineage + ccupa plugin conventions encode discipline that's more advanced than what most agentic-engineering primary sources prescribe for project hygiene — two-stream separation (concept vs. process), rule-admission test with mandatory `[DELETE]`, confidence-scored parallel reviewers at critical phase boundaries, model-tiered subagents, stash-based bug-fix proof. Together they're a coherent methodology for doing research-grade software with AI agents that deserves its own write-up.

**Audience:** researchers using Claude Code / coding agents for serious work; engineering managers building agent-augmented teams; the agentic-engineering practitioner community.

**Dependencies:** Property-4 export pipeline (Phase 3.1) must exist. Also benefits from at least one phase where the discipline visibly paid off (probably surfaces in a Phase 2.x retro).

**Status:** filed 2026-05-29. To be re-evaluated once Phase 3.1 lands.

**Adjacencies:** ccupa README, epibench's CLAUDE.md (the closest analog), the curriculum's Module 6B (which discusses CLAUDE.md/AGENTS.md authoring but not the meta-governance layer).

---

## [CANDIDATE-CONTRIBUTION] Context rot characterized for realistic agentic context structures

**Pitch:** Chroma's *Context Rot* characterizes degradation on contrived haystacks (PG essays / arXiv, coherent vs. shuffled). The structures that actually accumulate in agentic loops — tool-call/observation streams, interleaved retrieved docs, reasoning traces, preserved failures — are a less-studied gap. If rot onset/shape differs meaningfully across realistic agentic structure classes, that extends Chroma's contrived result to the agentic regime where it actually bites, which is a publishable finding.

**Audience:** agent builders; context-engineering practitioners; the Chroma / long-context research community.

**Dependencies:** Phase 1.0 exercise 1, sharpened (synthesis §3.6). Bounded-taxonomy discipline (§0.7) — characterize a few realistic classes, not the universe. First verify Chroma's coherent-vs-shuffled design (content+length held constant?) so we don't inherit a topic-count confound.

**Status:** filed 2026-06-01. **First data landed 2026-06-04** (`experiments/phase-1.0/results.md`). **Prior-art reframe (three-reviewer pass, 2026-06-05 — RULER read firsthand):** the bare **localized↔diffuse distractor-*count* axis is NOT the contribution** — RULER (Hsieh et al., arXiv:2404.06654) already spans it (Multi-key NIAH: 4 fixed distractors ≈ localized; `num_keys = full haystack` ≈ diffuse) and reports the same headline (perfect vanilla NIAH → large drops with length → "failure to ignore distractors"). **The defensible delta, which neither Chroma nor RULER does (verified firsthand):** (a) **distractor relatedness/potency as a swept knob** — RULER uses same-format random distractors and "does not vary distractor similarity"; we show a potency dose-response (the realism v1<v2<templated curve: knee ~10k saturated → ~50k natural-mixed, still collapsing by 100k); (b) an **agentic-structure substrate** (`tool_call_stream`; planned `research_doc_stream`) vs RULER's noise/PG-essays; (c) a **committed (confident-usable) vs mentioned collapse** — discriminability fails before burial — which RULER's failure-mode analysis doesn't isolate. So: cite RULER + Chroma as prior art; claim only (a)+(b)+(c). Re-evaluate after `research_doc_stream` + the §5 relatedness sweep + cross-provider (DeepSeek) replication.

**Adjacencies:** Chroma *Context Rot*; **RULER (arXiv:2404.06654)**; the NIAH-critique lineage (RULER intro; Michelangelo, DeepMind 2024); synthesis §1.3 (lower-bound), §3.4, §3.6, §5.1, §1.8, §5.2; the curriculum's Module 1 context-rot exercise.

---

## [CANDIDATE-CONTRIBUTION] Capability-dependent failure modes under pervasive (diffuse) competition

**Pitch:** Under diffuse competition the failure isn't uniform across model tiers — our Phase 1.0 spot-check suggests a *stronger* model (Sonnet 4.6 vs Haiku 4.5) fails **earlier and more honestly**: it *refuses* ("inconsistent and unreliable", UNKNOWN) where the weaker model *confabulates* (emits wrong/multiple numbers), and its knee moves earlier, not later. If this holds on a capability ladder, "a better model is a better conflict-detector, not a more robust retriever (under diffuse competition)" is a counterintuitive, useful claim for anyone choosing models for long-context agentic work — and a caution that committed-accuracy benchmarks penalize appropriate refusal.

**Audience:** agent builders choosing model tiers; eval designers; long-context researchers.

**Dependencies:** synthesis §3.8 (provisional, n=9). Needs a fuller test — ≥3 models on a capability ladder, refusal-affordance control (does removing the explicit "reply UNKNOWN" change it?), ≥5 seeds, multiple (structure × similarity) cells. Cross-provider (DeepSeek) tiers would strengthen.

**Status:** filed 2026-06-04 from the Phase 1.0 Sonnet spot-check. Low confidence (45); re-evaluate after the fuller test. **Update 2026-06-13 (§1.8 length-extension, `results-length-extension.md`):** a DeepSeek capability-ladder data point landed — under **pure-length** stress (not competition), **v4-pro** holds the neutral needle (1.00@94k, 0.67@758k) while **v4-flash** is abstention-noisy (~0.4–0.7 across all lengths). Both fail by **abstention** (empty/`UNKNOWN`), never confabulation. So the capability gradient generalizes from competition-stress to **length-stress**, and the *stressor that triggers collapse* is itself capability-dependent (capable: competition-only; weak: competition + length). Still low-confidence (the fuller refusal-affordance-controlled test is unrun); but the cross-provider tier comparison the candidate wanted now has its first point.

**Adjacencies:** synthesis §3.8, §1.8, §5.2; Chroma model-capability finding (lower models rot earlier — but non-monotonic in size/recency); eval-design literature on refusal vs. accuracy.

---

## [CANDIDATE-CONTRIBUTION] Agentic self-generation: a structural accessibility advantage (≈ §1.8, not a new immunity)

**Original claim (tentative, filed 2026-06-12):** the diffuse-competition collapse documented in
*passive* settings (§1.8; arXiv:2506.08184) may **not** transfer to agentic tasks where the agent
**fetches** the needle itself — an "agentic immunity."

**Disposition: DEMOTED → INCONCLUSIVE 2026-06-14 — structural argument only (`results-4v2.md`, #4-v2;
corrected after the three-reviewer pass; #4(i) 60→15).** Five designs, **all held at full
seed-count** (0 mis-binds — exact-key binding to 953k; semantic role-binding N≤6; recency N=40;
two-phase rolebind N=16 buried to 37k; **and** the low-discriminability diffuse design built to
collapse). A 5-seed *pilot* of the low-disc design showed a seed-4 lure-capture (active=passive),
banked as "demonstrated ⊆ §1.8" — but it **did not replicate at 12 seeds** (§0.21; no temperature
control). So **no agentic collapse was induced** (a third inconclusive, after the chain null and
binding A/B). The claim survives only as a **structural argument**:

> **Agentic self-generation confers a *structural accessibility advantage*** — the value arrives
> fresh / recent / uniquely-labeled, an advantage §1.8's collapse regime lacks. It **sidesteps**
> wall-retrieval (a near-tautology: fetching ≠ retrieving from a buried wall) rather than refuting
> §1.8. **#4 ⊆ §1.8 — argued, not demonstrated** (we never induced a collapse to attribute).

**Prior-art to engage (prior-art reviewer, conf 88 — VERIFY firsthand before citing):** the
"self-generated content is recalled better" intuition is the cognitive-psych **generation effect**
(Slamecka & Graf 1978) — cite it as the reference class to *distinguish from*: the human effect is
encoding-depth, any LLM "advantage" is purely token-position/recency/labeling (a transformer has no
memory of having generated anything — synthesis §1.4), which *strengthens* the "near-tautology, not
a novel cognitive immunity" honesty. So: **weaker than hoped** — not a separate mechanism, and not
even empirically demonstrated. The genuinely-novel agentic question (does tool-*retrieval* beat
in-context disambiguation under diffuse competition?) is the **RAG-vs-grep** debate (a later module),
using §1.8's own unique-answer needle ported to the agentic frame — the only route to a gradeable
collapse *rate* (the fuzzy-semantic cues here can't, §6b gradeable/luring tradeoff).

**Adjacencies:** synthesis §1.8; arXiv:2506.08184 (proactive interference); RULER (multi-key NIAH);
the RAG-vs-grep debate (Module later). Bonus harness artifact: the **stem-checker** (`shared_stems`)
+ the five reusable tiers.

---

## [CANDIDATE-CONTRIBUTION] Fix the return format to inline-detailed (and a measurement-honesty note)

**Pitch (CORRECTED 2026-06-14 after the three-reviewer pass).** The tempting story — "let the agent
pick a return format per call and it won't bother, so don't offer the choice" — **did not survive
review.** A *read-tools-only* tally suggested "models default to `detailed` everywhere"; the full
per-tool view (#6, `experiments/phase-1.1/results-6.md`) shows **all three models (v4-flash, v4-pro,
Sonnet 4.6, two families) DO use the choice — sensibly**: `concise` on the terminal `send_message`
(return unused), `detailed` on the consumed reads. So the choice is **not** unexploited overhead.
What's left is a narrower, still-useful claim: among *fixed* policies, **inline-detailed dominates**
(100% success, lowest call-count-confounded cost); an always-attach **handle-block is overhead**; and
**concise-pruned breaks** any downstream needing the handle. Plus a sharper methodological story — *a
behavioral signal is only confound-free if you tabulate every decision, not a subset* (the original
error). The contribution is now the **fix-to-inline-detailed guidance + the measurement caveat**, not
"agents ignore the choice."

**Audience:** agent/tool builders; the "writing effective tools" practitioner audience (Anthropic
tool-design blog); MCP server authors.

**Dependencies:** #6 (now **48**). To strengthen: an **economy-pressure prompt** ("use concise unless
you need the ids") to test whether the choice is *beneficial* (not just used), and a
**call-count-controlled** task so the token-efficiency ranking becomes a clean number.

**Status:** filed 2026-06-14 from the #6 sweep + anchors; **reframed same-day after the reviewer pass
inverted the behavioral claim**. Confidence-adjacent to #6 (**48**). Caveat: success didn't
discriminate (easy task) and the behavioral pillar inverted — the durable part is the fixed-arm
ranking, not a claim about whether to offer a choice.

**Adjacencies:** the Anthropic "writing effective tools for agents" blog (Module 2 source); §3.3
(tokens/KV-cache economy); the five reusable tool-use tiers + the per-arm A/B/C/D `make_tools`.
