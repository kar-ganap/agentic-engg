"""#4-v2 (rolebind) — the DECISIVE test: large-N, two-phase, semantic role-binding.

This is the one regime that defeats all three rescue mechanisms the earlier nulls revealed:
- **two-phase** (compute ALL refunds, THEN a gated `get_refund_request` reveals which to issue)
  → no shortcut-to-target, and the target was computed mid-sequence → **no recency rescue**;
- **large N** → recalling 1-of-N is no longer trivial → **no easy-recall rescue**;
- **no-leak cue** over a **confusable** pool → the cue→item match needs meaning, and even the
  re-fetched `list_adjustments` is hard to disambiguate at high overlap → **no lexical/re-fetch
  rescue**.

If high-overlap large-N collapses → the agentic interference regime is found + isolated. If it
holds → agentic self-generation robustness is strong/general. `kind="low"` (distinct items) is
the negative control (re-fetch trivially disambiguates → should hold).

The pools/cues are USER-OWNED (learning-first); this is a stem-validated FIRST DRAFT — refine
the confusable set + cues (and extend for larger N). See .claude/plans/ (refund #4-v2).
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

# low overlap (negative control) — distinct categories; cue lex-far; re-fetch disambiguates easily.
_LOW_ITEMS: tuple[tuple[str, str], ...] = (
    ("travel umbrella", "the thing that keeps rain off you"),
    ("desk lamp", "the light for your workspace"),
    ("kitchen blender", "the appliance for whipping up smoothies"),
    ("yoga mat", "the cushioned pad for floor stretches"),
    ("wireless headphones", "the device for private listening"),
    ("steel water bottle", "the refillable container for drinks"),
    ("frying pan", "the cookware for searing eggs"),
    ("alarm clock", "the bedside gadget that wakes you"),
    ("backpack", "the bag you carry on both shoulders"),
    ("sunglasses", "the tinted eyewear for bright days"),
    ("coffee mug", "the handled cup for hot drinks"),
    ("bath towel", "the large cloth for drying off"),
    ("screwdriver", "the hand tool that drives fasteners"),
    ("throw pillow", "the small cushion for a couch"),
    ("table fan", "the gadget that blows cool air"),
    ("flashlight", "the handheld beam for the dark"),
    ("leather wallet", "the fold that holds cash and cards"),
    ("wall clock", "the timepiece you hang up"),
)

# high overlap (treatment) — all houseplants (confusable category); cue keys on a DISTINCTIVE
# feature, lex-far from the plant's name, so it's the cue→item meaning match that's hard.
_HIGH_ITEMS: tuple[tuple[str, str], ...] = (
    ("snake plant", "the stiff upright one with tall sword-like blades"),
    ("pothos", "the trailing vine with heart-shaped foliage that's hard to kill"),
    ("monstera", "the climber prized for big leaves full of natural holes"),
    ("fiddle-leaf fig", "the fussy indoor tree with broad violin-shaped leaves"),
    ("ZZ plant", "the glossy waxy one that thrives on being forgotten"),
    ("peace lily", "the shade-lover whose single white hood wilts when thirsty"),
    ("spider plant", "the one that dangles tiny offspring on long runners"),
    ("rubber tree", "the upright with thick burgundy oval leaves that ooze sap"),
    ("aloe vera", "the toothed-edge succulent whose gel soothes a burn"),
    ("boston fern", "the feathery frond basket that craves damp air"),
    ("jade plant", "the chunky plump-leaved miniature shaped like a little tree"),
    ("english ivy", "the cascading creeper that grips brick and trellis"),
    ("moth orchid", "the elegant bloomer grown in bark chips, never soil"),
    ("barrel cactus", "the ribbed desert globe bristling with spines"),
    ("calathea", "the patterned one whose leaves fold shut after dark"),
    ("string of pearls", "the succulent that spills cascading rows of little green beads"),
)

_POOLS = {"low": _LOW_ITEMS, "high": _HIGH_ITEMS}


def build_rolebind_task(
    *, seed: int, kind: str, n_items: int, fill_tokens: int
) -> tuple[World, TaskInstance]:
    if kind not in _POOLS:
        raise ValueError(f"unknown kind: {kind!r}")
    pool = _POOLS[kind]
    if not 2 <= n_items <= len(pool):
        raise ValueError(f"n_items must be 2..{len(pool)} for kind={kind!r}")
    rng = random.Random(seed)
    taken: set[str] = set()
    user = gen_user(rng, taken)
    taken.add(user.id)
    acct = gen_account(rng, taken, holder=user.name)
    taken.add(acct.id)

    chosen = rng.sample(pool, n_items)
    target_index = rng.randrange(n_items)
    cue = chosen[target_index][1]

    items: list[tuple[Order, str]] = []  # (order, amount)
    order_lines: list[str] = []
    amounts_taken: set[str] = set()
    for desc, _ in chosen:
        base, disc, amount = gen_amount(rng, amounts_taken)
        amounts_taken.add(amount)
        oid = gen_id(rng, "O", taken)
        taken.add(oid)
        order = Order(
            id=oid, account_id=acct.id, days_ago=rng.randint(1, 30),
            base_price=base, discount=disc, description=desc,
        )
        items.append((order, amount))
        order_lines.append(f"- Order {oid}: {desc} (customer negotiated {int(disc * 100)}% off)")

    world = World(
        users={user.id: user}, accounts={acct.id: acct}, orders={o.id: o for o, _ in items}
    )
    target_order, target_amount = items[target_index]
    competitor_pool = [a for i, (_, a) in enumerate(items) if i != target_index]

    fill, _ = gen_transcript(rng, n_competitors=0, target_tokens=fill_tokens)
    prompt = (
        f"You are processing a customer's return of {n_items} items. The base price of each is "
        f"internal — only the tool knows it.\n"
        f"STEP 1 — compute the refund for EVERY item below with apply_adjustment (call it once per "
        f"order id).\n"
        f"STEP 2 — once ALL {n_items} are computed, call get_refund_request to learn which single "
        f"item's refund to issue, then issue it with issue_refund.\n\n"
        + "\n".join(order_lines)
        + (f"\n\n{fill}" if fill else "")
        + "\n\nBegin step 1 now."
    )

    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="issue_refund", args={"amount": target_amount})],
        ivs={"tier": "rolebind", "kind": kind, "n_items": n_items, "fill_tokens": fill_tokens},
        seed=seed,
        dependency_edge=DependencyEdge(
            consumer="issue_refund", needle_id=target_amount,
            needle_arg="amount", producer="apply_adjustment",
        ),
        competitor_pool=competitor_pool,
        notes={
            "target_order": target_order.id,
            "target_description": target_order.description,
            "cue": cue,
            "bindings": {o.description: a for o, a in items},
        },
    )
    return world, task
