# Phase 2.1 B3 — Observability: OpenTelemetry / Langfuse (Module 6 L187)

> "Wire observability on day one, not month six." The mature pattern is a **closed loop**: observe
> traces → enrich/annotate → convert failed traces into regression eval datasets → update
> prompts/tools. B3 wires the first link — committed tool-loop runs → Langfuse traces.

## What's wired
`trace_to_langfuse.py` exports a committed run (events + run record) to **Langfuse v4** (OTel-native)
as a nested trace: a root `agent` observation → one child per loop turn (`tool` for a tool call,
`generation` otherwise), carrying token usage (`usage_details`), outcome (`terminal_status`,
`is_error`, `guard_action`), and cell coordinates. The client is built from `stance.secrets` —
explicit `.env` keys (`langfuse_public_key` / `langfuse_secret_key` / `langfuse_base_url`), **never
`os.environ`** (the security rule; Langfuse's SDK would otherwise read env vars directly).

**Re-pointable (§0.7):** it replays committed JSONL, so traces regenerate without re-running (or
re-paying for) the experiment. Deliberately a *post-hoc exporter* over the existing event log
(`tooluse/events.py` already timestamps every turn), not a loop rewrite.

## Verified
3 binding runs → live traces (Langfuse US cloud), e.g. `.../traces/a25aa725…`. `make check` green.

## The loop this enables (the point)
The exporter is **link 1** of observe→enrich→evaluate→update. **Link 3** (failed traces → regression
eval cases) connects directly to B4's held-out set + B6's reliability report: any `terminal_status`
other than `complete`, or a `silent-wrong`, becomes a candidate regression case. Not built here — the
current corpus is all-clean, so there is nothing failing to harvest — flagged as the natural next step.

    uv run python experiments/phase-2.1/trace_to_langfuse.py --runs runs/phase-1.1/binding --limit 3
