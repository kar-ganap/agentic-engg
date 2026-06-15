"""Selection-tier task builder — tool selection under overlap (curriculum + #2/#5).

A single-step task ("look up customer X") where the manipulation is the TOOLSET:
the correct tool sits among `density_n` confusable siblings (pre-namespace) or
disambiguated `{entity}_search` names (post-namespace). The runner builds the
toolset with `make_selection_tools(world, density_n, namespaced)`; the DV is the
agent's first tool choice vs `expected_tool`. N=0 is the control. See plan
§ "build_selection_task".
"""

from __future__ import annotations

import random

from stance.tooluse.domain import World, gen_user
from stance.tooluse.tasks.base import TaskInstance


def build_selection_task(
    *, seed: int, density_n: int, namespaced: bool = False
) -> tuple[World, TaskInstance]:
    """Build one selection task. Stages a few users incl. the target; the prompt
    asks to look the target up; `expected_tool` is the (namespaced?) user-search."""
    rng = random.Random(seed)
    taken: set[str] = set()
    target = gen_user(rng, taken)
    taken.add(target.id)
    users = {target.id: target}
    for _ in range(3):
        u = gen_user(rng, taken)
        taken.add(u.id)
        users[u.id] = u
    world = World(users=users)

    expected_tool = "user_search" if namespaced else "search_users"
    task = TaskInstance(
        prompt=f"Look up the customer {target.name}.",
        expected_writes=[],
        ivs={"tier": "selection", "density_n": density_n, "namespaced": namespaced},
        seed=seed,
        expected_tool=expected_tool,
    )
    return world, task
