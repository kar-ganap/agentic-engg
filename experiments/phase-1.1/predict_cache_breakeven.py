"""#3 (B) — analytical PREDICTION of the carry-vs-swap crossover (pre-registration).

Pure arithmetic, NO API. Cost model from the step-1 smoke (`smoke_cache.py`): a stable prefix is
a cache HIT; mutating the tool block busts the whole request (full MISS); rates are v4-flash
hit=$0.0028 / miss=$0.14 per MTok. A scripted T-turn session, history growing C tokens/turn:

  per turn t (request = system S + tools + t·C):
    cold (t=1) or swap-turn  → full MISS (read 0): S + tools + t·C
    stable turn (t>=2)       → HIT prefix S+tools+(t-1)C, MISS only the new C

CARRY = superset N tools every turn, never swaps. SWAP = subset k tools, busts on swap turns.
Sweep N → the crossover N* (carry-cost = swap-cost). Verified empirically by `cache_breakeven.py`.

    uv run python experiments/phase-1.1/predict_cache_breakeven.py
"""

from __future__ import annotations

HIT = 0.0028 / 1e6   # deepseek-v4-flash cache-hit $/token
MISS = 0.14 / 1e6    # deepseek-v4-flash input (miss) $/token

# pre-registered config (chosen so N* is small → cheap to verify)
T, C, S, K = 8, 800, 300, 1500     # turns, content/turn, system, subset tool-tokens
SWAP_TURNS = {4}                    # one task boundary mid-session


def session_cost(tool_tokens: int, swap_turns: set[int]) -> float:
    cost = 0.0
    for t in range(1, T + 1):
        if t == 1 or t in swap_turns:           # cold or busted → full request misses
            miss, read = S + tool_tokens + t * C, 0
        else:                                    # stable prefix cached; only new content misses
            miss, read = C, S + tool_tokens + (t - 1) * C
        cost += miss * MISS + read * HIT
    return cost


def main() -> None:
    swap = session_cost(K, SWAP_TURNS)           # subset k, busts at turn 4
    print(f"config: T={T} C={C} S={S} subset_k={K} swaps={sorted(SWAP_TURNS)} "
          f"(rates hit=${HIT*1e6}/MTok miss=${MISS*1e6}/MTok)")
    print(f"SWAP cost (fixed): ${swap*1e3:.4f}e-3\n")
    print(f"{'superset N':>11} {'CARRY $e-3':>11} {'SWAP $e-3':>10}  cheaper")
    prev = None
    crossover = None
    for n in (1500, 2000, 3000, 4000, 5000, 6000, 8000, 12000, 20000):
        carry = session_cost(n, set())           # superset N, never swaps
        winner = "carry" if carry < swap else "swap"
        if prev is not None and prev != winner and crossover is None:
            crossover = n
        prev = winner
        print(f"{n:>11} {carry*1e3:>11.4f} {swap*1e3:>10.4f}  {winner}")
    # solve carry_cost(N) = swap exactly: carry is linear in N → interpolate
    c0, c1 = session_cost(0, set()), session_cost(1000, set())
    slope = (c1 - c0) / 1000
    nstar = (swap - c0) / slope
    print(f"\nPREDICTED crossover N* ≈ {nstar:,.0f} tool-tokens "
          f"(carry cheaper below, swap cheaper above)")


if __name__ == "__main__":
    main()
