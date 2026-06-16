# Phase 2.0 — Reasoning Patterns (Module 3) + Evidence-Graph Schema v0 (Plan)

## Context

Stage 1 (Crawl) is closed and merged. Phase 2.0 opens Stage 2 (Walk) and is the **first phase
where the project's unifying data model — `Claim` / `Evidence` / `Position` — gets BUILT, not just
used in prose.** Today positions live only as markdown in `docs/synthesis.md` (~8 §1.x entries, a
"holding pen"), which causes a recurring sync-bug (confidence copy-pasted across synthesis / retros /
candidates → the stale "60"). This phase also makes the **substrate transition** the curriculum calls
for: from synthetic context-rot tasks to **real "form a position given this evidence" tasks**, which
is exactly what the reasoning-pattern comparison runs on. The schema is the **persistence spine every
later throughline surface reads/writes through** (ingest → appends Evidence; query → reads Positions;
re-evaluation → walks stale Positions; export → serializes Positions). Architecture reference:
`docs/conceptual.md` (Evidence/Position/Interface layers; append-only evidence, mutable positions,
confidence first-class). Curriculum: `Agentic_Engineering_Curriculum.md:106–126`; spec: `PLAN.md:96–102`.

## Decisions locked (with user, 2026-06-15)

- **Storage:** JSON/JSONL + frozen dataclasses (house style — `domain.py`/`events.py`; greppable,
  no new dep, "keep it simple"). **SQLite deferred to Phase 2.2** (query surface / Property 2).
- **Source of truth:** **seed + graph-canonical for the seeded set.** Hand-author ~3–5 seed Positions;
  for those, the graph owns the structured fields; `synthesis.md` keeps the long-form prose and cites
  the record id. Remaining §1.x positions migrate incrementally in later phases. (Sync-bug fixed for
  the seeded set, deferred for the rest.)
- **User-owned at execution (learning-first):** the seed Position records + the reasoning-loop
  *position-formation logic*. I scaffold the seams, plumbing, harness, tests. The schema *fields* were
  co-designed and are now locked (below).

## Two coupled threads + sequencing

