# Phase 1.1 #6 — return-format policy: fix it, don't offer the choice

> **Outcome: remove the format choice; fix the return to inline-detailed.** Neither a weak model
> (DeepSeek v4-flash) nor a capable one (Sonnet 4.6) *exploits* an agent-set return-format choice —
> both default to `detailed` everywhere, even where `concise` is free — so the choice is unexploited
> overhead. Confirmed across **three models, two families, ~7× capability span**. **#6 prior 45 → 62.**
> The **behavioral** finding (choice unexploited, cross-provider) is
> load-bearing; the token ranking is supporting-only (call-count confounded). Written 2026-06-14.
> Numbers regenerate from `runs/phase-1.1/format/{deepseek-v4-flash,sonnet-4-6}_summaries.jsonl`.

## Question & arms

Should a tool's return **expose a format choice** to the agent, or **fix** it? Task
(`tasks/format.py`): `get_order` → (review 3-ticket history, if fill ≥1000) → `send_message(account_id)`
— the downstream send needs the account handle `get_order` returns, so the arm gates success:

- **A** detailed (ids inline) · **B** concise (ids omitted → floor) · **C** agent-chooses
  (`response_format` enum per call) · **D** handle-block (ids always in a `[ids: …]` block).

## Results

**DeepSeek v4-flash** — 4 arms × fill{low,mid,high} × 5 seeds (60 runs, $0.10):

| arm | low (success / ~tok) | mid | high |
|---|---|---|---|
| **A** detailed | 5/5 · 4.5k | 5/5 · 27.0k | 5/5 · 53.8k |
| **B** concise | **0/5** · 19.1k | **0/5** · 20.7k | **0/5** · 18.7k |
| **C** agent-choice | 5/5 · 4.6k | 5/5 · 31.0k | 5/5 · 46.5k |
| **D** handle-block | 5/5 · 4.8k | 5/5 · 25.6k | 5/5 · 60.7k |

**Anchors — A/C/D × high × 3 seeds** (Sonnet 4.6, $0.83; DeepSeek v4-pro, $0.10):

| arm | Sonnet (success / ~tok) | v4-pro (success / ~tok) |
|---|---|---|
| **A** detailed | 3/3 · 23.0k | 3/3 · 47.1k |
| **C** agent-choice | 3/3 · 31.3k | 3/3 · 41.8k |
| **D** handle-block | 3/3 · 30.5k | 3/3 · 55.1k |

Note the token ordering **flips** across models (Sonnet: A<D<C; v4-pro & v4-flash-high: C<A<D) — a
real format-efficiency effect wouldn't flip by model; this is the call-count confound (below).

## The load-bearing finding (behavioral, confound-free): the choice is unexploited — cross-provider

The choice (C) could pay off only if the agent went **`concise` on returns that don't need a handle**
(the *tickets* — you're just reading them) and **`detailed` on `get_order`** (handle needed). Reading
the per-tool `response_format` choices straight from the events:

- **v4-flash (C):** `detailed` on `get_ticket` ×9, `get_full_ticket_history` ×5, `get_order` ×5 (+1 concise).
- **v4-pro (C):** `detailed` on `get_ticket` ×6, `get_full_ticket_history` ×3, `get_order` ×3 — all detailed.
- **Sonnet (C):** `detailed` on **everything** — `get_ticket` ×3, `get_full_ticket_history` ×3, `get_order` ×3.

**All three models — two families, ~7× capability span — just default to `detailed`,** including on the tickets where `concise` is free. The
choice's potential savings are never realized — on a *weak* model and a *capable* one (a ~7×
capability gap; §0.8). This per-decision signal is **independent of how many calls the agent made**,
so it's the clean basis for the verdict.

## Why the token ranking is supporting-only (call-count confound)

The loop re-sends the full history each turn, so total tokens ≈ **Σ(return_size × remaining_turns)** —
dominated by **how many tool calls** the agent makes (variable `get_ticket` re-reads), not the
per-return format. E.g. A-fhigh made **12** `get_ticket` calls vs C-fhigh's **9**, which alone
explains the A>C token gap. So the (directional) ordering — **A cheapest; C and D add overhead
(C's per-tool `response_format` schema param; D's `[ids:]` block on every return) with no success
benefit** — is consistent with the behavioral finding but is not, on its own, load-bearing.

## Verdict — four return-format design rules

1. **Don't offer the agent a format choice (C).** Models don't spontaneously exploit it (default to
   `detailed`); the choice just adds the `response_format` schema param to every tool, every turn.
2. **Fix the return to inline-detailed (A).** Cheapest + 100% success on both providers.
3. **Don't always-attach a handle-block (D).** Pure per-return overhead, no success benefit.
4. **Don't over-prune to concise (B).** Pruning a handle the downstream needs → 0% (fabricate/loop).

## Confidence & caveats

**#6: 45 → 62.** Up because the load-bearing finding (choice unexploited, fixed-detailed dominates)
is clean and **replicates across three models, two families, a ~7× capability span** (v4-flash,
v4-pro, Sonnet) — and the token ordering *flips* across them, confirming the token DV is confounded
(so the behavioral signal is doing the work). Tempered by:
- **success didn't discriminate** (A/C/D all 100% — the task is easy enough that any handle-providing
  policy works; only tokens differ);
- the **token DV is call-count-confounded** (so the efficiency ranking is directional, not decisive);
- models might exploit the choice **if explicitly prompted to economize** — they don't do it
  *spontaneously* (untested with economy-pressure prompting).

**Retraction:** a model that *spontaneously* goes `concise`-when-safe and thereby Pareto-beats fixed
detailed (especially under an economy-pressure prompt or a call-count-controlled task).

## Reproduce & cost

```bash
uv run python experiments/phase-1.1/run_format.py --go                                    # DeepSeek sweep (60)
uv run python experiments/phase-1.1/run_format.py --arms A,C,D --fill high \
    --provider anthropic --limit-seeds 3 --go                                             # Sonnet anchor (9)
uv run python experiments/phase-1.1/run_format.py --arms A,C,D --fill high \
    --provider deepseek --model deepseek-v4-pro --limit-seeds 3 --go                       # v4-pro anchor (9)
```
Spend: sweep $0.10 + Sonnet anchor $0.83 + v4-pro anchor $0.10 = **~$1.03** (logged in `tasks/spend.md`).

## Open / future
- A **call-count-controlled** task (prescribed tool sequence) would let the *token* DV cleanly
  measure per-return format cost — the way to turn the directional A<C<D ordering into a verdict.
- An **economy-pressure prompt** ("use concise unless you need the ids") would test whether the
  choice is *usable* (vs merely un-used-by-default) — the one path that could revive C.
