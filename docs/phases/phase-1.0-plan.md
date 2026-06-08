# Phase 1.0 — Context Engineering (Module 1)

**Stage:** 1 (Crawl)
**Weeks:** 2–3
**Module:** Module 1 (Context Engineering & Context Management) — *the spine*
**Branch:** `phase-1.0-context-engineering`
**Critical phase boundary?** **YES** (PLAN.md: "context-engineering spine commitment") → three-reviewer pass required at close.

> Full approved plan archived at `~/.claude/plans/snuggly-launching-graham.md`. This is the repo-template version.

## Objective

Produce the **first experimental evidence** for the context-engineering positions filed (on theory) in `docs/synthesis.md` — generated on our own substrate — and begin the Property-4 contribution candidate (context rot on realistic agentic structures). Move confidences on §1.1, §1.8, §5.2 from literature/mechanistic to experiment-backed.

## Scope

**IN (two exercises, both deep):**
- **Exercise A — Context-rot study (VERY DEEP):** tests §1.8, §5.2, §3.6, §3.4. Extract `(ceiling, knee, slope)` + passband-existence per condition across a clean baseline + **two** agentic structure classes (tool-call/observation first, research-agent second).
- **Exercise B — KV-cache instrumentation (DEEP):** tests §1.1, §3.3. Anti-pattern break/restore.

**DEFERRED (explicit, not waterfall):** §3.7 (tool-result clearing/compaction), §3.2 (recitation), §3.5 (full disentangling), conversational structure class, SELF-ROUTE (→ M8).

**Budget:** ~$50. Haiku 4.5 primary; cap haystacks ~100k tokens (§5.2 — agentic rot is early); spot-check Sonnet 4.6. Log every run in `tasks/spend.md`.

## Pre-registered success criteria

- [ ] Context-rot harness (`accuracy.py` + `haystack.py` + `runner.py`) built, tested, re-pointable (§0.7).
- [ ] A-baseline reproduces Chroma's mechanism on our setup: clean → passband exists; distractors → passband shrinks/vanishes.
- [ ] A-structure-1 (tool-call/obs): `(ceiling, knee, slope)` + passband? measured.
- [ ] A-structure-2 (research-agent): same, on the distractor-rich structure.
- [ ] A-§3.4: failure-shaped vs random padding compared.
- [ ] B: cache instrumentation added; anti-patterns measurably drop hit-rate; restore recovers it; cost/latency delta quantified.
- [ ] `make check` green.
- [ ] Predictions pre-registered (in run-script headers) before each run.
- [ ] Positions updated in `docs/synthesis.md` with experimental Evidence + confidence moves.
- [ ] Retro + `/learn` + three-reviewer pass.

## Task backlog (priority-ordered; core = 1–4)

1. **Infra:** `src/stance/eval/accuracy.py`, `src/stance/rot/haystack.py`, `src/stance/rot/runner.py` (+ tests). TDD.
2. **A-baseline:** clean vs. distractor on essay haystack → validate harness.
3. **A-structure-1:** tool-call/observation stream.
4. **B:** KV-cache instrumentation + anti-pattern break/restore.
5. **A-structure-2:** research-agent stream.
6. **A-§3.4:** failure-shaped padding.
7. *(stretch)* Sonnet validation; more conditions.

Items 5–6 may slip to a Phase 1.0 extension without leaving the phase incomplete.

## Division of labor (learning-first)

- **User (load-bearing):** needle/question design; structure-class construction params; operational "knee" definition; anti-pattern choices; accuracy criterion; reads results; updates positions/confidences.
- **Claude (plumbing):** builder mechanics, runner loop, JSONL logging, `cache_control` wiring, matcher boilerplate, test scaffolds.
- **Pair:** curve interpretation + position updates.

## Out of scope (deferred to specific later phases)

- Compaction primitives + tool-result clearing → §3.7, Phase 1.0 extension / 1.1.
- Recitation cadence → §3.2.
- Full §1.2/§1.7 three-arm disentangling → §3.5.
- Evidence-graph schema (`Claim`/`Evidence`/`Position`) → Phase 2.0 (synthesis.md remains the holding pen).
- Full eval harness (rubric/judge/trajectory) → Phase 2.1; this phase builds only the deterministic accuracy slice.

## Validation gate

Per CLAUDE.md § Validation Gates. Critical-boundary three-reviewer pass mandatory (method-rigor reviewer scrutinizes the rot experimental design: seeds, deterministic eval, knee definition). Throughline gate: advances the **contribution** property.

## Retro

→ `docs/phases/phase-1.0-retro.md` (create at close, with synthesis-section anchors).
