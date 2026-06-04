# CLAUDE.md — Agentic-Engineering Project Conventions

> Entry point for any Claude Code (or other agent) session on this repository. Internal-voice. Humans should start with `PLAN.md` for the working plan or `Agentic_Engineering_Curriculum.md` for the source syllabus.

## Project Thesis

Build an **evidence-based position-forming assistant for agentic engineering** — a tool that helps the user form, defend, and update positions on the field's contested debates (single vs. multi-agent, RAG vs. grep, memory framework vs. filesystem, MCP/A2A choices, etc.) using both **source evidence** (papers/blogs/specs) and **experimental evidence** (own measurements). Unifying data model: `Claim` + `Evidence` + `Position`.

**Throughline bet:** designed for **years, not the 16-week curriculum**. The curriculum is the seed dataset; the substrate is the discipline itself. Four first-class design properties baked into specific weeks (see `PLAN.md`):
1. Stay-current ingest loop (Week 9 / Module 5)
2. Decision-support query surface (Week 8 / Module 6.5)
3. Position re-evaluation cadence (Week 7 / Module 6)
4. Contribution surface / export pipeline (Weeks 11–12 / Module 6B)

**Capstone deliverable:** a synthesis report (paper-equivalent) taking measured positions on every contested axis in the curriculum, produced *by* the tool — not separately.

**Working name:** TBD. Candidates: Praxis, Receipts, Anvil, Stance. Locking this week.

## Current State

- **Stage:** 1 (Crawl) — planning.
- **Most recent closed:** Phase 0.0 (foundations + instrumentation skeleton), closed 2026-06-01. See `docs/phases/phase-0.0-retro.md`.
- **Next phase:** 1.0 — Module 1 (Context Engineering). Plan TBD; see `tasks/todo.md` for the reading load.
- **Live docs:** working plan = `PLAN.md`; source syllabus = `Agentic_Engineering_Curriculum.md`; concept stream long-form = `docs/synthesis.md` (started 2026-06-01 with Manus reading session); process stream = `tasks/lessons.md`.

## Stage / Phase Model

Curriculum modules → phases. Each phase follows the lifecycle: **PLAN → TEST → IMPLEMENT → VERIFY → RETRO → `/learn`**. All six.

| Stage | Weeks | Modules | Theme |
|-------|-------|---------|-------|
| 0 — Setup | 1 | Module 0 (skim) | Foundations + instrumentation skeleton |
| 1 — Crawl | 2–5 | Modules 1–2 | Context engineering + tools (the spine) |
| 2 — Walk | 6–10 | Modules 3, 6, 6.5, 5, 4 | Reasoning, eval, LangGraph, protocols, multi-agent |
| 3 — Run | 11–15 | Modules 6B, 7, 8 | Coding agents + memory |
| 4 — Capstone | 16–18 | Integration | Synthesis report |

Phase IDs follow `Stage.Phase`: 0.0, 1.0, 1.1, 2.0–2.4, 3.0–3.3, 4.0. Plans live in `docs/phases/phase-X.Y-plan.md`. Retros live in `docs/phases/phase-X.Y-retro.md`. `/learn` outputs append to `tasks/lessons.md`. Full mapping in `PLAN.md` § "Stage / Phase mapping".

## Workflow Rules

1. **Plan mode for any 3+ step / architectural task.** Exercise-level code work defaults to plan mode. Reading / position-formation may stay conversational.
2. **TDD.** Code: failing tests first. Substrate work: falsifiable position + retraction criterion before adopting. Tests define "done."
3. **Only plan the current phase in detail.** Future phases stay headline-level — anything else is waterfall in disguise.
4. **Verification before "done."** "Would a staff engineer approve this?"
5. **Objective before subjective.** Automated/quantitative checks before qualitative review.
6. **Subagents liberally.** One task per subagent. Keep main context clean.
7. **Learning-first.** User writes load-bearing parts (raw loop, schema design, position-formation logic, design tradeoffs). Claude scaffolds plumbing. See memory `feedback-learning-first` for the operational contract.
8. **Autonomous bug fixing.** Just fix it. No context switch back to user.

