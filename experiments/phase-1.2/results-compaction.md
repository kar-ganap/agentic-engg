# Phase 1.2 Thread B — Compaction: do failures deserve preservation? (§1.2)

> Module-1's compaction exercise (Ex 2), never built before — the whole §1.2 / §2.1 / §3.x cluster
> was stranded on it. §1.2 was **literature-only (65, Manus + Anthropic)**; this is its first
> own-substrate test. **DV = ref-recall** (fraction of buried release refs the agent submits to
> `file_report`) — mechanical, no judge.

## Pre-registration (before the powered run)

**Claim:** under compaction, preserving failures **verbatim** retains goal-critical info that
summarizing loses — **conditional on ephemeral reasoning**; with persisted reasoning the model
self-rescues (null). **Prior 68** (user-set). **Falsifier:** (a) at 5 seeds `strip`+preserve does
*not* beat `strip`+summarize → demote −15; (b) `persist` *also* shows preserve>summarize → the
self-rescue story is wrong. Graph: `compaction-preserve-failures` (hypothesis 68). See
`prereg_compaction.py`.

## The design (all pre-prereg instrument-tuning — five design flaws the smokes forced out)

Each was a genuine design flaw or a couldn't-have-known-at-prereg fact, not result-chasing:

1. **Model batches** the whole task into one turn → no cross-turn context to compact. Fix: a
   **breadcrumb chain** (each `check_shipment` names the next order → sequential by construction).
2. **Trigger never fired** — it read `input_tokens`, but under prompt-caching that's only the
   *uncached delta*. Fix: trigger on the **full fill** (`input + cache_read + cache_creation`), like
   `score._fill` / §1.1. (Stash-proofed with a cached-context regression test.)
3. **Flavor-1 dead-end task couldn't discriminate** — a `NOT_FOUND` is redundant with the agent's
   never-compacted action history. Fix: **flavor-2** — the failure carries *forward-info* (a ref).
4. **Small results are self-preserved** — a capable model trivially carries a 40-token result
   forward. Fix: **large (~530-token) transcripts with the ref buried** (the regime that actually
   needs compaction).
5. **Reasoning is the self-preservation channel** — the model echoes salient content into its own
   reasoning, which compaction never touches. Fix: **`strip_reasoning`** (don't persist the model's
   between-call text → ephemeral-CoT regime) as the decisive IV.

**Substrate correction (the big one):** DeepSeek *reproduces content ablated from the request* — not
caching (output-invariant, `cache_read=0` verified) but its **stateful `reasoning_content`**: v4-flash
copies the ref into its thinking trace, which DeepSeek demands be resent (native 400: *"must be passed
back"*) / the `/anthropic` shim re-injects. So DeepSeek can't reach the `strip` regime. **Compaction
is an Anthropic-substrate experiment** (as CLAUDE.md prescribes). Full account: lessons §0.27.

## Powered result — Haiku 2×3 × 5 seeds

| reasoning | preserve_failures | summarize_but_flag | summarize_uniform |
|---|---|---|---|
| **persist** | 1.00 | 1.00 | 1.00 |
| **strip** | **1.00** | **0.20** | **0.20** |

Per-seed (the effect is not an average artifact):
- `strip`/preserve = **1.00 on all 5 seeds**; `strip`/summarize = 0.00–0.33/seed; **delta +0.67 to
  +1.00 every seed** — no seed ties.
- `persist` = flat 1.00 everywhere. `flag` ≡ `uniform` per-seed (the one-line signal never carries
  the buried ref).

**Cross-provider null:** DeepSeek v4-flash `persist` × 3 seeds = flat 1.00 (all policies) —
corroborates the `persist` self-rescue null on a second family.

## Disposition

Both falsifier clauses fail → **§1.2 confirmed, own-substrate, conditionally.** Trajectory **65
(literature) → 68 (prereg) → 74 (candidate)**. The claim, sharpened:
> Preserving failures **verbatim** matters — but **only when the agent's reasoning is ephemeral**.
> With persisted reasoning the model self-rescues salient failure-content into its own tokens
> (null, cross-provider). And it must be *verbatim*: a distilled signal (`flag`) loses a datum
> buried in the failure body.

Capped below ~80 by: the **bite is single-provider** (Haiku; DeepSeek pinned to `persist`), the
**regime is engineered** (large un-extractable failure + ephemeral CoT — real but a specific corner),
and the **DV is info-survival** (a clean mechanism measure, a proxy for downstream success). Graph:
`compaction-preserve-failures` (74, candidate, 5 legs, `tension_with 2.1`).

## §2.1 tension (Manus "keep the wrong stuff in" vs Chroma context rot)

This gives the tension a **mechanism-level resolution**: Manus's "keep failures in" is right *when the
agent can't otherwise recover the failure's signal* (ephemeral reasoning + large un-extractable
failure); Chroma's "rot" (spent successes are distractors) is why *all* arms drop success payloads.
The two aren't opposed — they partition by **what carries the signal**: preserve the failure iff the
model won't self-rescue it.

## Reproducibility

| script | produces |
|---|---|
| `prereg_compaction.py` | graph: §1.2 hypothesis (68), pre-registered before the run |
| `run_compaction.py --go [--reasoning …] [--arm-provider …] [--bust-cache]` | the 2×3 sweep; DV = ref-recall |
| `deepseek_native.py` | OpenAI-format adapter (localized the DeepSeek anomaly to core, not the shim) |
| `record_compaction_result.py` | graph: Evidence + Support + §1.2 candidate (74) |

Mechanism (`src/stance/tooluse/compaction.py` + `loop.py` hook, TDD, stash-proofed). Raw rows:
`experiments/phase-1.2/results/compaction-*.jsonl` (Haiku 2×3×5 = `…151549`; DeepSeek persist =
`…152237`); raw events/runs in `runs/phase-1.2/` (gitignored). ~$0.7 (Haiku-dominated).
