"""Phase 1.0 context-rot run configuration (versioned; Substrate Discipline #5).

Declares the experimental cell grid for Exercise A (context-rot study). The
pre-registration (predictions P1-P4 + mechanism) lives in `docs/synthesis.md`
§3.6 — locked before running. `runner.py` (built next) consumes these constants
to execute the sweep and log results.

Run this module directly to print the run plan + a cost estimate (NO API calls):
    uv run python experiments/phase-1.0/run_config.py
"""

from __future__ import annotations

from dataclasses import dataclass

# --- sweep axes -----------------------------------------------------------
LENGTHS = [1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000]  # target tokens
DEPTHS = [0.1, 0.5, 0.9]  # needle position fraction (averaged; decomposable)
SEEDS = [1, 2, 3, 4, 5]

# --- models ---------------------------------------------------------------
MODEL_PRIMARY = "claude-haiku-4-5-20251001"  # bulk runs (rots early/cheap)
MODEL_VALIDATION = "claude-sonnet-4-6"  # spot-checks of key points only

# --- budget ---------------------------------------------------------------
BUDGET_USD = 50.0
# Rough Haiku-tier input price; VERIFY against current pricing before the run.
_INPUT_USD_PER_MTOK = 1.0


@dataclass(frozen=True)
class Cell:
    """One experimental condition (swept over LENGTHS x DEPTHS x SEEDS)."""

    structure: str
    competition: str
    similarity: str
    item: str  # backlog item it serves
    tests: str  # predictions / positions it bears on


# Scoped cells — NOT full factorial. Each tests a specific prediction.
CELLS = [
    # Item 2 — essay baseline: validate the harness reproduces Chroma's
    # similarity (high vs low) and distractor (neutral vs localized) effects.
    Cell("clean_essay", "neutral", "high", "2", "harness validation; §1.8 baseline"),
    Cell("clean_essay", "localized", "high", "2", "Chroma distractor effect"),
    Cell("clean_essay", "neutral", "low", "2", "Chroma similarity effect (low-sim)"),
    Cell("clean_essay", "localized", "low", "2", "distractor x low-sim"),
    # Item 3 — agentic novelty (low-sim throughout): neutral / localized / diffuse
    # give P1 (diffuse vs neutral) and P2 (diffuse vs localized; crossover at length).
    Cell("tool_call_stream", "neutral", "low", "3", "agentic baseline / passband?"),
    Cell("tool_call_stream", "localized", "low", "3", "P2 reference (localized)"),
    Cell("tool_call_stream", "diffuse", "low", "3", "P1 (vs neutral); P2 (vs localized)"),
    # Item 5 (may slip): research_doc_stream x low-sim x {neutral, diffuse}
    # Item 6 (may slip): failure-shaped padding (§3.4)
]


def runs_per_cell() -> int:
    return len(LENGTHS) * len(DEPTHS) * len(SEEDS)


def estimate_cost_usd() -> float:
    """Rough input-token cost across all cells (output + count_tokens negligible/free)."""
    input_tokens_per_cell = len(DEPTHS) * len(SEEDS) * sum(LENGTHS)
    total_input_tokens = len(CELLS) * input_tokens_per_cell
    return total_input_tokens / 1_000_000 * _INPUT_USD_PER_MTOK


def _main() -> None:
    rpc = runs_per_cell()
    print("=== Phase 1.0 context-rot run plan ===")
    print(f"lengths: {LENGTHS}")
    print(f"depths:  {DEPTHS}   seeds: {SEEDS}")
    print(f"runs/cell: {rpc}   cells: {len(CELLS)}   total runs: {len(CELLS) * rpc}")
    print(f"primary model: {MODEL_PRIMARY}")
    print()
    for c in CELLS:
        print(f"  [item {c.item}] {c.structure:16} {c.competition:10} sim={c.similarity:4} -> {c.tests}")
    est = estimate_cost_usd()
    print()
    print(f"est. input cost: ${est:.2f}  (budget ${BUDGET_USD:.0f}; @ ${_INPUT_USD_PER_MTOK}/MTok input — VERIFY pricing)")
    if est > BUDGET_USD:
        print("  WARNING: estimate exceeds budget — trim seeds, drop 100k, or split cells.")


if __name__ == "__main__":
    _main()
