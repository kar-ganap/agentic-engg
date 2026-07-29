# Phase 2.1 B7 — Feedback-loop-vs-model attribution (Module 6 L192 punchline)

> Curriculum (L184/L192): *"much of reliability comes from the deterministic feedback loop **around**
> the model, not the model itself"* — "measure how much of the quality gain comes from the feedback
> loop vs. the model." **No fresh experiment is needed: §1.2 Thread-C already IS this measurement**,
> cleanly and cross-provider. This note frames that result as the attribution and connects it to the
> eval-harness mechanism built in B1.

## The measurement (§1.2 Thread-C, `results-correction.md`)
The task is constructed so a format rule lives **only** in a tool failure's content — the agent can
succeed on a late attempt **iff it adapted its action from that failure**. DV = fraction of late
first-attempt submits that apply the rule (task success). The single manipulated variable is whether
the deterministic corrective is **kept in context** (`preserve`) or **dropped** (`summarize`); the
model is identical across arms.

| provider | reasoning | preserve (loop on) | summarize (loop off) |
|---|---|---|---|
| Haiku (5 seeds) | strip | **1.00** | **0.00** |
| deepseek-chat (3 seeds, non-reasoning) | strip | **1.00** | **0.00** |
| Haiku | persist | 1.00 | 1.00 |

**Attribution:** with capability fixed, the deterministic feedback loop (corrective-in-context)
accounts for the **entire** achievable task-success gain — 1.00 → 0.00 when it is removed,
cross-provider, per-seed perfect. This is the curriculum's claim in its strongest form: *the loop,
not the model.*

## The scope-bounding null (the honest part)
The `persist` arm is **1.00 regardless** (preserve = summarize). When the model's *own* reasoning
persists across turns, it **self-rescues** — it carries the correction internally, so the external
loop is redundant. So the precise claim is: **the deterministic feedback loop is decisive exactly
where the model cannot self-rescue** — ephemeral-reasoning strips and non-reasoning models. A capable
model with persisted chain-of-thought substitutes its own internal correction for the external loop.
(This is also why B1's corrective-injection matters most for cheaper / non-reasoning agents.)

## The mechanism is now in the eval-harness (B1)
B1's verifier-split formats deterministic failures as **corrective signals for context re-injection**
(`EvalReport.correctives`, `Verdict.corrective`). §1.2 measured the *value* of exactly that loop;
B1 is the reusable machinery that produces the corrective a harness would inject.

## A second instance of eval-loop attribution (B5)
B5 (eval-driven-dev) is the same shape on a different task: deterministic held-out failures drove a
description rewrite, and the **isolation** attributed the working lever (attractor-demotion, not
correct-tool-improvement). Different mechanism, same discipline — the eval loop drives the change and
an isolation attributes it, rather than trusting an aggregate "it improved."

## Net
The feedback-loop-vs-model claim is **confirmed at its strongest** (1.00 vs 0.00), scoped honestly:
decisive when the model can't carry the correction in its own reasoning; redundant when it can.
No new spend — this is an attribution over committed §1.2 / B5 data.
