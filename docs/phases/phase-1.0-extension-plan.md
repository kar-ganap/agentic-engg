# Phase 1.0 Extension — Cross-Provider Validation + Deep Context-Rot Sweeps (plan)

> Captures the next-phase work designed conversationally on 2026-06-04 so the
> reasoning isn't lost. **Deepens Module 1 context-rot** (it is *not* Module 2 /
> tools). Per workflow rule 3 ("only plan the current phase in detail"), the
> settled designs are recorded at design-level; the rest stays headline. **Open
> sequencing question:** run this as a Phase 1.0 *extension* before Module 2, or
> interleave — decide at the Phase 1.0 close (watch the sandbox-pull gate: don't
> over-polish one module).

## Why this exists

Exercise A established (on Claude) that **diffuse competition collapses confident
retrieval; competition, not length, drives the knee** (`results.md`, §1.8/§5.2).
Three things remain to make it robust and deep, and they share an enabler
(DeepSeek as a validated cheap workhorse):
1. **External validity** — does it hold off the Anthropic family? (discharges
   §1.8 retraction clause (b) cross-family leg)
2. **Structure generality** — does it hold on the retrieved-document regime that
   *is* our own substrate? (the plan's promised 2nd structure class)
3. **Mechanism decomposition** — is it noise *potency* or noise *count*? where's
   the benign pocket? (the deepest §1.8 probe)

## Key design insight: migration *is* validation (two birds)

Do **not** treat "validate on DeepSeek" and "move to DeepSeek" as separate tasks.
Moving requires porting the harness + re-validating the measurement on DeepSeek's
behavior — and *that re-validation run is the cross-provider external-validity
check.* One piece of work, three payoffs: discharges §1.8(b); counters Anthropic
selection bias (§0.8); unlocks the cheap workhorse for the expensive sweeps.

## Sequencing

**Prereq (done at Phase 1.0 close, on Claude — validate instrument on home turf
first):** clean-essay baseline (instrument reproduces Chroma) + realism spot-check
+ Exercise B. *Don't port a possibly-broken instrument.*

**Step 1 — DeepSeek migration = cross-provider validation.**
- Build a provider adapter: OpenAI-format messages; **no `count_tokens` endpoint**
  → need a tokenizer or a calibrated estimate (real work, not free).
- **Re-validate the measurement** on DeepSeek: it hedges/refuses in *its own*
  phrasings → re-run the `committed`-detector audit (the §0.11 / Sonnet-detector-
  transfer work, redone for a new family; the offline part is cheap). Confirm the
  `usage`/cache fields exist and map (Exercise-B instrumentation may need adapting).
- Replicate the **headline diffuse / neutral / localized** cells on DeepSeek.
  → cross-provider replication; §1.8(b) discharged (or §1.8 demoted if it fails).

**Step 2 — DeepSeek workhorse + Claude spot-anchors.**
Run the expensive sweeps cheaply on DeepSeek, anchoring a few cells on Claude
(inverse of Exercise A: DeepSeek primary, Claude spot — because §0.8 says
*magnitudes don't transfer*, so anchor, don't assume).

## The deep sweeps

### (4) `research_doc_stream` — second structure class (our substrate)
- **Answers:** does the finding generalize across *structure* (prose passages vs
  tool-call JSON)? It's the closest analog to Stance itself (a research agent
  reading retrieved docs) → most decision-relevant cell. Prose competitors raise
  the similarity floor → prediction: rot ≥ `tool_call_stream`. Speaks to RAG-vs-grep.
- **Build:** implement `research_doc_stream` in `haystack.py` (currently
  `NotImplementedError`). Filler = P&P passages as neutral "documents"; competitors
  = catalog-style passages re other manuscripts; needle = a passage; optional
  reasoning-note interleaving.
- **Runs:** neutral/localized/diffuse × 1k–100k × 3 depths × 5 seeds, low-sim.
  DeepSeek workhorse + a Claude anchor (≥1 diffuse + neutral cell) for comparability.
