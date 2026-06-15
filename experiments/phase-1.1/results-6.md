# Phase 1.1 #6 — return-format policy: fix to inline-detailed (the choice IS used)

> **Outcome: if you fix one return format, fix it to inline-detailed — but do NOT conclude "never
> offer a choice."** The original read of this experiment ("models don't exploit an agent-set format
> choice → remove it") was **overturned by the three-reviewer pass + a firsthand re-tally**: it
> rested on a *read-tools-only* slice. The full per-tool view shows **all three models (v4-flash /
> Sonnet / v4-pro, two families) DO use the choice — and sensibly**: `concise` on the terminal
> `send_message` (whose return nothing consumes downstream) and `detailed` on the reads it needs. So
> the choice is **not** unexploited overhead. What survives is the **fixed-arm ranking**: A
> (inline-detailed) 100% success at lowest (call-count-confounded) cost; D (handle-block) pure
> overhead; B (concise, handle pruned) → 0%. **#6 prior 45 → 48** (near equipoise: the success
> discriminator never fired AND the behavioral pillar inverted). Written 2026-06-14; **corrected
> 2026-06-14 post-review**. Numbers regenerate from
> `runs/phase-1.1/format/{deepseek-v4-flash,sonnet-4-6,deepseek-v4-pro}_*.jsonl`.

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

## The behavioral finding, CORRECTED: the choice is used — sensibly (per-tool, all decisions)

> **The original version of this section was wrong** — it tallied `response_format` only on the
> *read* tools (`get_ticket`/`get_full_ticket_history`/`get_order`) and concluded "detailed
> everywhere → choice unexploited." It **omitted `send_message`**, the terminal write — where every
> model goes `concise`. The three-reviewer pass (method-rigor, conf 82) caught it; a firsthand
> re-tally of `runs/phase-1.1/format/*_events.jsonl` (arm C, all tools) confirms.

Full per-tool `response_format` (concise / total), arm C:

| tool | role | v4-flash | Sonnet | v4-pro |
|---|---|---|---|---|
| `send_message` | terminal write (return unused) | **10/15 concise** | **3/3 concise** | **2/3 concise** |
| `get_order` | handle source (return consumed) | 3/18 | 0/3 | 0/3 |
| `get_ticket` | content read | 0/24 | 0/3 | 0/6 |
| `get_full_ticket_history` | content read | 1/11 | 0/3 | 0/3 |

So **all three models — two families, ~7× span — *do* use the choice, and the usage is sensible**:
`concise` exactly where it's free (the terminal send nobody reads), `detailed` on the reads whose
content/handle is needed. This **inverts** the original behavioral claim: the choice is not
unexploited overhead — it is exercised, and roughly correctly. (Whether it's exercised *optimally*
is moot for the verdict: arm C matches arm A on success at no clear cost, so offering the choice is
harmless-to-mildly-helpful, not the overhead the first read claimed.)

## Why the token ranking is supporting-only (call-count confound)

The loop re-sends the full history each turn, so total tokens ≈ **Σ(return_size × remaining_turns)** —
dominated by **how many tool calls** the agent makes (variable `get_ticket` re-reads), not the
per-return format. E.g. A-fhigh made **12** `get_ticket` calls vs C-fhigh's **9**, which alone
explains the A>C token gap. So the (directional) ordering — **A cheapest; C and D add overhead
(C's per-tool `response_format` schema param; D's `[ids:]` block on every return) with no success
benefit** — is consistent with the behavioral finding but is not, on its own, load-bearing.

## Verdict — return-format design rules (corrected)

1. **If you fix one return format, fix it to inline-detailed (A).** 100% success at the lowest
   (call-count-confounded) cost on all three models. This is the surviving actionable claim.
2. **Don't always-attach a handle-block (D).** Pure per-return overhead, no success benefit.
3. **Don't over-prune to concise (B).** Pruning a handle the downstream needs → 0% (fabricate/loop).
4. **Offering a per-call choice (C) is NOT harmful — and is mildly used.** *(Reversed from the
   original "don't offer a choice.")* Arm C matches A on success; the agent spends the choice
   sensibly (concise on the terminal send, detailed on reads). So "remove the choice, it's
   unexploited overhead" is **not supported**. Whether to *expose* a choice is now open, not a
   verdict — the choice is harmless here, and might help under economy pressure (untested).

## Confidence & caveats

**#6: 45 → 48.** Only a small move off the prior, because the position's evidential basis is weak in
both directions:
- the **intended discriminator (success) never fired** (A/C/D all 100% — easy task);
- the **token DV is call-count-confounded** (ordering flips by model → not decisive);
- and the **behavioral pillar inverted** under the corrected per-tool tally (the choice *is* used).
What we can say with cross-model support (v4-flash/Sonnet/v4-pro, 2 families): **fixed inline-detailed
is a safe default; concise-pruned is dangerous (0%); handle-block is overhead.** What we *cannot* say:
"never offer a choice." The +3 reflects the surviving fixed-arm ranking; equipoise on the choice
question pending a redesign.

**Retraction / revival paths:** (a) an **economy-pressure prompt** ("use concise unless you need the
ids") + a **call-count-controlled** task would turn the directional token ranking into a real number
and test whether the choice is *beneficial* (not just used); (b) a harder task where success
discriminates would test whether arm choice ever *hurts*.

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
