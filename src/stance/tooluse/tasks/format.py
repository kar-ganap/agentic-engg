"""#6 return-format task builder — the 4-arm experiment.

A SHORT `get_order → send_message` chain where the needle (`account_id`) is available
only via the right return format (arm A/B/D fixed by the cell, C agent-set). Low
competition — this tier is about handle AVAILABILITY, not rot. `fill_tokens` ≥ 1000
stages a large history the prompt asks to review (the high-fill discriminator: does
D's edge over C grow under pressure?). The `arm` is recorded in ivs; the runner
applies it via `make_tools(world, arm)`. See plan § "#6 task specifics".
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


def build_format_task(
    *, seed: int, arm: str, fill_tokens: int = 0
) -> tuple[World, TaskInstance]:
    """Build one #6 format task. `fill_tokens` ≥ 1000 → high-fill (a reviewable
    history is staged); else low-fill (bare get_order → send)."""
    rng = random.Random(seed)
    taken: set[str] = set()
    user = gen_user(rng, taken)
    taken.add(user.id)
    account = gen_account(rng, taken, holder=user.name)
    taken.add(account.id)
    order = gen_order(rng, taken, account_id=account.id, days_ago=rng.randint(1, 30))
    taken.add(order.id)
    needle_id = account.id

    world = World(
        users={user.id: user}, accounts={account.id: account},
        orders={order.id: order}, tickets={},
    )
    high = fill_tokens >= 1000
    if high:
        for _ in range(3):
            text, _ = gen_transcript(
                rng, n_competitors=0, target_tokens=fill_tokens // 3, taken=taken
            )
            ticket = gen_ticket(rng, taken, account_id=account.id, transcript=text)
            taken.add(ticket.id)
            world.tickets[ticket.id] = ticket
        prompt = (
            f"A customer wrote in about order #{order.id}. After reviewing the account's full "
            f"support history, message the account holder to confirm their refund."
        )
    else:
        prompt = (
            f"A customer wrote in about order #{order.id}. Message the account holder to confirm "
            f"their refund has been processed."
        )

    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="send_message", args={"account_id": needle_id})],
        ivs={"tier": "format", "arm": arm, "fill_tokens": fill_tokens},
        seed=seed,
        dependency_edge=DependencyEdge(
            producer="get_order", consumer="send_message",
            needle_id=needle_id, needle_arg="account_id",
        ),
    )
    return world, task
