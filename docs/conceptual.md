# Conceptual Framing

> Skeleton document. The substantive concept stream lives in `docs/synthesis.md` (long-form draft, starts Module 1) and the evidence graph (`Claim` / `Evidence` / `Position` records). This file captures only the durable architectural framing that doesn't belong in either.

## The substrate in one paragraph

An evidence-based position-forming assistant for agentic engineering. Its job is to help the user form, defend, and update positions on the field's contested debates by accreting evidence (literature + experiments) into a single graph and surfacing position-relevant changes over time. Designed for years, not the 16-week curriculum that seeds it.

## Three layers (logical, not physical)

1. **Evidence layer** — `Claim` records (atomic propositions from sources or experiments), each linked to `Evidence` (with source-type or experiment-type and provenance). Append-only by default; revisions tracked.
2. **Position layer** — `Position` records (user's stance on a debate, with confidence, supporting evidence, and retraction criterion). Reviewable on a cadence (Property 3).
3. **Interface layer** — ingest (Property 1), query (Property 2), export (Property 4). Each wraps the layers below via MCP tools, A2A specialists, or direct calls depending on context.

## Design invariants (the ones expected to outlast the curriculum)

- **Append-only evidence; mutable positions.** Evidence accretes; positions evolve. Old positions get *demoted with reason*, never deleted — the trajectory is the learning.
- **Confidence is first-class.** Every position carries 0–100 confidence; no point-stance shortcuts.
- **Multiple evidence types per position where feasible** (literature + experiment).
- **Position-relevance is the filter.** Both ingest (digest filter) and query (retrieval) use position-relevance as the primary ranking signal, not generic similarity.
- **Files-as-interface, database-as-persistence.** Source documents land in the filesystem (so they're greppable); structured records live in SQLite (or equivalent). Aligned with the curriculum's M1 "files are all you need" thread.
- **Positions ship with portable evaluators.** A position decomposes into three layers: the **conclusion** (conditional — valid only within its preconditions, does not transfer blindly), the **applicability check** (its preconditions — general; given a new problem, decides whether the position applies), and the **evaluator** (its mechanism-data spec + measurement harness — general; given a qualifying problem's (task suite, model, metric), measures the position's efficacy *for that problem*). The long-term value of the package is that the second and third layers are reusable: a new problem can be plugged in and evaluated against the position store without bespoke glue. **Generality accretes along proven axes of variation — not by up-front universalization** (the Foxconn-factory premature-abstraction trap; cf. synthesis §2.3 and `tasks/lessons.md` §0.7). The preconditions + mechanism-data structure of each `Position` (see `docs/synthesis.md`) is literally this evaluator's interface: applicability-check as input gate, mechanism-data as output schema.

## What lives in this file vs. elsewhere

- *Here:* architectural invariants, layer model, things true across phases.
- *In `docs/synthesis.md`:* the long-form developing report — current positions, evidence summaries, contested-debate state.
- *In `docs/phases/`:* phase-specific plans and retros.
- *In the evidence graph:* the structured atomic records.
- *In `tasks/lessons.md`:* process discipline, separate from concept content.