- **Carries the clean-essay baseline's cousin:** if a Claude anchor of (4) runs,
  the essay baseline can ride alongside it; otherwise the baseline stays at close.

### (5) Relatedness sweep — DECIDED: choice B (drop same-item), D later
- **Answers:** is rot driven by competitor *potency* (per-item similarity) or
  *count* (mass)? Where's the H_A benign pocket (P3)? Holds **count fixed**, varies
  **per-competitor relatedness** → the cleanest §1.8 count-vs-potency decomposition.
- **The relatedness ladder** (value-format held constant — all catalog-shaped — so
  only routing/binding difficulty varies):

  | level | matches | example competitor |
  |---|---|---|
  | R0 off-domain | format only | `The part number for the Stratus compressor is QX-4410-PP.` |
  | R1 same-domain, diff attr | +domain | `The storage box number for the Halcyon manuscript is 2228.` |
  | R2 diff entity, same attr | +attribute | `The catalog number for the Halcyon manuscript is BF-1573-NT.` (current diffuse) |
  | R3 name-confusable entity | +near-entity | `The catalog number for the Meridian Codex is RX-2841-MM.` |

- **Decision 1 — R3 gated behind a short-context smoke test:** a 1k-context model
  must still answer correctly at R3, else the decoy breaks answer *uniqueness*
  (confounds competition with genuine ambiguity) → dial back.
- **Decision 2 — choice B (drop same-item-attribute distractors):** the same-item
  decoys live on the orthogonal *attribute-routing* axis; keeping them (choice A)
  leaves R0 potent (entity-matched) so R0 ≠ neutral and the benign-pocket test
  breaks. B = pure single-axis entity-relatedness ladder → R0≈neutral valid.
  **D later** (two-factor: ladder × same-item present/absent) is the rigorous
  follow-on; B *is* D's same-item-absent arm, so nothing is wasted.
- **Verdict logic (count fixed):** knee moves right as relatedness drops ⇒
  **potency** drives it = §1.8 confirmed + locates H_A pocket. Knee flat across
  relatedness ⇒ **count/mass** drives it ⇒ partially challenges §1.8 (more
  surprising, more publishable).
- **Runs:** diffuse only, R0–R3 × ~4 lengths (knee region) × 1–3 depths × 5 seeds,
  DeepSeek + Claude anchor. Deliverable: knee/slope **vs relatedness** dose-response.

### Density sweep — de-knob the `diffuse_density=0.3` caveat
- **Answers:** how does the knee move with competitor density ρ (count ∝ ρL)?
  Turns the "0.3 is a knob" caveat (results.md) into a curve. Complements (5): (5)
  varies potency at fixed count; this varies count at fixed potency → together they
  fill the `ρL · exp(s)` plane.
- **Runs:** diffuse, ρ ∈ {0.1, 0.3, 0.5, 0.7} × knee-region lengths × seeds.

## Cautions (carry forward)

- **§3.8 capability ladder is within-family.** Haiku→Sonnet was clean; appending
  DeepSeek tiers **confounds capability with family/architecture**. For §3.8
  specifically, stay within a family OR treat *family* as an explicit factor — do
  not just bolt DeepSeek onto the ladder.
- **DeepSeek instrumentation debts:** no `count_tokens` (tokenizer/estimate); the
  `committed` detector is Haiku/Sonnet-tuned (re-audit on DeepSeek phrasings);
  `usage`/cache-field shape may differ (Exercise-B price table needs a DeepSeek row,
  verified against DeepSeek pricing).
- **§0.8 always:** DeepSeek gives *direction*; anchor *magnitudes* on Claude.

## Throughline properties

Advances **contribution** (Property 4): the localized↔diffuse regime distinction +
the potency-vs-count decomposition + structure-generality are the publishable core
(`contribution-candidates.md`). Cross-provider replication is what makes it a claim
about *models*, not about Claude.

## Cost (rough, headline)

DeepSeek is the cheap workhorse → the expensive sweeps drop ~5–10× vs Claude.
Migration adapter + re-validation is mostly engineering time + a small replication
run. Claude anchors are a few cells each. Detailed costing at phase entry, not now.
