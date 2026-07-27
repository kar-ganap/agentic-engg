# Phase 1.2 Thread A — Tool selection + namespacing (position #2)

> Module-2's named central exercise, pre-registered as position **#2** in Phase 1.1, built
> (`src/stance/tooluse/tasks/selection.py`) but never run — a soft-defer that lapsed (lessons
> §0.26). Back-filled here. **DV = the model's FIRST tool choice == `expected_tool`** — a *mechanical*
> deterministic string match, no LLM judge. DeepSeek v4-flash primary + Haiku anchor.

## Pre-registration (before the run)

**Claim:** confusable-sibling *density* degrades first-tool selection accuracy; **namespacing**
(disambiguated `{entity}_search` names) recovers it. **Prior 55** (user-set). **Two-clause falsifier:**
(a) accuracy flat in `density_n` — no degradation (a #4/§0.20 "manipulation-didn't-bite" null); or
(b) namespacing does not recover accuracy at high N. Design: `density_n ∈ {0,1,3,5}` (pre-registered
in `phase-1.1-plan §293`; N capped at 5 by the sibling list) `× {pre-, post-namespace} × 5 seeds`.
Registered to the graph via `prereg_selection.py` (`tool-selection`, hypothesis, 55).

## Results

### Main sweep — selection accuracy by density × namespace (DeepSeek v4-flash)

| density N | 0 | 1 | 2 | 3 | 5 |
|---|---|---|---|---|---|
| **pre-namespace** | 1.00 | 1.00 | **0.00** | **0.00** | **0.20** |
| **post-namespace** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

(N=2 filled as a follow-up control — see below.) **0 "no-tool" picks** (the model always called a tool).
**Every** pre-namespace wrong pick — 9/9 at N∈{3,5}, and all of N=2 — was the *same* sibling:
`lookup_user`.

Neither falsifier clause fires: (a) there **is** degradation (1.00 → 0.00), and (b) namespacing
**does** recover (1.00 everywhere). But the shape refutes the *"density"* framing and demanded two
controls before I'd trust it.

### Control 1 — N=2 fill (is it count, or the attractor entering?)

Pre-siblings enter in order `[find_user, lookup_user, search_accounts, search_kb, search]`. So `find_user`
is present from N=1, `lookup_user` from N=2. The curve is a **step-function**, not a gradient:

- **N=1** (`find_user` only — shares the entity token "user", no verb match): **1.00**.
- **N=2** (`lookup_user` enters): **0.00**.

The collapse switches on the *instant* `lookup_user` appears, and `find_user` (equally entity-sharing)
never captures. So it is **presence of one specific sibling, not count**.

### Control 2 — verb-swap (is it that sibling's *name*, causally?)

The task prompt is *"Look up the customer {name}."* The correct tool `search_users` carries the best
*semantic* match in its **description** — *"Find a customer (user) by name"* — yet loses to `lookup_user`,
whose **name** matches the prompt verb "**look up**". Hypothesis: the model surface-matches the tool
**name** to the request verb, overriding the description. **Causal test:** move the "lookup" token onto
the *correct* tool (`search_users → lookup_users`, ex-attractor `lookup_user → search_user`); hold the
prompt, the entity-focused correct-tool description, the sibling set, and the densities fixed.

**Prediction (pre-registered in `run_selection_control.py`): recover to ≥0.80.** Result:

| density N | 3 | 5 |
|---|---|---|
| **verb-swap accuracy** | **1.00** | **1.00** |

10/10, every pick `lookup_users`. Moving the matching verb onto the correct tool yields **100%
recovery** — the attraction follows the **verb-token wherever it lives**, not the position or the count.
Prediction beaten (1.00 vs ≥0.80).

### Cross-provider anchor (Haiku — §0.8 substrate discipline)

The mechanism *could* be a cheap-model failure mode (v4-flash surface-matching where a stronger model
reads the description). Haiku anchor on the decisive cells:

| | N=1 pre | N=3 pre | post (any N) | verb-swap N=3 |
|---|---|---|---|---|
| **Haiku** | 1.00 | **0.20** | 1.00 | **1.00** |
| **DeepSeek** | 1.00 | 0.00 | 1.00 | 1.00 |

Same step-function, **same specific attractor** (all 4 Haiku wrong picks = `lookup_user`), same
namespacing + verb-swap recovery. Haiku is a hair more robust (1/5 resisted at N=3 → 0.20 vs 0.00) but
the mechanism is unmistakably present on an independent provider. **Cross-provider, not cheap-model.**

## Finding

**Tool selection is governed by lexical name↔request alignment, not tool count.** A confusable sibling
whose *name* matches the request verb captures the first tool call the instant it appears
(step-function), overriding the semantically-correct description — on two independent providers, and
causally confirmed by the verb-swap. Two fixes fall out:

1. **Namespace by entity** (`{entity}_search`) — makes the entity token the *unique* disambiguator and
   strips the verb-synonyms → **1.00 at every density, both providers**. (Practitioner consensus, now
   own-substrate.)
2. **Equivalently, align the tool's name-verb to the expected request** (the verb-swap fix).

## Disposition

Both falsifier clauses failed → **#2 confirmed and sharpened**. Trajectory **55 (hypothesis) → 78
(candidate)**. The confidence is capped below ~85 by a single load-bearing gap: **template-generality**
— one task template + one verb-pair ("lookup"/"look up"). **Path to `active`:** a 2nd template/verb-pair
replicating both the capture and the verb-swap recovery (ledgered as a cheap future follow-up; the
analog of the reasoning-pattern's "2nd debate per regime"). The mechanical DV means #2 carries **no
fuzzy-judge caveat** — a rigor advantage over §1.9.

Graph: `tool-selection` (78, candidate, `synthesis_ref=1.10`), 5 legs — namespacing-recovers 85 /
lexical-verb-capture 80 / presence-not-count 78 / cross-provider 72 / template-generality 55.

## Reproducibility

| script | produces |
|---|---|
| `prereg_selection.py` | graph: `tool-selection` hypothesis (55), pre-registered before the run |
| `run_selection.py --go [--densities …] [--arm-provider …]` | the density × namespace sweep (DV = first-tool == expected) |
| `run_selection_control.py --go [--densities …] [--arm-provider …]` | the verb-swap causal control |
| `record_selection_result.py` | graph: Evidence + Support + `tool-selection` candidate (78) |

Raw rows (append-only): `experiments/phase-1.2/results/selection-*.jsonl` (sweep) and
`selection-control-*.jsonl` (verb-swap); each row carries `arm_provider`/`arm_model`,
`density_n`, `namespaced`, `seed`, `picked`, `expected`, `correct`. 85 runs total (DeepSeek 50 sweep +
10 verb-swap; Haiku 20 sweep + 5 verb-swap). ~$0.04.
