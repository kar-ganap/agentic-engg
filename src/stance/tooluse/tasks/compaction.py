"""Compaction-tier task builder (§1.2, Phase 1.2 Thread B) — failure-preservation under a squeeze.

A **breadcrumb-chain audit**: the agent walks a chain of orders via `check_shipment` (each result
names the next order → sequential by construction, so the model can't batch and context
accumulates for the mid-loop compaction trigger). ~1-in-3 orders are BLOCKED; each blocked check is
an `is_error` carrying a **release ref** the final `file_report` must include. The ref lives ONLY in
the failure content — NOT in the agent's (never-compacted) action history — so summarizing the
failure away genuinely loses it (flavor-2 §1.2: the failure carries forward-info, not just
"don't-repeat"). Reuses `make_compaction_tools(chain, blocked)`.

Primary DV = **ref-recall**: fraction of true release refs the agent includes in `file_report`
(computed by the runner from the call args — mechanical, no judge). See phase-1.2-plan § Thread B.
"""

from __future__ import annotations

import random

from stance.tooluse.domain import World, gen_id
from stance.tooluse.tasks.base import TaskInstance, Write

_REASONS = ("address unverified", "payment review", "customs hold", "weight mismatch",
            "fraud screen", "restricted item")


def build_compaction_task(
    *, seed: int, n_orders: int = 9, n_blocked: int = 3
) -> tuple[World, TaskInstance]:
    """Stage a chain of `n_orders` orders; block `n_blocked` of them (never the first — a clean
    start), each with a distinct release `ref`. The agent must collect every ref while walking the
    chain and submit them all to `file_report`."""
    rng = random.Random(seed)
    taken: set[str] = set()
    chain: list[str] = []
    for _ in range(n_orders):
        oid = gen_id(rng, "O", taken)
        taken.add(oid)
        chain.append(oid)

    blocked_ids = sorted(rng.sample(chain[1:], n_blocked), key=chain.index)
    blocked: dict[str, tuple[str, str]] = {}
    true_refs: list[str] = []
    for oid in blocked_ids:
        ref = gen_id(rng, "R", taken)
        taken.add(ref)
        blocked[oid] = (rng.choice(_REASONS), ref)
        true_refs.append(ref)

    prompt = (
        f"Audit this customer's order shipments, starting with {chain[0]}. Call check_shipment on "
        "each order; every result tells you the next order to check. Some orders are BLOCKED and "
        "return a release ref — collect every ref you see. When you reach the last order, call "
        "file_report with ALL the refs you collected."
    )
    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write("file_report", {}, cardinality=1)],  # filed once; recall in runner
        ivs={"tier": "compaction", "n_orders": n_orders, "n_blocked": n_blocked},
        seed=seed,
        notes={"chain": chain, "blocked": blocked, "true_refs": true_refs},
    )
    return World(), task  # tools close over chain/blocked (task.notes), not the world