## Code Rules

- **Always `uv`, never `pip`.**
- **Simplicity first.** Minimal code, minimal impact. No over-engineering.
- **No laziness.** Root causes only. No temporary fixes. Senior-developer standards.
- **Reproducibility.** Pin all parameters, seeds, model versions. Raw data is never modified. Token-budget logs and trace dumps are append-only.
- **Stash-based bug-fix proof** (from ccupa): stash fix → confirm tests fail → pop stash → confirm tests pass. Verifies the test catches the bug, not just that the bug is gone.
- **Demand elegance (balanced).** For non-trivial changes, pause and ask "is there a more elegant way?" Skip for simple fixes.
- **Secrets strictly from `.env`, never the shell.** All API keys/secrets load via `stance.secrets` (reads `.env` directly through `dotenv_values`; `os.environ`/`.zshrc` is never consulted; missing keys fail loud). Construct clients as `anthropic.Anthropic(api_key=stance.secrets.anthropic_api_key())` — never bare `Anthropic()`, never `load_dotenv()` into the process env. **`.env` must hold a project-scoped *personal* key; never copy a work or shared key into it.** *Trigger: without this, `load_dotenv()`'s no-override default lets a shell `ANTHROPIC_API_KEY` (e.g. a work key in `.zshrc`) silently win over `.env`, and a work account gets billed for personal experiments — it happened 2026-06-03 (lessons §0.10); with this, the project can only ever use the key explicitly placed in `.env`.*

## Substrate Discipline (curriculum-adaptation of experimental discipline)

1. **Pre-register positions.** Before adopting a position on a contested debate, write the position + the supporting evidence + the **retraction criterion** ("what evidence would change my mind"). No drift-by-default; positions are explicit commitments with explicit out-conditions.
2. **Report contradictions honestly.** A position that didn't hold up gets *demoted*, not deleted — the trajectory IS the learning. Old positions stay in the graph with their retraction reasons.
3. **Confidence is mandatory.** Every position records a confidence (0–100). Point stances without uncertainty are insufficient.
4. **Multiple evidence sources per position.** Combine literature + experiment where feasible. A position grounded only in one is flagged as such.
5. **Numbers regenerate.** Every experimental number maps to a versioned script in `experiments/`. No one-time scripts.

## Two-Stream Discipline

**Do not conflate concept stream and process stream.** Different lifecycles, different destinations.

- **Concept stream → the synthesis report (paper-equivalent).** Lives in the evidence graph (`Claim` / `Evidence` / `Position` records) + `docs/synthesis.md` (long-form draft) + phase retros anchored to synthesis sections. Aggregates into the capstone report.
- **Process stream → discipline that outlives this project.** Lives in `tasks/lessons.md`. Rule changes, where discipline slipped and why, tooling friction, working-style refinements.

Cross-references allowed; content separated. Concept learnings *build up* into the report; process learnings *make the next phase cheaper* and outlast the curriculum.

## Validation Gates (per phase, mandatory)

1. **Tests pass** (code phases) or **all evaluation criteria met** (substrate phases).
2. **Lint / typecheck clean** (code phases): `make check` (= ruff + mypy --strict + pytest).
3. **Reproducibility check:** results regenerate from committed code + documented parameters.
4. **Retro written** with synthesis-section anchors.
5. **`/learn` written** with mandatory `[DELETE]` section (empty deletions allowed but must be explicit, not omitted).
6. **Three-reviewer parallel pass at critical phase boundaries** (ccupa-pattern). *Critical* = a position commitment, a framework adoption, or a phase closing out a throughline property. Spawn three Opus subagents in **clean-context** sessions, each given the synthesis + the phase artifacts only:
   - **Method-rigor reviewer** — does the method/measurement work?
   - **Framing-stress reviewer** — does the position survive contact with this phase's evidence?
   - **Prior-art-coverage reviewer** — would a domain reviewer raise an uncited reference class?

   **Confidence filter:** each issue is 0–100; report includes only ≥80; lower flags go to an appendix for author judgment.

## Throughline Property Gate (cross-cutting)

