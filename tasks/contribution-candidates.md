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

**Status:** filed 2026-06-01. **First data landed 2026-06-04** (`experiments/phase-1.0/results.md`): the **localized↔diffuse** distinction is the sharp, defensible contribution — Chroma measured *localized* competition (fixed distractor count); agentic contexts are *diffuse* (competitor count ∝ length). We show diffuse competition collapses confident retrieval while localized/neutral hold a passband to 100k, on the same substrate, cross-model (Haiku + Sonnet) — i.e. **competition, not token count, governs onset**. The realism check (templated vs LLM-generated competitors) adds a **potency dose-response**: the collapse *knee* scales with competitor relatedness/composition (~10k saturated-templated → ~50k natural-mixed, still collapsing by 100k) — so the result is not a templating artifact, and "agentic free budget" is a *potency-dependent* quantity, not a single number. Strengthens the pitch from "characterize structures" to "name and measure the regime Chroma's design didn't cover, with a dose-response." Re-evaluate after `research_doc_stream` + the §5 relatedness sweep + cross-provider (DeepSeek) replication.

**Adjacencies:** Chroma *Context Rot*; synthesis §1.3 (lower-bound), §3.4, §3.6, §5.1, §1.8, §5.2; the curriculum's Module 1 context-rot exercise.

---

## [CANDIDATE-CONTRIBUTION] Capability-dependent failure modes under pervasive (diffuse) competition

**Pitch:** Under diffuse competition the failure isn't uniform across model tiers — our Phase 1.0 spot-check suggests a *stronger* model (Sonnet 4.6 vs Haiku 4.5) fails **earlier and more honestly**: it *refuses* ("inconsistent and unreliable", UNKNOWN) where the weaker model *confabulates* (emits wrong/multiple numbers), and its knee moves earlier, not later. If this holds on a capability ladder, "a better model is a better conflict-detector, not a more robust retriever (under diffuse competition)" is a counterintuitive, useful claim for anyone choosing models for long-context agentic work — and a caution that committed-accuracy benchmarks penalize appropriate refusal.

**Audience:** agent builders choosing model tiers; eval designers; long-context researchers.

**Dependencies:** synthesis §3.8 (provisional, n=9). Needs a fuller test — ≥3 models on a capability ladder, refusal-affordance control (does removing the explicit "reply UNKNOWN" change it?), ≥5 seeds, multiple (structure × similarity) cells. Cross-provider (DeepSeek) tiers would strengthen.

**Status:** filed 2026-06-04 from the Phase 1.0 Sonnet spot-check. Low confidence (45); re-evaluate after the fuller test.

**Adjacencies:** synthesis §3.8, §1.8, §5.2; Chroma model-capability finding (lower models rot earlier — but non-monotonic in size/recency); eval-design literature on refusal vs. accuracy.