**Schema v0 first** (so there's a graph to reason over) → **reasoning comparison evaluated on graph
operations** (the position-forming suite) → wire the winning loop into the spine.

## Thread A — Evidence-graph schema v0 (BUILD)

**I scaffold:** `src/stance/graph/{__init__,models,store}.py` + `tests/test_graph.py`. Append-only
invariant for `Claim`/`Evidence`/`Support`/`DecisiveProbe`; **`Position` stored append-only with
latest-wins** so the confidence trajectory falls out for free. TDD, failing-first; stash-proof one
invariant test.

**User authors:** the ~3–5 seed records (recommended **§1.1+#3, §1.8, §3.8** — they exercise legs,
the `qualifies`/`subsumes` edges, a `tension_with`, and a contradicting-evidence `Support`).

**v0 explicitly defers:** the "portable-evaluator" decomposition (conclusion/applicability/evaluator,
`conceptual.md`); full migration of all ~8 positions; SQLite; Toulmin *backing*; **mechanism-data**
(the evaluator-output layer → note-string for now, first-class in v1); a `Tension` node (§2) and a
`Framing` node (§5 stays prose).

**Two design additions baked in (whiteboard 2026-06-15):**
1. **Warrant (Toulmin).** The support edge is reified as a `Support` record carrying a `warrant` —
   the inferential link ("why this evidence licenses this stance," usually the **mechanism**) +
   `polarity`. Mapping: *qualifier→confidence*, *rebuttal→preconditions*; `retraction` is the Popper
   overlay Toulmin lacks → the schema is **Toulmin + Popper.**
2. **`DecisiveProbe` (the crux / value-of-information).** The highest-VoI *uncollected* datum per
   position (the experiment that would most likely *toggle* it) + why it's uncollected. Its own node;
   hand-estimated VoI; guard against sprawl (must plausibly *toggle*). Seeds from existing deferred
   items (#3 Claude anchor, §1.8 clause-b). Symmetry: `Evidence` = data we *have*; `DecisiveProbe` =
   data we most *want*. Feeds the Property-1 ingest filter + Property-3 re-eval.

**v0 SCHEMA — LOCKED with user 2026-06-15:**
```python
@dataclass(frozen=True)
class Claim:        # atomic proposition (append-only)
    id: str; text: str; kind: str            # proposition | finding
    evidence_ids: tuple[str, ...]
@dataclass(frozen=True)
class Evidence:     # backs/contradicts a claim (append-only)
    id: str; type: str                       # literature|mechanistic|experimental|analogous
    source: str; summary: str; strength: str  # direct|corroborating|lower_bound|contradicting
    claim_ids: tuple[str, ...]
@dataclass(frozen=True)
class Support:      # reified edge — carries the Toulmin WARRANT
    position_id: str; evidence_id: str
    warrant: str                             # WHY this evidence licenses the stance (the mechanism)
    polarity: str                            # supports | contradicts
@dataclass(frozen=True)
class Retraction:   # forward falsification trigger (Popper)
    direction: str; delta: int; condition: str; tags: tuple[str, ...]
@dataclass(frozen=True)
class Leg:          # sub-confidence split (e.g. §1.1 cache~90 / coherence~65)
    label: str; confidence: int; note: str
@dataclass(frozen=True)
class Position:     # stored append-only, latest-wins → confidence_history derived for free
    id: str        # "1.1","1.8","3.8"
    title: str; stance: str; confidence: int  # qualifier (headline; author-set, capped by weakest leg)
    legs: tuple[Leg, ...]                      # sub-confidence split ( () if none )
    status: str                               # hypothesis|candidate|active|demoted
    preconditions: tuple[str, ...]            # rebuttal/scope
    retraction: tuple[Retraction, ...]
    edges: tuple[tuple[str, str], ...]        # (kind,target): tension_with|qualifies|subsumes
    registered: str; updated: str
    demoted_reason: str | None; synthesis_ref: str
    # DEFERRED to v1 (evaluator layer, conceptual.md): mechanism_data_to_capture → note-string for now
@dataclass(frozen=True)
class DecisiveProbe:  # the crux / value-of-information node
    id: str; description: str
    would_move: tuple[str, ...]               # position ids
    expected: str                             # up|down|toggle
    why_uncollected: str                      # cost|capability|access|methodology-gap
    status: str; note: str                    # blocked|deferred|planned ; hand-estimated VoI
```

**Sufficiency test against real records (2026-06-15) — drove the locked shape:** loaded §1.1 / §1.8 /
§3.8 / §2.x / §5.x into the schema.
- **§1.x positions + §3.x hypotheses → `Position` (cleanly).** §3.x = a Position with
  `status=hypothesis`; contradicting literature (§3.8 vs *From Loops to Oops* / OpenAI-hallucinate)
  → `Support(polarity=contradicts)`; the mandatory affordance-control → `DecisiveProbe`.
- **`legs` ADDED** — §1.1's cache~90 / coherence~65 split (overall **capped by the weaker leg**;
  retraction needs *both* null) was force-fit by a flat int, and §1.1 is a seed → minimal `Leg`;
  headline `confidence` stays author-set (not auto-computed).
- **mechanism-data DEFERRED → v1** — §1.1's measurement spec is `conceptual.md`'s evaluator-output
  layer; note-string for v0.
- **§2.x tensions → a `Tension` node, DEFERRED.** Richer than a `tension_with` edge (resolution
  sketch + camps that are often *sources*, not yet our positions). `tension_with` is a placeholder;
  `Position` stays graftable so a `Tension` node adds later without rework.
- **§5.x framings → OUT of the graph (v0).** No single stance/confidence/experiment → they stay
  `synthesis.md` prose.
- **Bonus:** the inline #3 refinement maps to a separate `Position` + `qualifies` edge — the schema
  is *cleaner* than the prose here.

**Files:** `src/stance/graph/{__init__,models,store}.py`; `data/graph/*.jsonl` (seeds); `tests/test_graph.py`.

## Thread B — Reasoning-pattern comparison (Module 3 concept)

Implement a **no-loop baseline** plus **ReAct**, **plan-and-execute**, and **reflection** as variants
over the **same task suite**, then compare success / token-cost / latency
(`Agentic_Engineering_Curriculum.md` exercise 1 + the baseline control).

- **No-loop baseline (essential control).** Single pass: stuff the evidence set in context, ask for
  the position once (no tool-loop, no critique). Answers "does *any* loop beat just-asking?" and tests
  a **§1.8-linked hypothesis**: for large evidence sets, stuffing-it-all may trigger the
  diffuse-competition collapse, so a *retrieval* loop (ReAct, pulling evidence by graph-edge) could
  win *because* of rot — a pre-registrable prediction grounded in our own prior work.
- **Reuse, don't rebuild:** the tooluse loop scaffolding — `src/stance/tooluse/loop.py` (loop-guard,
  error-as-data), `events.py` (`CallEvent`/`RunRecord`/`EventLogger` tracing), `instrumentation`
  pricing, `eval`. The reasoning loops are agentic loops with **graph-read tools** (fetch evidence by
  topic/id) whose output is a `Position`.
