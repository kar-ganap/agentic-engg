"""Tests for build_chain_task (#4) — the validity-critical staging.

Checks the staging invariants (not agent behavior): needle produced by get_order,
competitors same-format/distinct/collision-filtered and in the pool, fill ~ target,
depth⟂fill, control (N=0), determinism, global id uniqueness — plus that the tools
actually surface the needle + competitors so the loop can run it.
"""

from __future__ import annotations

from stance.tooluse.tasks.chain import build_chain_task
from stance.tooluse.tasks.format import build_format_task
from stance.tooluse.tasks.loopguard import build_loopguard_task
from stance.tooluse.tasks.selection import build_selection_task
from stance.tooluse.tools import dispatch, make_selection_tools, make_tools


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


def test_staged_order_is_eligible_so_the_task_is_coherent() -> None:
    # the prompt presumes a refund; an ineligible order would make a capable agent
    # correctly refuse → mislabeled failure (smoke 2026-06-12). §0.18 coherence.
    world, _ = build_chain_task(seed=4, depth=3, fill_tokens=1500, competition_n=2)
    order = next(iter(world.orders.values()))
    assert order.eligible is True


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


# --- #6 format builder -----------------------------------------------------
def test_format_task_low_fill_is_bare_chain() -> None:
    world, task = build_format_task(seed=1, arm="A", fill_tokens=0)
    assert task.ivs["tier"] == "format" and task.ivs["arm"] == "A"
    assert world.tickets == {}  # low-fill → no review history
    order = next(iter(world.orders.values()))
    assert order.eligible is True  # coherent (refund presumed)
    assert task.dependency_edge.needle_id in world.accounts  # type: ignore[union-attr]


def test_format_task_high_fill_stages_history() -> None:
    world, task = build_format_task(seed=1, arm="C", fill_tokens=9000)
    assert len(world.tickets) == 3 and task.ivs["arm"] == "C"
    assert "review" in task.prompt.lower()


def test_format_arm_b_concise_omits_the_needle() -> None:
    world, task = build_format_task(seed=2, arm="B", fill_tokens=0)
    tools = make_tools(world, "B")  # concise
    order_id = next(iter(world.orders))
    r = dispatch(tools, "get_order", {"order_id": order_id}, terminal_style="crisp")
    assert task.dependency_edge.needle_id not in r.extracted_ids  # type: ignore[union-attr]


# --- selection builder + tools --------------------------------------------
def test_selection_task_and_toolset() -> None:
    world, task = build_selection_task(seed=1, density_n=3, namespaced=False)
    assert task.expected_tool == "search_users" and task.dependency_edge is None
    assert task.expected_writes == []
    target_name = task.prompt.removeprefix("Look up the customer ").rstrip(".")
    assert any(u.name == target_name for u in world.users.values())
    tools = make_selection_tools(world, density_n=3, namespaced=False)
    names = [t.name for t in tools]
    assert names[0] == "search_users" and len(tools) == 4  # correct + 3 siblings


def test_selection_namespaced_expected_tool_and_names() -> None:
    _, task = build_selection_task(seed=1, density_n=2, namespaced=True)
    assert task.expected_tool == "user_search"
    world, _ = build_selection_task(seed=1, density_n=2, namespaced=True)
    names = [t.name for t in make_selection_tools(world, density_n=2, namespaced=True)]
    assert names[0] == "user_search" and all("_search" in n for n in names)


def test_selection_density_zero_is_control() -> None:
    world, _ = build_selection_task(seed=1, density_n=0, namespaced=False)
    assert len(make_selection_tools(world, density_n=0)) == 1  # only the correct tool


# --- loop-guard builder + ambiguous rendering ------------------------------
def test_loopguard_task_stages_ambiguity_and_resolver() -> None:
    world, task = build_loopguard_task(seed=1)
    janes = [u for u in world.users.values() if u.name.startswith("Jane")]
    assert len(janes) >= 3  # ambiguous on a first-name search
    edge = task.dependency_edge
    assert edge is not None and edge.needle_id in world.accounts  # resolvable via the order
    order = next(iter(world.orders.values()))
    assert order.account_id == edge.needle_id


def test_ambiguous_search_renders_crisp_vs_soft() -> None:
    world, _ = build_loopguard_task(seed=1)
    crisp = make_tools(world, "A", terminal_style="crisp")
    soft = make_tools(world, "A", terminal_style="soft")
    rc = dispatch(crisp, "search_users", {"query": "Jane"}, terminal_style="crisp")
    rs = dispatch(soft, "search_users", {"query": "Jane"}, terminal_style="soft")
    assert rc.error_type == "ambiguous" and rs.error_type == "ambiguous"
    assert "do not repeat" in rc.content.lower()  # crisp = actionable + anti-repeat
    assert "more results may be available" in rs.content.lower()  # soft = vague (baits a loop)
    assert rc.content != rs.content
