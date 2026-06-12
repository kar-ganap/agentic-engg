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
| 2026-06-05 | 1.0-ext | cross-family (DeepSeek) | DeepSeek | deepseek-v4-flash | 9.28M / tiny | $1.30 | 315 runs tool_call_stream low-sim via Anthropic-compat endpoint. Confounded (DSML tool-call leak); diffuse = abstention not collapse. Inconclusive for §1.8 clause(b). |
| 2026-06-05 | 1.0-ext | cross-structure (clean_essay) | Anthropic | claude-haiku-4-5 | 8.17M / ~0.005M | $8.17 | 315 runs clean_essay low-sim (neutral/localized/diffuse, 5 seeds to 100k). Neutral control broken by folio-wrinkle on prose → effect not isolable. Establishes structure×similarity entanglement (`results-cross-family.md`). |
| 2026-06-10 | 1.1 | entry-gate smokes (declared-tools + DSML 2×2) | DeepSeek | deepseek-v4-flash | ~1.3M / ~0.06M | ~$0.19 (est.) | Build-path gate. Declared-tools probe → CLEAN (structured tool_use); 120-call paired 2×2 → DSML leak 3/30 only in stream×no-tools, 0/30 elsewhere (conjunctive, §0.17). `experiments/phase-1.1/smoke_*.py`. Est. — usage not summed (cheap smoke). |
| 2026-06-12 | 1.1 | e2e pipeline smoke (1 chain cell) | DeepSeek | deepseek-v4-flash | ~0.036M / tiny | ~$0.003 | Full #4 pipeline end-to-end: build_chain_task→make_tools→run_tool_loop→score. 2 runs (run 1 caught + fixed an order-eligibility coherence bug; run 2 → correct-use ✓, control holds at low competition). Exact from response.usage. `experiments/phase-1.1/smoke_e2e.py`. |
| 2026-06-12 | 1.1 | #4 chain sweep (11 cells × 5 seeds) + depth pilot | DeepSeek | deepseek-v4-flash | ~5.6M / ~0.03M | $0.789 | 55-run sweep ($0.773) + 8-run depth pilot ($0.016). Fill/depth/position/competition; fill_at_use to 186k. Result: 55/55 correct-use, 0 mis-bind — clean NULL, INCONCLUSIVE for #4 (manipulation bit on volume+presence, not same-frame rivalry). `experiments/phase-1.1/results.md`. |

> **Un-itemized iteration:** cumulative Haiku spend *including* debugging runs that were overwritten (count_tokens-validation failures, the max_tokens=64 truncation era, tool-param experiments — lessons §0.4/§0.11) ran a loose tally of ~$42. Those were not logged per-call, so only the regeneration cost above is reproducible. **Lesson:** log spend at run time, not retroactively (proposed §0.12).

## Running total

**~$39.80** reproducible (Phase 1.0: Haiku $15.80 + Sonnet $3.51 + baseline $5.37 + realism $4.26 + KV-cache $0.42; ext: DeepSeek $1.30 + cross-structure $8.17; Phase 1.1: entry-gate smokes ~$0.19 + e2e smoke ~$0.003 + #4 chain sweep $0.789) — cumulative incl. un-logged iteration ≈ $64. Soft cap $75 (lifted 2026-06-04).
