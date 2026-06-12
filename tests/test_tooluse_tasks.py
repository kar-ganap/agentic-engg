"""Tests for build_chain_task (#4) — the validity-critical staging.

Checks the staging invariants (not agent behavior): needle produced by get_order,
competitors same-format/distinct/collision-filtered and in the pool, fill ~ target,
depth⟂fill, control (N=0), determinism, global id uniqueness — plus that the tools
actually surface the needle + competitors so the loop can run it.
"""

from __future__ import annotations

from stance.tooluse.tasks.chain import build_chain_task
from stance.tooluse.tools import dispatch, make_tools


def test_needle_is_produced_by_get_order() -> None:
    world, task = build_chain_task(seed=1, depth=4, fill_tokens=4000, competition_n=5)
    edge = task.dependency_edge
    assert edge is not None
    assert edge.producer == "get_order" and edge.consumer == "send_message"
    assert edge.needle_arg == "account_id"
    needle = edge.needle_id
    assert needle in world.accounts  # the needle account exists
    order = next(iter(world.orders.values()))
    assert order.account_id == needle  # get_order(order) → the needle account


def test_competitors_unique_distinct_from_needle_and_in_pool() -> None:
    world, task = build_chain_task(seed=1, depth=4, fill_tokens=4000, competition_n=5)
    needle = task.dependency_edge.needle_id  # type: ignore[union-attr]
    embedded = [cid for t in world.tickets.values() for cid in t.embedded_ids]
    assert len(embedded) == 5 and len(set(embedded)) == 5  # exactly N, unique
    assert needle not in embedded  # collision-filtered vs the needle
    assert all(cid.startswith("A-") for cid in embedded)  # same format as the needle
    # every embedded id actually appears in its transcript (in the pool the agent sees)
    assert all(c in t.transcript for t in world.tickets.values() for c in t.embedded_ids)


def test_zero_competition_is_the_control() -> None:
    world, task = build_chain_task(seed=3, depth=3, fill_tokens=1500, competition_n=0)
    embedded = [cid for t in world.tickets.values() for cid in t.embedded_ids]
    assert embedded == []  # control: no competitors → the §0.18 zero-point
    assert task.ivs["competition_n"] == 0


def test_depth_and_fill_are_independent_knobs() -> None:
    # same fill, different depth → same total volume, different # tickets (distance)
    w_shallow, _ = build_chain_task(seed=5, depth=2, fill_tokens=8000, competition_n=2)
    w_deep, _ = build_chain_task(seed=5, depth=8, fill_tokens=8000, competition_n=2)
    assert len(w_shallow.tickets) == 2 and len(w_deep.tickets) == 8
    vol_shallow = sum(len(t.transcript) for t in w_shallow.tickets.values())
    vol_deep = sum(len(t.transcript) for t in w_deep.tickets.values())
    # volume is comparable despite very different depth (decoupled)
    assert abs(vol_shallow - vol_deep) < 0.5 * max(vol_shallow, vol_deep)


def test_expected_write_targets_the_needle() -> None:
    _, task = build_chain_task(seed=2, depth=2, fill_tokens=1000, competition_n=2)
    w = task.expected_writes[0]
    assert w.action == "send_message"
    assert w.args["account_id"] == task.dependency_edge.needle_id  # type: ignore[union-attr]
    assert w.cardinality == 1


def test_globally_unique_ids() -> None:
    world, _ = build_chain_task(seed=11, depth=5, fill_tokens=5000, competition_n=8)
    all_ids = (
        [u.id for u in world.users.values()]
        + [a.id for a in world.accounts.values()]
        + [o.id for o in world.orders.values()]
        + [t.id for t in world.tickets.values()]
        + [cid for t in world.tickets.values() for cid in t.embedded_ids]
    )
    assert len(all_ids) == len(set(all_ids))  # needle, entities, competitors all distinct


def test_deterministic() -> None:
    w1, t1 = build_chain_task(seed=7, depth=3, fill_tokens=2000, competition_n=3)
    w2, t2 = build_chain_task(seed=7, depth=3, fill_tokens=2000, competition_n=3)
    assert t1.prompt == t2.prompt
    assert t1.dependency_edge.needle_id == t2.dependency_edge.needle_id  # type: ignore[union-attr]
    assert sorted(w1.tickets) == sorted(w2.tickets)


def test_tools_surface_needle_and_competitors_end_to_end() -> None:
    world, task = build_chain_task(seed=5, depth=3, fill_tokens=2000, competition_n=4, arm="A")
    tools = make_tools(world, "A")
    order_id = next(iter(world.orders))
    needle = task.dependency_edge.needle_id  # type: ignore[union-attr]
    r = dispatch(tools, "get_order", {"order_id": order_id}, terminal_style="crisp")
    assert needle in r.extracted_ids  # get_order surfaces the needle (held for send_message)
    ticket_ids = list(world.tickets)
    assert all(tid in r.extracted_ids for tid in ticket_ids)  # ticket handles for the review
    # reviewing a ticket (by ticket_id, not the needle) surfaces its competitors
    rt = dispatch(tools, "get_ticket", {"ticket_id": ticket_ids[0]}, terminal_style="crisp")
    assert all(c in rt.extracted_ids for c in world.tickets[ticket_ids[0]].embedded_ids)
