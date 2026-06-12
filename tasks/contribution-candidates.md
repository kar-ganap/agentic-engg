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

**Status:** filed 2026-06-04 from the Phase 1.0 Sonnet spot-check. Low confidence (45); re-evaluate after the fuller test.

**Adjacencies:** synthesis §3.8, §1.8, §5.2; Chroma model-capability finding (lower models rot earlier — but non-monotonic in size/recency); eval-design literature on refusal vs. accuracy.

---

## [CANDIDATE-CONTRIBUTION] Agentic self-fetched values resist diffuse rot

**Claim (tentative):** the diffuse-competition retrieval collapse documented in
*passive* settings (§1.8; proactive-interference / WM-limits, arXiv:2506.08184) may
**not** transfer to agentic tasks where the agent **fetches** the needle itself.
Phase 1.1 #4 chain sweep: DeepSeek-v4-flash kept 55/55 correct-use with the needle
(an `account_id` it obtained via a labeled `get_order` call) buried under ~186k
tokens and 8 same-format competitors — recalled from memory, no re-fetch.

**Why it might be real:** an actively-fetched value sits in a structurally findable
tool_result ("the account I looked up for this order"), unlike a needle anonymously
buried in prose. Active acquisition + structure may immunize against the burial that
collapses passive retrieval — the agentic-vs-passive distinction.

**Status:** filed 2026-06-12 from the #4 chain sweep (`experiments/phase-1.1/results.md`).
**Confounded** — the competitors weren't same-frame rivals (§0.20), so it's inconclusive
whether this is immunity or just absent rivalry. Needs: (1) same-frame rival competitors,
(2) an active-vs-passive A/B, (3) a Claude spot-anchor (§0.8). Do not claim until separated.

**Adjacencies:** synthesis §1.8 (clause b — cross-setting generality), §3.6; the WM /
proactive-interference literature (passive setting); RULER (multi-key NIAH, passive).
