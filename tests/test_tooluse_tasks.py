"""Tests for build_chain_task (#4) — the validity-critical staging.

Checks the staging invariants (not agent behavior): needle produced by get_order,
competitors same-format/distinct/collision-filtered and in the pool, fill ~ target,
depth⟂fill, control (N=0), determinism, global id uniqueness — plus that the tools
actually surface the needle + competitors so the loop can run it.
"""

from __future__ import annotations

import random

from stance.tooluse.domain import gen_amount
from stance.tooluse.tasks.binding import build_binding_task
from stance.tooluse.tasks.chain import build_chain_task
from stance.tooluse.tasks.diffuse import build_diffuse_task
from stance.tooluse.tasks.format import build_format_task
from stance.tooluse.tasks.loopguard import build_loopguard_task
from stance.tooluse.tasks.recency import build_recency_task
from stance.tooluse.tasks.refund import (
    SCENARIOS,
    Scenario,
    build_refund_task,
    gen_items,
    shared_stems,
)
from stance.tooluse.tasks.rolebind import _POOLS, build_rolebind_task
from stance.tooluse.tasks.selection import build_selection_task
from stance.tooluse.tools import dispatch, make_refund_tools, make_selection_tools, make_tools


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


# --- binding A/B (active vs passive) ---------------------------------------
def test_binding_active_fetches_needle_with_rivals_in_pool() -> None:
    world, task = build_binding_task(seed=1, regime="active", n_rivals=10, fill_tokens=5000)
    edge = task.dependency_edge
    assert edge is not None and edge.producer == "get_order"  # active = agent-fetched
    assert edge.needle_id in world.accounts and len(world.orders) == 1  # fetchable
    assert len(task.competitor_pool) == 10 and edge.needle_id not in task.competitor_pool
    assert all(a in world.accounts for a in task.competitor_pool)  # rivals exist → valid sends
    assert f"account {edge.needle_id}" not in task.prompt  # needle NOT dumped (must fetch)


def test_binding_passive_dumps_needle_no_producer() -> None:
    world, task = build_binding_task(seed=1, regime="passive", n_rivals=10, fill_tokens=5000)
    edge = task.dependency_edge
    assert edge is not None and edge.producer is None  # passive = not fetched
    assert world.orders == {}  # no get_order path
    assert f"account {edge.needle_id}" in task.prompt  # needle IS in the dumped directory
    assert len(task.competitor_pool) == 10  # same rival burden as active


def test_binding_same_needle_across_regimes_only_access_differs() -> None:
    # same seed → same needle/rivals; the ONLY difference is how the needle is reached
    _, ta = build_binding_task(seed=3, regime="active", n_rivals=8, fill_tokens=3000)
    _, tp = build_binding_task(seed=3, regime="passive", n_rivals=8, fill_tokens=3000)
    assert ta.dependency_edge.needle_id == tp.dependency_edge.needle_id  # type: ignore[union-attr]
    assert sorted(ta.competitor_pool) == sorted(tp.competitor_pool)


def test_binding_fill_scales_directory() -> None:
    _, small = build_binding_task(seed=1, regime="passive", n_rivals=5, fill_tokens=2000)
    _, big = build_binding_task(seed=1, regime="passive", n_rivals=5, fill_tokens=20000)
    assert len(big.prompt) > 4 * len(small.prompt)  # filler scales the dumped directory


# --- refund tier (#4-v2): self-generated semantic role-binding -------------
def test_gen_amount_distinct_and_consistent() -> None:
    rng = random.Random(0)
    taken: set[str] = set()
    amts = []
    for _ in range(20):
        base, disc, amt = gen_amount(rng, taken)
        taken.add(amt)
        amts.append(amt)
        assert abs(round(base * disc, 2) - float(amt)) < 1e-9  # amount == base × discount
    assert len(set(amts)) == 20  # collision-filtered → all distinct


def test_shared_stems_catches_inflections_not_semantics() -> None:
    assert shared_stems("trail-running shoes", "off-road trails")  # trail/trails
    assert shared_stems("racing flats", "race day")  # race/racing
    assert shared_stems("track spikes", "running track")  # track
    # semantically related but lexically distinct → NOT flagged (the property we exploit)
    assert not shared_stems("trail-running shoes", "muddy mountain switchbacks")
    assert not shared_stems("espresso machine", "the gadget for pulling morning shots")


