"""#4 chain-task builder — the validity crux (Phase 1.1).

Stages a *hold-and-use-late* task: the needle (an opaque `account_id`) is produced
early by `get_order`, held UNUSED while the agent reviews `depth` competitor-laden
support tickets (by ticket_id — NOT the needle), then consumed late by
`send_message`. The competitors are same-format, distinct-value, collision-filtered
account ids embedded in those transcripts (the diffuse pool); `fill_tokens` sizes
the transcripts (volume) independently of `depth` (distance). See
docs/phases/phase-1.1-plan.md § "Loop & generator design" and the build_chain_task
nuances. Validity gates: opaque-id needle (no synonym-bridging), entity-reference
held clear (difficulty = burial only), competition_n=0 is the control.
"""

from __future__ import annotations

import random

from stance.tooluse.domain import (
    World,
    gen_account,
    gen_order,
    gen_ticket,
    gen_transcript,
    gen_user,
)
from stance.tooluse.tasks.base import DependencyEdge, TaskInstance, Write


def build_chain_task(
    *,
    seed: int,
    depth: int,
    fill_tokens: int,
    competition_n: int,
    position: float = 0.1,
    arm: str = "A",
) -> tuple[World, TaskInstance]:
    """Build one #4 chain task. `depth` intervening tickets carry `competition_n`
    competitors total, sized to `fill_tokens` — depth (distance) and fill (volume)
    are independent knobs. `position` is the intended produce-point (achieved span
    is binned by the scorer). Returns `(World, TaskInstance)`."""
    rng = random.Random(seed)
    taken: set[str] = set()

    user = gen_user(rng, taken)
    taken.add(user.id)
    account = gen_account(rng, taken, holder=user.name)
    taken.add(account.id)
    order = gen_order(rng, taken, account_id=account.id)
    taken.add(order.id)
    needle_id = account.id  # what send_message needs; produced by get_order

    world = World(
        users={user.id: user},
        accounts={account.id: account},
        orders={order.id: order},
        tickets={},
    )

    # Distribute `competition_n` competitors + `fill_tokens` evenly across `depth`
    # intervening tickets. Competitors are reserved against `taken` (never == needle).
    n = max(1, depth)
    per_ticket_tokens = max(1, fill_tokens // n)
    remaining = competition_n
    for i in range(n):
        here = remaining // (n - i)  # n - i >= 1 across the loop
        remaining -= here
        text, comp_ids = gen_transcript(
            rng, n_competitors=here, target_tokens=per_ticket_tokens, taken=taken
        )
        taken.update(comp_ids)
        ticket = gen_ticket(
            rng, taken, account_id=account.id, transcript=text, embedded_ids=comp_ids
        )
        taken.add(ticket.id)
        world.tickets[ticket.id] = ticket

    prompt = (
        f"A customer wrote in about order #{order.id}. Before replying, review the account's "
        f"{n} most recent support ticket(s) and confirm the order is within its return window. "
        f"Then message the account holder to confirm their refund has been processed."
    )
    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="send_message", args={"account_id": needle_id})],
        ivs={
            "tier": "chain",
            "depth": depth,
            "fill_tokens": fill_tokens,
            "competition_n": competition_n,
            "position": position,
            "arm": arm,
        },
        seed=seed,
        dependency_edge=DependencyEdge(
            producer="get_order",
            consumer="send_message",
            needle_id=needle_id,
            needle_arg="account_id",
        ),
    )
    return world, task
