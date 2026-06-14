"""#4-v2 (recency) — self-generated *proactive-interference* over a running total.

The agent applies N successive adjustments to one order via `apply_adjustment` (each call
returns the new running total — the self-generated value), then must issue the refund for the
**final** total. The stale intermediate totals are the interference (the agent retrieving an
earlier value = the documented proactive-interference error, arXiv:2506.08184, log-linear in N).

N **scales for free** — it's just `n_updates` more `gen_amount` draws, no per-item curation —
so this reaches the interference regime the curated role-binding pools (capped ~6) could not.
**Secondary modifier:** `semantic_similar` frames the adjustments with semantically-similar
reasons (loyalty/member/rewards discount…) vs distinct ones (discount/shipping/tax…), previewing
the option-1 semantic question (do blurry anchors worsen the recency confusion?).

Bypass guard: there is NO clean "current total" query — the agent must track the latest from
its own returns (faithful to the prior art's no-re-query setting). The open empirical question
the pilot answers: does message-recency (the last total is the most-recent turn) *rescue* the
agent, or does proactive interference bite at large N anyway?
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

_REASONS_SIMILAR = (
    "loyalty discount", "member discount", "rewards discount", "seasonal discount",
    "promotional discount", "clearance discount", "bundle discount", "referral discount",
)
_REASONS_DISTINCT = (
    "loyalty discount", "expedited shipping", "gift wrapping", "sales tax",
    "handling fee", "restocking credit", "price-match credit", "damage credit",
)


def build_recency_task(
    *, seed: int, n_updates: int, fill_tokens: int, semantic_similar: bool
) -> tuple[World, TaskInstance]:
    rng = random.Random(seed)
    taken: set[str] = set()
    user = gen_user(rng, taken)
    taken.add(user.id)
    acct = gen_account(rng, taken, holder=user.name)
    taken.add(acct.id)
    oid = gen_id(rng, "O", taken)
    taken.add(oid)

    amounts_taken: set[str] = set()
    running_totals: list[str] = []
    for _ in range(n_updates):
        _, _, amount = gen_amount(rng, amounts_taken)  # distinct totals → unambiguous mis-bind
        amounts_taken.add(amount)
        running_totals.append(amount)
    reason_pool = _REASONS_SIMILAR if semantic_similar else _REASONS_DISTINCT
    reasons = tuple(reason_pool[k % len(reason_pool)] for k in range(n_updates))

    order = Order(
        id=oid, account_id=acct.id, days_ago=rng.randint(1, 30),
        running_totals=tuple(running_totals), reasons=reasons,
    )
    world = World(users={user.id: user}, accounts={acct.id: acct}, orders={oid: order})

    needle = running_totals[-1]
    competitor_pool = running_totals[:-1]
    fill, _ = gen_transcript(rng, n_competitors=0, target_tokens=fill_tokens)
    prompt = (
        f"You are processing a refund for order {oid}. The customer negotiated {n_updates} "
        f"successive adjustments. Apply EACH adjustment in order with apply_adjustment (call it "
        f"once per adjustment — it returns the new running total), then issue the refund for the "
        f"FINAL running total after all {n_updates} adjustments."
        + (f"\n\n{fill}" if fill else "")
    )

    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="issue_refund", args={"amount": needle})],
        ivs={
            "tier": "recency", "n_updates": n_updates,
            "fill_tokens": fill_tokens, "semantic_similar": semantic_similar,
        },
        seed=seed,
        dependency_edge=DependencyEdge(
            consumer="issue_refund", needle_id=needle,
            needle_arg="amount", producer="apply_adjustment",
        ),
        competitor_pool=list(competitor_pool),
        notes={"order": oid, "running_totals": running_totals, "reasons": list(reasons)},
    )
    return world, task
