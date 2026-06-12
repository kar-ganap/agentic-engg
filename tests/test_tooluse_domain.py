"""Tests for the Phase 1.1 customer-support domain substrate.

Load-bearing properties: deterministic from seed, collision-filtered ids
(uniqueness is required for needle/competitor disambiguation — plan req #2),
transcripts embed the requested competitor count, World lookups behave.
"""

from __future__ import annotations

import random

from stance.tooluse.domain import (
    Order,
    build_world,
    gen_account,
    gen_id,
    gen_order,
    gen_transcript,
    gen_user,
)


def test_gen_id_format_and_collision_filter() -> None:
    rng = random.Random(1)
    taken = {"U-0000"}
    ids = {gen_id(rng, "U", taken) for _ in range(50)}
    assert all(i.startswith("U-") and len(i) == 6 for i in ids)
    assert "U-0000" not in ids  # collision-filtered against `taken`


def test_gen_id_deterministic() -> None:
    a = [gen_id(random.Random(7), "A") for _ in range(1)]
    b = [gen_id(random.Random(7), "A") for _ in range(1)]
    assert a == b  # same seed -> same id


def test_order_eligibility_derives_from_age() -> None:
    assert Order(id="O-1", account_id="A-1", days_ago=10).eligible is True
    assert Order(id="O-2", account_id="A-1", days_ago=45).eligible is False


def test_generators_use_taken_set_for_uniqueness() -> None:
    rng = random.Random(3)
    taken: set[str] = set()
    u = gen_user(rng, taken)
    taken.add(u.id)
    a = gen_account(rng, taken, holder=u.name)
    taken.add(a.id)
    o = gen_order(rng, taken, account_id=a.id)
    assert len({u.id, a.id, o.id}) == 3
    assert o.account_id == a.id


def test_gen_transcript_embeds_requested_competitor_count() -> None:
    rng = random.Random(5)
    text, comp_ids = gen_transcript(rng, n_competitors=4, target_tokens=2000)
    assert len(comp_ids) == 4
    assert len(set(comp_ids)) == 4  # unique
    assert all(cid in text for cid in comp_ids)  # actually rendered in the text
    assert all(cid.startswith("A-") for cid in comp_ids)  # same format as account ids


def test_gen_transcript_hits_target_size_roughly() -> None:
    rng = random.Random(5)
    text, _ = gen_transcript(rng, n_competitors=2, target_tokens=4000)
    est = len(text) // 4
    assert 3000 <= est <= 6000  # within a reasonable band of the 4000 target


def test_gen_transcript_deterministic() -> None:
    t1, c1 = gen_transcript(random.Random(9), n_competitors=3, target_tokens=1500)
    t2, c2 = gen_transcript(random.Random(9), n_competitors=3, target_tokens=1500)
    assert t1 == t2 and c1 == c2


def test_build_world_and_lookups() -> None:
    world = build_world(random.Random(2), n_accounts=5, orders_per_account=2)
    # an account exists and resolves
    some_acct = next(iter(world.accounts))
    assert world.get_account(some_acct) is not None
    assert world.get_account("A-9999-nope") is None
    # orders_for returns that account's orders
    orders = world.orders_for(some_acct)
    assert all(o.account_id == some_acct for o in orders)
    # search_users matches on a name substring
    a_user = next(iter(world.users.values()))
    first = a_user.name.split()[0]
    hits = world.search_users(first)
    assert a_user in hits


def test_world_ids_are_globally_unique() -> None:
    world = build_world(random.Random(11), n_accounts=6, orders_per_account=3)
    all_ids = (
        [u.id for u in world.users.values()]
        + [a.id for a in world.accounts.values()]
        + [o.id for o in world.orders.values()]
        + [t.id for t in world.tickets.values()]
    )
    assert len(all_ids) == len(set(all_ids))  # no collisions anywhere
