# Phase 0.0 — Foundations + Instrumentation Skeleton

**Stage:** 0 (Setup)
**Weeks:** 1
**Module(s):** Module 0 (skim) + cross-cutting setup
**Branch:** `main` (Phase 0.0 stays on main per CLAUDE.md § Git Lifecycle)
**Critical phase boundary?** No (Stage 0 has no critical-review requirement).

## Objective

Stand up the repo, the Python package skeleton, and the cross-cutting instrumentation that every subsequent phase reads from or writes to. End-of-phase deliverable: a runnable ~50-line raw agent loop with per-turn token-budget logging, against a real LLM API.

## Pre-registered success criteria

- [ ] Working name locked; pyproject.toml + src/ package skeleton uses it.
- [ ] A bare raw agent loop (~50 LOC, no framework) calls a real LLM, parses a tool call, executes it, appends the observation, loops to a stop token.
- [ ] Token-budget logger emits per-turn tokens by category (`system` / `tools` / `history` / `retrieved`) to an append-only log file.
- [ ] Empty eval-harness module exists with the shape it'll grow into in Phase 2.1.
- [ ] `make check` passes (ruff clean, mypy --strict clean, ≥1 smoke test green).
- [ ] CLAUDE.md, PLAN.md, and this phase plan are all referenced by an initial commit on `main`.

## Tasks

### 1. Name + skeleton (load-bearing decision, user owns)
- [ ] Lock the working name (Praxis / Receipts / Anvil / Stance / yours).
- [ ] Initialize `pyproject.toml` (uv-managed, Python 3.12+, dependencies: anthropic, pytest, ruff, mypy as a starting set).
- [ ] Create `src/<package>/__init__.py` and `tests/__init__.py`.

### 2. Raw agent loop (load-bearing learning, user writes)
- [ ] Read Anthropic *Building Effective Agents* (Schluntz & Zhang, Dec 2024) — fast vocabulary pass on the augmented-LLM building block and the workflow patterns.
- [ ] Implement `src/<package>/loop.py`: ~50-line while-loop that calls the model, parses a tool call (one or two trivial tools — e.g., echo + add), executes, appends observation, loops until stop token. **No framework.** Per CLAUDE.md § Workflow Rules #7, user writes this from scratch.
- [ ] One smoke test in `tests/test_loop.py` that runs the loop with a stubbed tool and asserts terminal behavior.

### 3. Token-budget logger (plumbing, Claude scaffolds)
- [ ] `src/<package>/instrumentation/token_budget.py`: a context manager / decorator that records per-turn tokens by category (`system`, `tools`, `history`, `retrieved`) to an append-only JSONL file in `runs/`.
- [ ] Wire it into the raw loop above.
- [ ] One test asserting the JSONL records have the expected shape across a multi-turn run.

### 4. Eval harness skeleton (plumbing, Claude scaffolds)
- [ ] `src/<package>/eval/__init__.py` with placeholder interfaces for: `Rubric`, `TrajectoryLog`, `LLMJudge`. No implementations — interfaces only. Grows in Phase 2.1.

### 5. Validation gate readiness
- [ ] `make check` runs and passes.
- [ ] `runs/` is in `.gitignore` (already in place).

## Out of scope (intentionally deferred)

- Evidence-graph schema (`Claim`/`Evidence`/`Position`) — designed in Phase 2.0 when substrate goes real and we know what tools need to query it.
- MCP server — Phase 2.3.
- LangGraph rebuild — Phase 2.2.
- Memory tiers — Phase 3.2.
- Any non-trivial tool — Phase 1.1.

## Throughline property progress (anticipated)

None this phase. Stage 0 is foundation only; Property 3 first moves in Phase 2.1, Property 2 in 2.2, Property 1 in 2.3, Property 4 in 3.1.

## Retro template (fill in at phase close)

→ `docs/phases/phase-0.0-retro.md` (create at phase close)