def test_scenarios_are_stem_valid() -> None:
    # the lexical contract (so the cue-leak can't silently return): cue lex-FAR from target;
    # semantic pools lex-far from cue; lures lex-NEAR cue but lex-far target.
    for sc in SCENARIOS:
        assert not shared_stems(sc.cue, sc.target), sc.target  # no cue→target leak
        for kind in ("high", "mid", "low"):
            for d in getattr(sc, kind):
                assert not shared_stems(sc.cue, d), (sc.target, kind, d)  # not an accidental lure
        for d in sc.lure:
            assert shared_stems(sc.cue, d), (sc.target, d)  # a lure shares a cue stem
            assert not shared_stems(sc.target, d), (sc.target, d)  # but not a target stem
        alld = [sc.target, *sc.high, *sc.mid, *sc.low, *sc.lure]
        assert len(alld) == len(set(alld)), sc.target  # all distinct


def test_gen_items_lure_and_mixed() -> None:
    items, _cue, ti, lures = gen_items(random.Random(1), kind="lure", n_items=5)
    assert len(items) == 5 and len(lures) == 4  # all competitors are lures
    assert items[ti] not in lures  # the target itself is not a lure
    _, _, _, lures2 = gen_items(random.Random(1), kind="mixed", n_items=5)
    assert 0 < len(lures2) < 4  # mixed = some lures + some semantic neighbors


def _scenario_for(target_desc: str) -> Scenario:
    return next(s for s in SCENARIOS if s.target == target_desc)


def test_refund_amounts_distinct_and_pool_excludes_needle() -> None:
    _, task = build_refund_task(seed=1, kind="high", n_items=5, fill_tokens=0)
    edge = task.dependency_edge
    assert edge is not None and edge.producer == "apply_adjustment" and edge.needle_arg == "amount"
    pool = task.competitor_pool
    assert len(pool) == 4 and edge.needle_id not in pool  # N-1 rivals, needle excluded
    assert len({edge.needle_id, *pool}) == 5  # all N amounts distinct → mis-bind unambiguous


def test_refund_bypass_guard_amounts_not_in_prompt() -> None:
    # the amount is obtainable ONLY via apply_adjustment (base price is hidden) — no prompt leak.
    world, task = build_refund_task(seed=2, kind="high", n_items=5, fill_tokens=0)
    for amount in [task.dependency_edge.needle_id, *task.competitor_pool]:  # type: ignore[union-attr]
        assert amount not in task.prompt
    tools = make_refund_tools(world)
    r = dispatch(tools, "apply_adjustment", {"order_id": task.notes["target_order"]})
    assert task.dependency_edge.needle_id in r.extracted_ids  # type: ignore[union-attr]


def test_refund_cue_is_lexically_far_from_target() -> None:
    _, task = build_refund_task(seed=3, kind="high", n_items=5, fill_tokens=0)
    cue, target = task.notes["cue"], task.notes["target_description"]
    assert cue in task.prompt and target in task.prompt
    assert not shared_stems(cue, target)  # forces SEMANTIC, not lexical, cue→item matching


def test_refund_kind_draws_from_scenario_pool() -> None:
    for kind in ("low", "mid", "high", "lure"):
        _, task = build_refund_task(seed=4, kind=kind, n_items=6, fill_tokens=0)
        sc = _scenario_for(task.notes["target_description"])
        comps = set(task.notes["bindings"].keys()) - {task.notes["target_description"]}
        assert comps <= set(getattr(sc, kind)) and len(comps) == 5  # from the right pool


def test_refund_lure_amounts_recorded_for_capture_analysis() -> None:
    _, task = build_refund_task(seed=5, kind="lure", n_items=5, fill_tokens=0)
    assert len(task.notes["lure_amounts"]) == 4  # mis-binds to these = lexical capture
    assert task.dependency_edge.needle_id not in task.notes["lure_amounts"]  # type: ignore[union-attr]


def test_refund_deterministic_and_fill_scales() -> None:
    _, a = build_refund_task(seed=7, kind="mid", n_items=4, fill_tokens=0)
    _, b = build_refund_task(seed=7, kind="mid", n_items=4, fill_tokens=0)
    assert a.prompt == b.prompt and a.dependency_edge.needle_id == b.dependency_edge.needle_id  # type: ignore[union-attr]
    _, big = build_refund_task(seed=7, kind="mid", n_items=4, fill_tokens=8000)
    assert len(big.prompt) > 4 * len(a.prompt)  # neutral chatter scales the trajectory


# --- recency tier (#4-v2): proactive interference -------------------------
def test_recency_needle_is_last_total_pool_is_stale() -> None:
    _, task = build_recency_task(seed=1, n_updates=8, fill_tokens=0, semantic_similar=False)
    edge = task.dependency_edge
    assert edge is not None and edge.producer == "apply_adjustment" and edge.needle_arg == "amount"
    totals = task.notes["running_totals"]
    assert len(totals) == 8 and edge.needle_id == totals[-1]  # needle = the FINAL total
    assert task.competitor_pool == totals[:-1]  # stale totals = the interference
    assert len(set(totals)) == 8  # all distinct → unambiguous mis-bind


