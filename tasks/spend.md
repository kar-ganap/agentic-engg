# Compute Spend

> Append-only log of LLM API + infra costs. Per CLAUDE.md § Code Rules (reproducibility) and § Substrate Discipline #5 (numbers regenerate from scripts).
>
> Format: `| date | phase | item | provider | model | tokens (in/out) | est. $ | notes |`

| date | phase | item | provider | model | tokens (in/out) | est. $ | notes |
|------|-------|------|----------|-------|-----------------|--------|-------|
| 2026-05-29 | 0.0 | repo scaffold | — | — | — | $0.00 | setup only |
| 2026-06-04 | 1.0 | A: context-rot evidence (regen) | Anthropic | claude-haiku-4-5 | 15.7M / ~0.01M | $15.80 | **Reproducible regeneration cost** of committed run files (567 runs: 5-seed diffuse + neutral/localized controls to 100k + clean_essay baseline). Computed from `exact_tokens` in `runs/phase-1.0/*haiku*.jsonl`; input-dominated (output ~5–15 tok/run). |
| 2026-06-04 | 1.0 | A: Sonnet within-family spot-check | Anthropic | claude-sonnet-4-6 | 1.15M / ~0.002M | $3.51 | 135 runs: diffuse + neutral + localized, knee region (≤20k), 3 seeds. Validates the diffuse-collapse is not a Haiku artifact. From `runs/phase-1.0/*sonnet*.jsonl`. |
| 2026-06-04 | 1.0 | A: clean-essay baseline (harness validation) | Anthropic | claude-haiku-4-5 | 5.37M / ~0.003M | $5.37 | 210 runs: clean_essay neutral-high + localized-high, 5 seeds to 100k. Reproduces Chroma: clean plateau (neutral-hi flat 1.0 to 100k) + distractor shrink (localized-hi → 0.80@100k). Re-run with fixed runner (old files lacked `answer`). |
| 2026-06-05 | 1.0 | A: realism check (LLM competitors) | Anthropic | claude-haiku-4-5 | ~4.3M / ~0.01M | $4.26 | v1 (20k, confounded) + v2 (20k overwritten + full 100k) diffuse-from-pinned-pool, + 2 pool-gen calls. Confirms collapse is not a templating artifact (knee potency-dependent ~50k natural vs ~10k templated). |
| 2026-06-05 | 1.0 | B: KV-cache anti-patterns | Anthropic | claude-haiku-4-5 | ~0.4M (cache-heavy) / tiny | $0.42 | 5 policies × 6 turns (restore 12) + pilot, ×3 iterations (cross-condition cache confounds fixed). Single clean run ~$0.14. §1.1/§3.3 confirmed: tool change = 7× stable (cache root). Cost exact from response.usage. |

> **Un-itemized iteration:** cumulative Haiku spend *including* debugging runs that were overwritten (count_tokens-validation failures, the max_tokens=64 truncation era, tool-param experiments — lessons §0.4/§0.11) ran a loose tally of ~$42. Those were not logged per-call, so only the regeneration cost above is reproducible. **Lesson:** log spend at run time, not retroactively (proposed §0.12).

## Running total

**~$29.35** reproducible (Haiku $15.80 + Sonnet $3.51 + baseline $5.37 + realism $4.26 + KV-cache $0.42) — cumulative incl. un-logged iteration ≈ $54. Soft cap $75 (lifted 2026-06-04).
