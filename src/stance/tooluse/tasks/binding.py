"""Active-vs-passive binding A/B — isolates the agentic-self-fetch immunity (results.md).

Same needle + same-frame RIVALS (`order O_i is held by account A_i`), varying ONLY how
the needle is obtained:
- **passive:** the needle's mapping is in the dumped directory (in the prompt); the agent
  must FIND it among rivals (content-addressed retrieval, no get_order). Tools: send_message.
- **active:** the needle is fetched via `get_order(O_target)`; the SAME rival directory is
  in the prompt as burial, but the needle mapping is NOT (action-addressed recall).

The passive arm is the POSITIVE CONTROL — it must mis-bind for the A/B to be interpretable
(else the stimulus is too easy, §0.20). The competitor pool is declared on the task so the
scorer can classify mis-binds even though rivals aren't surfaced via tool returns.
"""

from __future__ import annotations

import random

from stance.tooluse.domain import Account, Order, World, gen_account, gen_id, gen_user
from stance.tooluse.tasks.base import DependencyEdge, TaskInstance, Write

_FILLER = [
    "Routine maintenance completed on the records system.",
    "No anomalies detected during the nightly audit.",
    "Customer satisfaction survey responses archived.",
    "Shipping carrier rates updated for the quarter.",
    "Warehouse inventory reconciled with no discrepancies.",
    "Support queue cleared; average handle time nominal.",
    "Backup verified; retention policy unchanged.",
]


def _est(text: str) -> int:
    return len(text) // 4


def build_binding_task(
    *, seed: int, regime: str, n_rivals: int, fill_tokens: int
) -> tuple[World, TaskInstance]:
    """`regime` ∈ {active, passive}. Same needle + `n_rivals` same-frame rivals,
    a `fill_tokens` directory; only the needle's *access* differs."""
    rng = random.Random(seed)
    taken: set[str] = set()
    holder = gen_user(rng, taken)
    taken.add(holder.id)
    needle_acct = gen_account(rng, taken, holder=holder.name)
    taken.add(needle_acct.id)
    target_order = gen_id(rng, "O", taken)
    taken.add(target_order)

    rivals: list[tuple[str, str]] = []
    accounts = {needle_acct.id: needle_acct}
    for _ in range(n_rivals):
        ro, ra = gen_id(rng, "O", taken), gen_id(rng, "A", taken)
        taken.update({ro, ra})
        rivals.append((ro, ra))
        accounts[ra] = Account(id=ra, holder=f"Holder of {ro}")  # exists → mis-bind is a valid send
    rival_accounts = [ra for _, ra in rivals]

    # the directory: same-frame rival claims (+ the needle claim, passive only) + filler
    claims = [f"Order {ro} is held by account {ra}." for ro, ra in rivals]
    if regime == "passive":
        claims.append(f"Order {target_order} is held by account {needle_acct.id}.")
    elif regime != "active":
        raise ValueError(f"unknown regime: {regime!r}")
    lines = list(claims)
    size = _est("\n".join(lines))
    while size < fill_tokens:
        line = rng.choice(_FILLER)
        lines.append(line)
        size += _est(line) + 1
    rng.shuffle(lines)
    directory = "\n".join(lines)
    prompt = (
        f"Recent order directory:\n{directory}\n\n"
        f"Message the holder of order {target_order} to confirm their refund."
    )

    if regime == "active":
        order = Order(id=target_order, account_id=needle_acct.id, days_ago=rng.randint(1, 30))
        world = World(
            users={holder.id: holder}, accounts=accounts, orders={order.id: order}, tickets={}
        )
        producer: str | None = "get_order"
    else:  # passive
        world = World(users={holder.id: holder}, accounts=accounts, orders={}, tickets={})
        producer = None

    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="send_message", args={"account_id": needle_acct.id})],
        ivs={"tier": "binding", "regime": regime, "n_rivals": n_rivals, "fill_tokens": fill_tokens},
        seed=seed,
        dependency_edge=DependencyEdge(
            consumer="send_message", needle_id=needle_acct.id,
            needle_arg="account_id", producer=producer,
        ),
        competitor_pool=rival_accounts,
    )
    return world, task
