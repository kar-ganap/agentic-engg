# Phase 0.0 — Foundations + Instrumentation Skeleton (Retro)

**Closed:** 2026-06-01
**Branch:** `main` (Stage 0 stays on main per CLAUDE.md § Git Lifecycle)
**Critical phase boundary?** No.

## Summary

Foundation work for the substrate. Stood up the Python package (`stance`), the repo conventions (CLAUDE.md, Makefile, `docs/phases/`, `tasks/`), and the four cross-cutting primitives every subsequent phase builds on:

- **Raw agent loop** (`src/stance/loop.py`) — ~50-line DI-driven turn-by-turn loop, no framework. Calls a configurable `complete_fn`, dispatches `tool_use` blocks, accumulates history until a non-`tool_use` stop.
- **Tool surface** (`src/stance/tools.py`) — frozen `Tool` dataclass + the trivial `ECHO` / `ADD` tools + stable `TOOLS` tuple. Pattern for all future tools.
- **Categorized context** (`src/stance/context.py`) — owns prompt state (system / tools / messages) and maintains per-category token bookkeeping via cumulative `count_tokens` + delta, with deferral for incomplete conversation states.
- **Budget logger** (`src/stance/instrumentation/token_budget.py`) — append-only JSONL of per-turn category snapshots. Cross-module instrument consumed by every subsequent phase.

Plus: project constitution (`CLAUDE.md`) and working plan (`PLAN.md`) adopted from the `crit-thinking → synthoracle → epibench` template lineage + ccupa governance.

## Decisions made

| Decision | Choice | Why |
|---|---|---|
| Stack | Python 3.12, uv, ruff, mypy `--strict` | Matches lineage template; no signal for anything else. |
| Per-section token counting strategy | **C with API `count_tokens`** (cumulative + delta) | Exact numbers needed for M1 cache-economics claims; latency cost acceptable for instrumentation. |
| LLM-call abstraction layer | **None** — call Anthropic SDK directly | YAGNI at Phase 0.0; revisit at M6.5 (LangGraph) or first second-provider need. |
| Tool registry shape | `TOOLS: tuple[Tool, ...]` (not list, not dict) | Enforces stability against M1 KV-cache discipline at the type level. |
| Dispatch dict location | In the loop, not in `tools.py` | `tools.py` describes *what* exists; consumers compose *how* to use. |
| Test fakes | DI for `count_fn` and `complete_fn`; `FakeCounter` in `tests/conftest.py` | Testable without API quota; conftest hoist applied when the 2nd consumer appeared. |
| Smoke test | One real-API call marked `@pytest.mark.slow` | Catches what unit tests can't; opt-in via `make test-all`. |
| Schema for `Claim` / `Evidence` / `Position` | **Deferred to Phase 2.0** | Substrate goes real at Module 3; no need to commit a shape we don't yet exercise. |

## Validation gate

| Gate | Status |
|---|---|
| Tests pass | **27/27** (`make test`); +1 real-API smoke (`make test-all`) |
| Lint / typecheck clean | `make check` green (ruff + mypy `--strict` + pytest) |
| Reproducibility | All code under `src/`; tests fully reproducible from committed state |
| Retro written | This file |
| `/learn` written | See `tasks/lessons.md` § Phase 0.0 |
| Three-reviewer parallel pass | N/A (Stage 0 is not a critical boundary) |

## Concept-stream output

**None** — Stage 0 is foundation/infrastructure. No positions formed, no debates resolved. Concept stream starts in Phase 1.0 (Module 1, Context Engineering).

→ *Methods / Results / Discussion / Related Work / Limitations:* N/A for this phase.

## Out of scope (deferred to specific later phases)

- Evidence-graph schema (`Claim` / `Evidence` / `Position`) → Phase 2.0 (Module 3)
- Per-call tool error handling → Phase 1.1 (Module 2)
- Async I/O → Phase 1.1+ as need surfaces
- Tool-call trajectory telemetry beyond token budgets → Phase 2.1 (Module 6)
- KV-cache breakpoints + cached-vs-uncached attribution → Phase 1.0 (Module 1)
- LLM-call abstraction layer → Phase 2.2 (Module 6.5) or earlier on second-provider need
- Compaction / `clear_history` / `pop_message` on `CategorizedContext` → Phase 1.0 (Module 1, compaction exercise)
- `retrieved` category accumulation logic → Phase 1.0 (Module 1, when retrieval lands)

## Throughline property progress

**None this phase.** Stage 0 is foundation. Property advancement begins:

- **Property 3** (re-evaluation cadence) → Phase 2.1
- **Property 2** (decision-support query surface) → Phase 2.2
- **Property 1** (stay-current ingest loop) → Phase 2.3
- **Property 4** (contribution surface) → Phase 3.1

## Key references (in-repo)

| Path | Role |
|---|---|
| `CLAUDE.md` | Project constitution (adopted from template lineage this phase) |
| `PLAN.md` | Week-by-week plan with throughline-property mapping |
| `docs/phases/phase-0.0-plan.md` | This phase's plan |
| `docs/conceptual.md` | Architectural framing (skeleton; defers to live docs) |
| `src/stance/loop.py` | Raw agent loop |
| `src/stance/context.py` | CategorizedContext + token bookkeeping |
| `src/stance/tools.py` | Tool dataclass + ECHO/ADD + TOOLS registry |
| `src/stance/instrumentation/token_budget.py` | BudgetLogger |
| `src/stance/eval/__init__.py` | Eval Protocol stubs (grow in Phase 2.1) |
| `tasks/lessons.md` | Process-stream entries from this phase |
| `tests/conftest.py` | Shared test helpers (`FakeCounter`, `load_dotenv`) |
