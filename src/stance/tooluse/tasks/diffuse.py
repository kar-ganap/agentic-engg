"""#4-v2 (diffuse) — the §1.8 LOW-discriminability test, active vs passive.

Tests the structural claim from `results-4v2.md`: §1.8's diffuse collapse lives in the
**identification** step (cue→item), upstream of where self-generation's advantage applies — so a
low-discriminability cue should collapse retrieval *whether or not* the values are self-generated
(#4 ⊆ §1.8, no agentic immunity).

A **low-disc** cue is weak/indirect: its SURFACE words pull toward same-type **forced lures**,
while its MEANING uniquely picks the target (e.g. *"the spiky one you'd reach for to soothe a
sunburn"* → aloe, with "spiky" luring toward cactus/snake plant). The **high-disc** cue (each
item's distinctive `_HIGH_ITEMS` cue) is the control. `regime` ∈ {active (two-phase self-fetch),
passive (the bindings dumped in the prompt)} — only the *provenance* of the values differs.

Predictions (pre-registered): high-disc holds (both regimes); **low-disc collapses** (mis-binds to
the surface lures) in active AND passive → #4 ⊆ §1.8. Caveat: the §1.8 sweet-spot (weak-enough to
collapse, unique-enough to grade) is hard — the control gates interpretation (§0.18).
"""

from __future__ import annotations

import random

from stance.tooluse.domain import (
    Order,
    World,
    gen_account,
    gen_amount,
    gen_id,
    gen_transcript,
    gen_user,
)
from stance.tooluse.tasks.base import DependencyEdge, TaskInstance, Write
from stance.tooluse.tasks.rolebind import _HIGH_ITEMS

_HIGH_CUE = {desc: cue for desc, cue in _HIGH_ITEMS}

# USER-OWNED crafted low-disc cues: (target → (weak two-attribute cue, forced-lure descriptions)).
# Each cue names TWO attributes; the TARGET matches both, each forced lure matches only the SURFACE
# attribute (RULER-style multi-key). A model attending to the surface attribute is captured by a
# lure; the target is the unique full match. (No stem-validation here — surface pull is the point.)
_LOW_DISC: dict[str, tuple[str, tuple[str, ...]]] = {
    "snake plant": (  # tall-upright + drought; lures are drought-only (globe/rosette, not upright)
        "the tall upright one you can leave unwatered for a month",
        ("barrel cactus", "aloe vera"),
    ),
    "moth orchid": (  # showy-flowering + soilless; lure is flowering-only (in soil)
        "the showy flowering one that grows without any potting soil",
        ("peace lily",),
    ),
    "boston fern": (  # feathery + humidity; lures are humidity-only (not feathery)
        "the feathery one that thrives in a steamy bathroom",
        ("calathea", "peace lily"),
    ),
}


def build_diffuse_task(
    *, seed: int, cue_disc: str, regime: str, n_items: int, fill_tokens: int
) -> tuple[World, TaskInstance]:
    if cue_disc not in ("high", "low"):
        raise ValueError(f"unknown cue_disc: {cue_disc!r}")
    if regime not in ("active", "passive"):
        raise ValueError(f"unknown regime: {regime!r}")
    rng = random.Random(seed)
    taken: set[str] = set()
    user = gen_user(rng, taken)
    taken.add(user.id)
    acct = gen_account(rng, taken, holder=user.name)
    taken.add(acct.id)

    targets = list(_LOW_DISC)
    target_desc = targets[seed % len(targets)]
    low_cue, forced = _LOW_DISC[target_desc]
    pool = [d for d, _ in _HIGH_ITEMS]
    others = [d for d in pool if d != target_desc and d not in forced]
    rng.shuffle(others)
    chosen = [target_desc, *forced] + others[: max(0, n_items - 1 - len(forced))]
    chosen = chosen[:n_items]
    rng.shuffle(chosen)
    cue = low_cue if cue_disc == "low" else _HIGH_CUE[target_desc]

    items: list[tuple[Order, str]] = []
    amounts_taken: set[str] = set()
    for desc in chosen:
        base, disc, amount = gen_amount(rng, amounts_taken)
        amounts_taken.add(amount)
        oid = gen_id(rng, "O", taken)
        taken.add(oid)
        items.append((Order(
            id=oid, account_id=acct.id, days_ago=rng.randint(1, 30),
            base_price=base, discount=disc, description=desc,
        ), amount))

    world = World(
        users={user.id: user}, accounts={acct.id: acct}, orders={o.id: o for o, _ in items}
    )
    ti = next(i for i, (o, _) in enumerate(items) if o.description == target_desc)
    target_order, target_amount = items[ti]
    competitor_pool = [a for i, (_, a) in enumerate(items) if i != ti]

    fill, _ = gen_transcript(rng, n_competitors=0, target_tokens=fill_tokens)
    if regime == "active":  # two-phase self-fetch; cue revealed by get_refund_request (NOT prompt)
        lines = [f"- Order {o.id}: {o.description}" for o, _ in items]
        prompt = (
            f"You are processing a customer's return of {n_items} items.\n"
            f"STEP 1 — compute the refund for EVERY item below with apply_adjustment.\n"
            f"STEP 2 — once all are computed, call get_refund_request to learn which to issue, "
            f"then issue it with issue_refund.\n\n" + "\n".join(lines)
            + (f"\n\n{fill}" if fill else "") + "\n\nBegin step 1 now."
        )
        producer: str | None = "apply_adjustment"
    else:  # passive: the (item→amount) bindings are dumped in the prompt; cue given directly
        lines = [f"- Order {o.id} ({o.description}): refund ${a}" for o, a in items]
        prompt = (
            "Here are the customer's pre-computed refunds:\n" + "\n".join(lines)
            + (f"\n\n{fill}" if fill else "")
            + f"\n\nIssue the refund for {cue}."
        )
        producer = None

    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="issue_refund", args={"amount": target_amount})],
        ivs={
            "tier": "diffuse", "cue_disc": cue_disc, "regime": regime,
            "n_items": n_items, "fill_tokens": fill_tokens,
        },
        seed=seed,
        dependency_edge=DependencyEdge(
            consumer="issue_refund", needle_id=target_amount,
            needle_arg="amount", producer=producer,
        ),
        competitor_pool=competitor_pool,
        notes={
            "target_order": target_order.id, "target_description": target_desc, "cue": cue,
            # mis-binds to these = the model fell for the surface lures (the §1.8 failure mode)
            "lure_amounts": [a for o, a in items if o.description in forced],
            "bindings": {o.description: a for o, a in items},
        },
    )
    return world, task