- **Task suite = the substrate transition:** "form/update a position on debate X given this evidence
  set," drawn from the seeded graph. Small fixed evidence set per task for v0.
- **Metrics:** success (graded — a rubric / LLM-as-judge on the formed position; keep light, judge
  reliability is a Module-6/2.1 problem), token cost, latency. **DeepSeek v4-flash primary; Claude
  anchor** on a couple of capability-sensitive cells (§0.8).
- **User owns:** what "form a position" means as a loop, the grading rubric judgment, the
  interpretation of which loop wins when.
- **ToT on Game-of-24:** lighter, **time-boxed** side-experiment (exercise 2). Trim first if the
  phase balloons — synthetic, off the position-forming spine (no cheap partial-position evaluator →
  ToT's branch-and-evaluate is a weak fit for our task).

**Open items / coverage check (Jan-2026 survey arXiv:2601.12538 read 2026-06-15):** the menu maps
cleanly onto the survey's *foundational* layer (planning / tool-use / search); collective
(multi-agent), memory, and RL-post-training are exactly our deferred / out-of-scope layers — no
unknown primitive is being missed. Carried items:
- **Validator-driven feedback (best-of-N against the judge) — strong optional 5th arm.** Distinct
  from reflection (resample on a binary validator signal, **no language introspection**). We already
  have a grader in the loop → cheap fit, and a sharp contrast: *does language self-critique
  (reflection) actually beat brute resample-against-the-rubric?* Add if budget allows.
- **Self-consistency: optional only** — majority-voting *positions* is awkward (cluster/merge N
  stances).
- **Framing:** ReAct's "act" here is **graph-traversal over the evidence KG** (the survey's
  *structure-enhanced search*), not generic RAG.

**Files:** `src/stance/reasoning/` (loop variants + shared suite runner); `experiments/phase-2.0/`
(runner, safe-by-default `--go`; `results-reasoning.md`).

## Pre-registration (Substrate Discipline #1 — before running)

- Pre-register the **prior position** on "which reasoning pattern for position-forming tasks, and
  when," + its **retraction criterion**, before the comparison runs (user sets the confidence).
- **Controls (§0.20/§0.21):** a trivial task all loops pass (rig check); read the comparison curve
  only at **full seed-count**, not a pilot (the §0.21 lesson — sprung hard in 1.1).

## Verification

- `make check` green (ruff + mypy --strict + pytest): graph models/store/query + reasoning harness.
- TDD: failing-first for store/query; stash-proof a graph invariant test (per CLAUDE.md).
- Reproducibility: seed records committed; reasoning runs seed-pinned; cost from `response.usage` →
  `tasks/spend.md`.
- End-to-end before the full grid: seed the graph → run one position-forming task through one loop →
  produce + grade a `Position` (the e2e-smoke pattern from 1.1).

## Close

- Retro + `/learn`.
- **Three-reviewer pass: LIKELY required.** Per CLAUDE.md, *critical = a framework adoption OR a
  position commitment* — Phase 2.0 has **both** (the evidence-graph schema is a framework adoption;
  the reasoning-pattern choice is a position commitment), even though `PLAN.md`'s explicit boundary
  list names 2.2→2.3, not 2.0. Default to running it for the **schema design** at minimum.

## Throughline

- 2.0 builds the persistence **spine** (substrate for all four surfaces) but is **not itself a
  user-facing surface** — the first surface is Phase 2.1 (Property 3). The standing flag (2.1 must
  ship a runnable surface slice) holds; 2.0 makes it possible.

## Spend

- Reasoning loops (esp. ToT) are token-heavier than sweeps. ~$75/$100 cumulative used. **ToT is the
  main cost risk → time-box it.** A cap raise may be needed before 2.4 regardless.

## Out of scope (this phase)

SQLite + query surface (2.2); ingest loop (2.3); full migration of all positions; portable
evaluators; `Tension`/`Framing` nodes; the Opik-style self-repairing eval harness (Phase 2.1
territory — captured in `tasks/ingest-backlog.md`).
