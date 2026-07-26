# Phase 2.0 — Reasoning Patterns + Evidence-Graph Schema (Module 3) — Retro

**Closed:** 2026-07-25 (experimental work concluded 2026-07-25)
**Branch:** `phase-2.0-reasoning-loops` (Thread B; Thread A merged separately, PR #6)
**Critical phase boundary?** **YES** — a position commitment (`reasoning-pattern` → candidate 62) **and** a framework/taxonomy adoption (bias×epistemic-structure), plus the evidence graph becomes the project's persistence spine. → three-reviewer pass required before merge.

## Summary

Phase 2.0 had two threads. **Thread A** built the evidence-graph schema v0 (Claim/Evidence/reified-Support-with-Toulmin-warrant/DecisiveProbe/Leg/Retraction/Position; append-only latest-wins → confidence trajectory for free) and seeded it — the persistence spine the whole project now writes to (merged PR #6). **Thread B** used Module 3 (reasoning patterns) as the first real *consumer* of that spine: build a position-forming harness (sampler → 4 arms → fuzzy grader → runner, TDD, `make check` 229) and run the pre-registered comparison of reasoning loops.

**The headline is the finding's shape, and how the experiment earned it.** The prereg bet a single pragmatic winner (which loop to wire in) + an interaction bonus. The experiment's *stimulus design* had to be corrected twice before it could test anything — and the corrections are the substance:
1. **First §1.8 sweep found nothing** because the §0.22-style "silent" distractors were trivially triaged as off-topic (plan_execute read exactly the 3 targets, 96%). → **§0.25**: distractors must be **on-axis, non-decisive-by-explicit-flaw**.
2. **Redesigned §1.8 fired** (baseline bimodal-collapses to length; plan-execute sidesteps) — but a single debate.
3. **Cross-debate (§1.1, §3.8) refused to replicate** — and *that* was the real result: **there is no universal best pattern; effectiveness = alignment between a pattern's inductive bias and the debate's epistemic structure.**

The discipline did its job repeatedly: the §0.17 smoke caught two harness bugs (truncation, markdown-labels) before the pilot; the pilot's `evidence_used`-composition check caught the triage confound before any curve was believed; the cross-debate sweep dissolved the single-winner claim before it was banked. The banked position is a **taxonomy**, not a recommendation.

## Concept-stream output (synthesis-anchored, pre-review)

- **§1.9 — No universal best reasoning pattern; match the pattern to the debate's epistemic structure (conf 62, candidate; was prereg hypothesis 40).** Legs: no-universal-winner **68** / bias×structure **62** / reflection-systematic-caution **62** / §1.8-dilution-sidestep **70** / regime-taxonomy **40**. Mechanisms confirmed via confidence+stance data; the 3-cell partition is n=1 debate/regime (hypothesis). Graph: `reasoning-pattern` + `ev-reason-{sd,ts,cf,refl}` (4 warranted support edges). (`results-reasoning.md`.)
- **§1.8 / §1.1 / §3.8 used as *test debates*, not moved as content positions** — but the sweep characterized each: §1.8 = dilutable-convergent (rot = dilution-to-length); §1.1 = robust-single-fact (cache ~7× undilutable → no rot; baseline stance 4/4/4); §3.8 = hedge (rot = overclaiming). These are experimental readings of the *reasoning task over* each debate, not new evidence on the debates themselves.
- **Prereg trajectory:** single-winner bet **refuted**; ranking (react ≥ plan) **refuted** (plan > react on §1.8, react > plan on §1.1, both lose on §3.8); reflection (< reputation) **refined** to *systematic caution* (hurts confident tasks, wins hedge tasks).

## Decisions made

| Decision | Choice | Why |
|---|---|---|
| Distractor design | **§0.25: on-axis + non-decisive-by-flaw** (replaces "silent") | silent/off-axis distractors are triaged → no competition → nothing to measure |
| `reasoning-pattern` disposition | **hypothesis 40 → candidate 62 (taxonomy)** | winner flips across 3 debates with confirmed mechanisms; capped by n=1/regime + single-provider + unvalidated grader |
| Judge model | **Sonnet-5 (anchor), arms DeepSeek-v4-flash** | grading noise feeds the DV; cost is one call/run; uniform judge doesn't bias the between-arm comparison |
| Rubric | **fuzzy 5-criterion 0–20** (stance/calibration/retraction/evidence-use/epistemic-humility) | crisp/oracle grader would smuggle in reflection's home edge (prereg precondition) |
| plan-execute execution | **P1 (harness batch-reads the plan)** | non-adaptivity must be *structural*, else it silently re-admits react's adaptivity |
| reflection critique | **generic (not rubric-guided)** | handing it the rubric = teaching-to-the-test (mirror of the crisp-grader smuggle) |
| Grading key | **credit the reasoning move** (discount-the-flawed / hold-the-hedge) | the redesigned task tests flaw-detection; a stale key wouldn't reward it |
| Raw sweep data | **committed** (deviates from 1.1 convention) | backs a committed position + isn't regenerable (model non-determinism) |
| Three-reviewer pass | **run at this close** | position commitment + taxonomy adoption — see § below |

## Validation gate

| Gate | Status |
|---|---|
| Tests / `make check` (ruff + mypy --strict + pytest) | ✅ green, 229 tests |
| Evaluation criteria adjudicated | ✅ the control (rot) was *made* to fire only after §0.25; cross-debate honestly refuted the single-winner bet |
| Reproducibility | scripts + pinned seeds + committed raw JSONLs + `results-reasoning.md`; graph regenerates via append scripts |
| Pre-registration | `reasoning-pattern` prior (40) + legs + retraction locked 2026-06-29 (`prereg_reasoning.py`) before any run |
| Retro written | this file |
| `/learn` written | ✅ `tasks/lessons.md` §0.25 (+ [DELETE] considered below) |
| Three-reviewer pass | ⬜ pending — see § below |

## Three-reviewer pass outcome (the load-bearing event of the close)

*(to be filled after the pass — three clean-context Opus reviewers: method-rigor / framing-stress / prior-art; ≥80 filter; author verifies every finding firsthand before acting.)*

## Method wins (process-stream, → `tasks/lessons.md`)

- **§0.25 (new)** — to induce competition, distractors must be **on-axis + non-decisive-by-explicit-flaw**; a "silent-on-the-axis" distractor guarantees triage-ability (the whole first sweep measured who-triages-best). Generalizes §0.20 (presence ≠ rivalry).
- **Smoke catches what units can't (again, §0.4).** The §0.17 smoke caught two real bugs the fake-client tests couldn't: DeepSeek reasoning-token truncation (`max_tokens` too tight) and markdown-wrapped labels (`**STANCE:**`). *The instruction ("no markdown") is not reliable — the parser must be.*
- **Diagnose the confound before believing the curve.** The pilot's flat result wasn't "no effect" — the `evidence_used`-composition check (plan_execute 96% target citations) revealed a triage artifact. A per-decision composition check gates the aggregate read (cf. §0.23).
- **The grading key must credit the reasoning move the task tests**, not just the answer — else the DV silently ignores the skill under study.

## Rule changes (`/learn`)

- **[MODIFY]** the distractor-design criterion: "silent on the axis" (phase-2.0 plan, loosely tagged §0.22) → **§0.25** "on-axis + non-decisive-by-flaw." Fixed the stray §0.22 cross-references (lessons §0.22 is rescue-progression — unrelated).
- **[ADD]** *(candidate for CLAUDE.md Code Rules, pending review)* store raw model outputs (arm + judge) per experiment run for audit — it turned the grade-truncation diagnosis into a one-line lookup.
- **[ADD]** *(candidate)* when an experiment's stimulus is redesigned to test a new skill, update the grading key in the same commit so the DV rewards that skill.
- **[DELETE]** none. The superseded "silent" criterion stays in the trajectory (plan + §0.25's note) — the correction *is* the learning; deleting it would erase why §0.25 exists.

## Friction (where discipline slipped / cost time)

- **Two failed stimulus designs before a testable one** (silent → §1.8-only → cross-debate). Not wasted (each was diagnosed, not guessed), but the §0.25 tension (non-decisiveness ↔ selection-confusability) should have been anticipated from §0.20.
- **A sloppy stash-proof shell command corrupted `arms.py`** (stray `perl` edit; restore brought back the corrupted copy). Recovered; the lesson is to back up *outside* the repo and restore by copy (used thereafter).
- **`synthesis_ref` mis-set to "3"** then corrected to §1.9 (a duplicate 62 in the trajectory) — a metadata slip, caught in the close.
- **Repeated E501 churn** on new experiment files — line-length friction, mechanical.

## Throughline property progress

- **Property 2 (decision-support query surface) — advanced.** `show_graph.py` is a working read surface (summary table + per-position subgraph); it was the primary lens for reviewing the seeded + moved positions. A proto, but real.
- **Property 3 (position re-evaluation) — exercised.** The graph's append-only latest-wins Position moved `reasoning-pattern` 40 → 62 with a preserved trajectory and pre-registered retraction — the anti-drift machinery did real work (the prereg's ranking leg's retraction *fired*).
- **Properties 1 (ingest) / 4 (contribution) — untouched** this phase (ingest-backlog remains the manual stand-in). Two of four moved — no gate flag, but Stage 2 must keep surfaces advancing.

## Carry-forward

- **Cross-provider replication** — the whole taxonomy is DeepSeek-arms + Sonnet-judge; run arms on a second family (the §0.8 anchor pattern) before firming past candidate.
- **≥2 debates per regime** — the 3-cell partition is n=1/regime; a second dilutable / robust-fact / hedge debate each would move regime-taxonomy off 40.
- **Human-validated grader** — the fuzzy rubric is an unvalidated instrument; a small human-agreement check removes that caveat.
- **The §0.25 tension is general** — any future competition/interference stimulus (RAG-vs-grep, memory) must be on-axis-flawed, not silent, or it won't induce the phenomenon.