def test_recency_n_scales_for_free() -> None:
    for n in (5, 20, 40):
        _, task = build_recency_task(seed=2, n_updates=n, fill_tokens=0, semantic_similar=False)
        assert len(task.notes["running_totals"]) == n  # N is a free knob (no curation)


def test_recency_semantic_modifier_picks_reason_pool() -> None:
    _, sim = build_recency_task(seed=3, n_updates=5, fill_tokens=0, semantic_similar=True)
    _, dis = build_recency_task(seed=3, n_updates=5, fill_tokens=0, semantic_similar=False)
    assert all("discount" in r for r in sim.notes["reasons"])  # similar = all discounts (blurry)
    assert not all("discount" in r for r in dis.notes["reasons"])  # distinct = varied anchors


def test_recency_bypass_totals_not_in_prompt() -> None:
    _, task = build_recency_task(seed=4, n_updates=6, fill_tokens=0, semantic_similar=False)
    for amt in task.notes["running_totals"]:
        assert amt not in task.prompt  # totals obtainable ONLY via apply_adjustment


# --- rolebind tier (#4-v2): the decisive two-phase large-N test -----------
def test_rolebind_two_phase_cue_hidden_in_prompt() -> None:
    _, task = build_rolebind_task(seed=1, kind="high", n_items=8, fill_tokens=0)
    assert task.notes["cue"] not in task.prompt  # cue revealed by get_refund_request, NOT prompt
    assert task.notes["target_description"] in task.prompt  # items listed (for cue→order mapping)
    assert "STEP 1" in task.prompt and "get_refund_request" in task.prompt  # two-phase structure


def test_rolebind_needle_pool_and_amount_bypass() -> None:
    _, task = build_rolebind_task(seed=2, kind="high", n_items=8, fill_tokens=0)
    edge = task.dependency_edge
    assert edge is not None and edge.producer == "apply_adjustment" and edge.needle_arg == "amount"
    assert len(task.competitor_pool) == 7 and edge.needle_id not in task.competitor_pool
    for amt in [edge.needle_id, *task.competitor_pool]:
        assert amt not in task.prompt  # amounts obtainable ONLY via apply_adjustment (bypass)


def test_rolebind_cue_leakfree_and_from_pool() -> None:
    for kind in ("low", "high"):
        _, task = build_rolebind_task(seed=3, kind=kind, n_items=10, fill_tokens=0)
        # the cue forces SEMANTIC matching (no shared stem with the target description)
        assert not shared_stems(task.notes["cue"], task.notes["target_description"])
        descs = {d for d, _ in _POOLS[kind]}
        assert set(task.notes["bindings"].keys()) <= descs  # staged from the right pool


# --- diffuse tier (#4-v2): §1.8 low-discriminability, active vs passive ----
def test_diffuse_low_cue_and_forced_lures() -> None:
    _, t = build_diffuse_task(seed=0, cue_disc="low", regime="active", n_items=10, fill_tokens=0)
    assert t.notes["cue"] == "the tall upright one you can leave unwatered for a month"  # weak cue
    assert t.notes["target_description"] == "snake plant"
    assert len(t.notes["lure_amounts"]) == 2  # the two drought-only surface lures are forced in
    assert all(a in t.competitor_pool for a in t.notes["lure_amounts"])
    assert t.dependency_edge.needle_id not in t.notes["lure_amounts"]  # type: ignore[union-attr]


def test_diffuse_active_hides_amount_passive_dumps_it() -> None:
    _, a = build_diffuse_task(seed=0, cue_disc="low", regime="active", n_items=10, fill_tokens=0)
    _, p = build_diffuse_task(seed=0, cue_disc="low", regime="passive", n_items=10, fill_tokens=0)
    assert a.dependency_edge.producer == "apply_adjustment"  # type: ignore[union-attr]
    assert a.dependency_edge.needle_id not in a.prompt  # active: amount self-fetched
    assert a.notes["cue"] not in a.prompt  # active: cue revealed by get_refund_request
    assert p.dependency_edge.producer is None  # type: ignore[union-attr]
    assert p.dependency_edge.needle_id in p.prompt and p.notes["cue"] in p.prompt  # passive dumps


def test_diffuse_high_cue_is_the_distinctive_control() -> None:
    _, low = build_diffuse_task(seed=0, cue_disc="low", regime="active", n_items=10, fill_tokens=0)
    _, high = build_diffuse_task(seed=0, cue_disc="high", regime="active", n_items=10, fill_tokens=0)  # noqa: E501
    assert high.notes["target_description"] == low.notes["target_description"]  # same target
    assert high.notes["cue"] != low.notes["cue"]  # control uses the distinctive (high-disc) cue
    assert not shared_stems(high.notes["cue"], high.notes["target_description"])  # still no leak
