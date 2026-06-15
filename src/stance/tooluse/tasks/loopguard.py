"""Loop-guard tier task builder — terminal-states × loop-guard (curriculum).

Stages an AMBIGUOUS situation that baits a repeated identical call: several customers
named "Jane", and a task to message the Jane who placed a given order. A naive
`search_users("Jane")` is ambiguous → under soft terminal style the result is vague
(the agent tends to loop) → under crisp it lists matches + says don't-repeat (the
agent resolves, using the order). The disambiguator (the order → the right account)
makes it resolvable so crisp can win. `terminal_style` + `loop_guard` are cell knobs
the runner sets; the DVs are redundant_call_count / recovered / terminal_status.
See plan § "build_loopguard_task".
"""

from __future__ import annotations

import random

from stance.tooluse.domain import Account, Order, User, World, gen_id
from stance.tooluse.tasks.base import DependencyEdge, TaskInstance, Write


def build_loopguard_task(*, seed: int) -> tuple[World, TaskInstance]:
    """Build one loop-guard task: 3 customers named Jane (ambiguous on first-name
    search), the target identifiable via the order. Resolvable (crisp can win),
    ambiguous (soft baits a loop)."""
    rng = random.Random(seed)
    taken: set[str] = set()

    def _user(name: str) -> User:
        uid = gen_id(rng, "U", taken)
        taken.add(uid)
        return User(id=uid, name=name)

    target = _user("Jane Doe")
    decoys = [_user("Jane Smith"), _user("Jane Park")]
    account = Account(id=gen_id(rng, "A", taken), holder=target.name)
    taken.add(account.id)
    order = Order(id=gen_id(rng, "O", taken), account_id=account.id, days_ago=rng.randint(1, 30))
    taken.add(order.id)

    world = World(
        users={u.id: u for u in (target, *decoys)},
        accounts={account.id: account},
        orders={order.id: order},
        tickets={},
    )
    prompt = (
        f"Message the customer named Jane who placed order #{order.id} to confirm her refund. "
        f"(Note: several customers are named Jane.)"
    )
    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="send_message", args={"account_id": account.id})],
        ivs={"tier": "loopguard"},
        seed=seed,
        dependency_edge=DependencyEdge(
            producer="get_order", consumer="send_message",
            needle_id=account.id, needle_arg="account_id",
        ),
    )
    return world, task
