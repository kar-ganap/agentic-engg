# Compute Spend

> Append-only log of LLM API + infra costs. Per CLAUDE.md § Code Rules (reproducibility) and § Substrate Discipline #5 (numbers regenerate from scripts).
>
> Format: `| date | phase | item | provider | model | tokens (in/out) | est. $ | notes |`

| date | phase | item | provider | model | tokens (in/out) | est. $ | notes |
|------|-------|------|----------|-------|-----------------|--------|-------|
| 2026-05-29 | 0.0 | repo scaffold | — | — | — | $0.00 | setup only |
| 2026-06-04 | 1.0 | A: context-rot evidence (regen) | Anthropic | claude-haiku-4-5 | 15.7M / ~0.01M | $15.80 | **Reproducible regeneration cost** of committed run files (567 runs: 5-seed diffuse + neutral/localized controls to 100k + clean_essay baseline). Computed from `exact_tokens` in `runs/phase-1.0/*haiku*.jsonl`; input-dominated (output ~5–15 tok/run). |
| 2026-06-04 | 1.0 | A: Sonnet within-family spot-check | Anthropic | claude-sonnet-4-6 | 1.15M / ~0.002M | $3.51 | 135 runs: diffuse + neutral + localized, knee region (≤20k), 3 seeds. Validates the diffuse-collapse is not a Haiku artifact. From `runs/phase-1.0/*sonnet*.jsonl`. |

> **Un-itemized iteration:** cumulative Haiku spend *including* debugging runs that were overwritten (count_tokens-validation failures, the max_tokens=64 truncation era, tool-param experiments — lessons §0.4/§0.11) ran a loose tally of ~$42. Those were not logged per-call, so only the regeneration cost above is reproducible. **Lesson:** log spend at run time, not retroactively (proposed §0.12).

## Running total

**~$19.30** reproducible (Haiku evidence $15.80 + Sonnet spot-check $3.51) — cumulative incl. un-logged iteration ≈ $45. Budget $50.