At every phase boundary in Stages 2–3, check progress on the four throughline properties (see PLAN.md). If a phase closes without advancing any of {ingest, query, re-evaluation, contribution}, flag in the retro and re-evaluate. **Sandbox pull is the primary failure mode** — the falsification test in PLAN.md is the long-horizon check; this gate is the short-horizon one.

## Git Lifecycle

- **Phase branches** off `main` (e.g., `phase-1.0-context-engineering`). Phase 0.0 stays on `main`.
- **User merges manually.** No force pushes.
- **No Co-Authored-By** lines in commits for this repo.
- **Small, focused commits.** Branch naming `phase-X.Y-<2-3-word-desc>`.
- **Prerequisite enforcement** (procedural, from ccupa):
  - No commit on a phase branch without a written plan it references.
  - No merge to `main` without retro + `/learn` written + (critical phases) three-reviewer pass.
- **Model tiering** for subagents: **Opus** for reviewers, **Sonnet** for task agents/architects, **Haiku** for test runners and mechanical checks.

## Meta-Rules (Governance of the Rule Set)

### Rule-admission test
Every proposed rule (here or in `tasks/lessons.md`) must include a one-line **trigger statement**: *"Without this, X; with this, Y."* If `Y == X`, the rule is decoration — move it to background context, not an active rules section. Vague rules ("be rigorous") fail; specific operationalizations ("write the retraction criterion before adopting a position") pass.

### Phase-completion `/learn` ritual
At every phase-complete declaration, *before* merge to `main`, write a `/learn` output covering:

- **What worked** (specific, not platitudes)
- **What caused friction** (where discipline slipped and why)
- **Rule changes proposed:** `[ADD]` / `[MODIFY]` / `[DELETE]` — **deletion is mandatory to consider** (empty `[DELETE]` allowed but must be explicit)
- **Synthesis cleanup proposed:** which positions to demote, merge, or sharpen
- **Tool / permission allowlist additions**
- **Throughline property progress** (which of the four moved this phase)

## Known Gotchas

*(Empty at Phase 0.0; accretes as the curriculum runs. Anticipated entries:)*

- **Sandbox pull** — without active resistance the tool becomes a curriculum companion that dies at Week 16. Counter: throughline-property gate at every phase boundary; six-month falsification test post-curriculum.
- **Velocity creep** — easy to slip back into ship-mode for the artifact and skip the load-bearing learning. Counter: `tasks/lessons.md` tracks where discipline slipped; learning-first principle is non-negotiable.

## Key References (in-repo)

| Path | Role |
|------|------|
| `PLAN.md` | Working plan: week-by-week, throughline-property mapping, Stage/Phase table |
| `Agentic_Engineering_Curriculum.md` | Source syllabus (the seed dataset) |
| `docs/conceptual.md` | Architectural framing (skeleton; defers to live docs) |
| `docs/synthesis.md` | Concept stream — long-form draft of the capstone synthesis (TBD, starts Module 1) |
| `docs/phases/` | Plans, retros, `/learn` outputs |
| `tasks/todo.md` | Current phase's open items |
| `tasks/lessons.md` | Process stream — discipline journal |
| `tasks/spend.md` | Compute spend tracking |
| `tasks/contribution-candidates.md` | `[CANDIDATE-CONTRIBUTION]` notes for the Property-4 export pipeline |

## If Continuing After a Gap

1. Read `tasks/lessons.md` (process state, carry-forward rules).
2. Read `PLAN.md` (current week + throughline-property status).
3. Read the most recent `docs/phases/phase-X.Y-retro.md` (concept state).
4. Check `tasks/todo.md` for the active phase's open items.
5. *Then* propose the next step.

**Sister projects to consult for conventions (not for content):**
- `../crit-thinking/CLAUDE.md` — predecessor template
- `../synthoracle/CLAUDE.md` — refined template
- `../epibench/CLAUDE.md` — current template (closest analog)
- `https://github.com/kambatla/ccupa/` — plugin-style conventions (governance, model tiering, prerequisite enforcement, parallel reviewers, stash-bug-proof)
