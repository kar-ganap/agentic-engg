"""Phase 1.1 #4 chain sweep — run configuration (versioned; Substrate Discipline #5).

Scoped cells (anchor + one-factor sweeps), NOT a factorial — each isolates one
driver (§0.13). Mirrors the Phase 1.0 run_config idiom. `run.py` consumes these.
The #4 prediction: mis-bind-rate rises with competition (and fill), roughly flat in
depth/distance (compounding shows as task-failure, not mis-bind). See
docs/phases/phase-1.1-plan.md § "Run-config".

    uv run python experiments/phase-1.1/run_config.py   # print plan + cost estimate (NO API)
"""

from __future__ import annotations

from dataclasses import dataclass

MODEL = "deepseek-v4-flash"
SEEDS = [1, 2, 3, 4, 5]
FILL_TOKENS = {"low": 5_000, "mid": 50_000, "high": 150_000}
COMPETITION_N = {"none": 0, "few": 3, "many": 8}
INPUT_USD_PER_MTOK = 0.14  # deepseek-v4-flash input; VERIFY against pricing.py before a run
BUDGET_USD = 75.0


@dataclass(frozen=True)
class Cell:
    """One #4 chain condition (swept over SEEDS). `sweep` tags which one-factor
    sweep it belongs to; the anchor is shared across the fill/position/competition
    sweeps (run once)."""

    sweep: str
    depth: int
    fill: str  # low | mid | high  (→ FILL_TOKENS)
    position: float
    competition: str  # none | few | many  (→ COMPETITION_N; none = the §0.18 control)
    arm: str = "A"
    tier: str = "chain"

    @property
    def cell_id(self) -> str:
        return f"chain-{self.sweep}-d{self.depth}-{self.fill}-p{self.position}-{self.competition}"


# Anchor A0 = depth8 / fill-mid / pos0.9 / comp-many (shared point of the sweeps).
_ANCHOR = Cell(sweep="anchor", depth=8, fill="mid", position=0.9, competition="many")

CELLS: list[Cell] = [
    _ANCHOR,
    # fill sweep (headline: rot/volume vs compounding) @ depth8/pos0.9/comp-many
    Cell(sweep="fill", depth=8, fill="low", position=0.9, competition="many"),
    Cell(sweep="fill", depth=8, fill="high", position=0.9, competition="many"),
    # depth sweep (compounding baseline) @ fill-LOW/pos0.9/comp-many
    Cell(sweep="depth", depth=2, fill="low", position=0.9, competition="many"),
    Cell(sweep="depth", depth=4, fill="low", position=0.9, competition="many"),
    Cell(sweep="depth", depth=8, fill="low", position=0.9, competition="many"),
    Cell(sweep="depth", depth=12, fill="low", position=0.9, competition="many"),
    # position sweep (needle-depth analog) @ depth8/fill-mid/comp-many
    Cell(sweep="position", depth=8, fill="mid", position=0.1, competition="many"),
    Cell(sweep="position", depth=8, fill="mid", position=0.5, competition="many"),
    # competition dose-response (§1.8 echo; none = control) @ depth8/fill-mid/pos0.9
    Cell(sweep="competition", depth=8, fill="mid", position=0.9, competition="none"),
    Cell(sweep="competition", depth=8, fill="mid", position=0.9, competition="few"),
]


def est_run_input_tokens(cell: Cell) -> int:
    """Rough cumulative input tokens for one run: context grows ~linearly to `fill`
    over (depth+2) turns, re-sent each turn → ≈ (fill/2)·(depth+2)."""
    fill = FILL_TOKENS[cell.fill]
    return (fill // 2) * (cell.depth + 2)


def estimate_cost_usd() -> float:
    total_input = sum(est_run_input_tokens(c) * len(SEEDS) for c in CELLS)
    return total_input / 1_000_000 * INPUT_USD_PER_MTOK


def _main() -> None:
    print("=== Phase 1.1 #4 chain sweep ===")
    print(f"model: {MODEL}   seeds: {SEEDS}")
    print(f"cells: {len(CELLS)}   runs: {len(CELLS) * len(SEEDS)}")
    print(f"fill: {FILL_TOKENS}   competition: {COMPETITION_N}")
    print()
    for c in CELLS:
        est = est_run_input_tokens(c) * len(SEEDS)
        print(
            f"  [{c.sweep:11}] d{c.depth:<2} {c.fill:4} p{c.position} {c.competition:4} "
            f"arm={c.arm}  ~{est / 1e6:.2f}M in/cell"
        )
    est = estimate_cost_usd()
    print()
    print(f"est. input cost: ${est:.2f}  (budget ${BUDGET_USD:.0f}; @ ${INPUT_USD_PER_MTOK}/MTok)")
    if est > BUDGET_USD:
        print("  WARNING: estimate exceeds budget — trim cells/seeds or drop high-fill.")


if __name__ == "__main__":
    _main()
