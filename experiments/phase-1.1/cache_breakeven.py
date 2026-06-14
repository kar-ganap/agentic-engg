"""#3 (A) — empirical VERIFICATION of the carry-vs-swap crossover predicted by (B).

A SCRIPTED (no-agent) T-turn session — fixed, prescribed turns, so there's no agent call-count
variance (the confound that muddied #6). Each turn sends [system + tools + growing history];
measures real `cache_read_input_tokens` / `input_tokens` from DeepSeek; costs them at the same
v4-flash rates the prediction used. CARRY = superset N tools every turn (stable → hits). SWAP =
subset k tools, mutated at the task boundary (busts the suffix). Sweep N; find where carry-cost
crosses swap-cost; compare to the pre-registered N* ≈ 5,111 (`predict_cache_breakeven.py`).

SAFE BY DEFAULT: prints the plan + exits unless --go is passed.

    uv run python experiments/phase-1.1/cache_breakeven.py            # dry-run
    uv run python experiments/phase-1.1/cache_breakeven.py --go       # ~$0.05
"""

from __future__ import annotations

import argparse
import uuid

import anthropic

from stance.secrets import deepseek_api_key

HIT, MISS = 0.0028 / 1e6, 0.14 / 1e6  # v4-flash $/token (same as the prediction)
T, SWAP_TURN = 8, 4                    # 8 turns; SWAP mutates the tool block at turn 4
SUBSET_TOK, CONTENT_TOK = 1500, 800   # k; content added per turn
SWEEP_N = (2000, 4000, 5000, 6000, 7000, 8000)  # finer bracket of predicted N* ≈ 5111
PREDICTED_NSTAR = 5111
# Unique per RUN: DeepSeek prefix-cache TTL is hours-days, so a re-run would hit the prior run's
# warm cache and mis-measure the "cold" turn 1. A fresh nonce per invocation forces every session
# cold. (This is deliberately anti-reproducible on the cache STATE; the cost MODEL is what's pinned.)
NONCE = uuid.uuid4().hex[:6]


def _filler(n_tokens: int, salt: str) -> str:
    unit = f"{salt} " + "context note routine account review nothing actionable "
    return unit * (n_tokens // 8)


def _tool(tok: int, salt: str) -> list[dict[str, object]]:
    return [{
        "name": "lookup", "description": _filler(tok, salt),
        "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}, "required": []},
    }]


def _run_session(client: anthropic.Anthropic, tools_at: object) -> tuple[float, int]:
    """Run T scripted turns; return (total cost at the prediction's rates, turn-1 input tokens).

    Turn-1 is a full cold miss, so its input = system + tool-block + first content — the handle we
    use to recover the ACTUAL tool-token count (the nominal-N param isn't token-calibrated)."""
    msgs: list[dict[str, str]] = []
    cost, turn1_input = 0.0, 0
    for t in range(1, T + 1):
        if t > 1:
            msgs.append({"role": "assistant", "content": "Acknowledged."})
        msgs.append({"role": "user", "content": _filler(CONTENT_TOK, f"turn{t}") + " Reply OK."})
        r = client.messages.create(
            model="deepseek-v4-flash", system="You are a customer-support agent.",
            tools=tools_at(t), max_tokens=8, messages=msgs,  # type: ignore[arg-type]
        )
        u = r.usage
        cost += u.input_tokens * MISS + (getattr(u, "cache_read_input_tokens", 0) or 0) * HIT
        if t == 1:
            turn1_input = u.input_tokens
    return cost, turn1_input


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--go", action="store_true")
    args = p.parse_args()
    if not args.go:
        print(f"would run CARRY (N in {SWEEP_N}) + SWAP (k={SUBSET_TOK}, swap@turn {SWAP_TURN}), "
              f"{T} turns each, on deepseek-v4-flash. Predicted N* ≈ {PREDICTED_NSTAR}. Pass --go.")
        return

    client = anthropic.Anthropic(
        base_url="https://api.deepseek.com/anthropic", api_key=deepseek_api_key()
    )
    # SWAP: subset k tools; the block's content changes at the swap turn → busts the cache.
    # Salts carry the run-nonce so neither swap nor any carry-N session shares a prefix with another.
    swap, _ = _run_session(
        client, lambda t: _tool(SUBSET_TOK, f"s{NONCE}A" if t < SWAP_TURN else f"s{NONCE}B")
    )
    raw = []  # (nominal_n, turn1_input, carry_cost) — all sessions first, then calibrate, then print
    for n in SWEEP_N:
        carry, in1 = _run_session(client, lambda _t, n=n: _tool(n, f"c{NONCE}_{n}"))  # cold
        raw.append((n, in1, carry))
    # nominal N is not token-calibrated; recover actual tool-tokens from the linear turn-1 input.
    # turn-1 input = system + tool-block + first content; its slope in N gives tokens-per-nominal-N,
    # the intercept is the fixed (system + content) overhead → actual tool-tokens = in1 - overhead.
    (n_lo, in_lo, _), (n_hi, in_hi, _) = raw[0], raw[-1]
    overhead = in_lo - (in_hi - in_lo) / (n_hi - n_lo) * n_lo
    rows = [(n, in1 - overhead, c) for (n, in1, c) in raw]  # (nominal_n, actual_tool_tokens, carry)

    print(f"SWAP (k={SUBSET_TOK}, swap@{SWAP_TURN}): ${swap * 1e3:.4f}e-3\n")
    print(f"{'tool tok':>9} {'CARRY $e-3':>11} {'SWAP $e-3':>10}  cheaper")
    for _n, tok, carry in rows:
        print(f"{tok:>9.0f} {carry * 1e3:>11.4f} {swap * 1e3:>10.4f}  "
              f"{'carry' if carry < swap else 'swap'}")
    nstar = None
    for (_, a0, c0), (_, a1, c1) in zip(rows, rows[1:]):
        if c0 < swap <= c1:
            nstar = a0 + (a1 - a0) * (swap - c0) / (c1 - c0)
            break
    emp = f"{nstar:,.0f}" if nstar else "outside swept range"
    print(f"\nEMPIRICAL crossover ≈ {emp} actual tool-tokens  (pre-registered prediction: "
          f"{PREDICTED_NSTAR})")


if __name__ == "__main__":
    main()
