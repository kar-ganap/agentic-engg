"""Tests for the ToolResult contract + representative tool suite (Phase 1.1).

Covers the error contract (universal Layer-1 + semantic Layer-2, loud->data),
rendered (format-aware) extracted_ids, the A/B/C/D arm threading, and the
terminal_style seam.
"""

from __future__ import annotations

from stance.tooluse.domain import Account, Order, Ticket, World
from stance.tooluse.tools import (
    ToolResult,
    dispatch,
    make_recency_tools,
    make_refund_tools,
    make_rolebind_tools,
    make_tools,
    render_error,
)


def _world() -> tuple[World, str, str]:
    """A tiny fixed world; returns (world, an order id, its account id)."""
    world = World()
    acct = Account(id="A-7731", holder="Jane Doe")
    world.accounts[acct.id] = acct
    order = Order(id="O-1042", account_id=acct.id, days_ago=12)
    world.orders[order.id] = order
    return world, order.id, acct.id


def test_toolresult_two_faces_defaults() -> None:
    r = ToolResult(content="ok")
    assert r.content == "ok" and r.is_error is False
    assert r.error_type is None and r.extracted_ids == [] and r.size_tokens == 0


def test_dispatch_unknown_tool_is_data_not_raise() -> None:
    world, _, _ = _world()
    tools = make_tools(world, "A")
    r = dispatch(tools, "no_such_tool", {}, terminal_style="crisp")
    assert r.is_error and r.error_type == "unknown_tool"


def test_dispatch_schema_missing_required() -> None:
    world, _, _ = _world()
    tools = make_tools(world, "A")
    r = dispatch(tools, "get_order", {}, terminal_style="crisp")  # missing order_id
    assert r.is_error and r.error_type == "schema:missing"


def test_dispatch_schema_unknown_arg() -> None:
    world, oid, _ = _world()
    tools = make_tools(world, "A")
    r = dispatch(tools, "get_order", {"order_id": oid, "bogus": 1}, terminal_style="crisp")
    assert r.is_error and r.error_type == "schema:unknown_arg"


def test_dispatch_schema_enum_on_arm_c_format() -> None:
    world, oid, _ = _world()
    tools = make_tools(world, "C")  # arm C exposes response_format enum
    r = dispatch(
        tools, "get_order", {"order_id": oid, "response_format": "verbose"}, terminal_style="crisp"
    )
    assert r.is_error and r.error_type == "schema:enum"


def test_get_order_not_found_is_semantic_error() -> None:
    world, _, _ = _world()
    tools = make_tools(world, "A")
    r = dispatch(tools, "get_order", {"order_id": "O-0000"}, terminal_style="crisp")
    assert r.is_error and r.error_type == "not_found"


def test_arm_a_detailed_surfaces_ids_arm_b_concise_omits() -> None:
    world, oid, acct = _world()
    a = dispatch(make_tools(world, "A"), "get_order", {"order_id": oid}, terminal_style="crisp")
    b = dispatch(make_tools(world, "B"), "get_order", {"order_id": oid}, terminal_style="crisp")
    assert acct in a.extracted_ids and acct in a.content   # detailed renders the needle
    assert b.extracted_ids == [] and acct not in b.content  # concise omits it (the #6 mechanism)
    assert a.response_format == "detailed" and b.response_format == "concise"


def test_arm_d_handle_block_surfaces_ids() -> None:
    world, oid, acct = _world()
    d = dispatch(make_tools(world, "D"), "get_order", {"order_id": oid}, terminal_style="crisp")
    assert acct in d.extracted_ids and acct in d.content
    assert d.response_format == "handle"


def test_arm_c_agent_chooses_format() -> None:
    world, oid, acct = _world()
    tools = make_tools(world, "C")
    concise = dispatch(
        tools, "get_order", {"order_id": oid, "response_format": "concise"}, terminal_style="crisp"
    )
    detailed = dispatch(
        tools, "get_order", {"order_id": oid, "response_format": "detailed"}, terminal_style="crisp"
    )
    assert concise.extracted_ids == [] and acct in detailed.extracted_ids


def test_send_message_write_not_found_vs_success() -> None:
    world, _, acct = _world()
    tools = make_tools(world, "A")
    miss = dispatch(
        tools, "send_message", {"account_id": "A-0000", "body": "hi"}, terminal_style="crisp"
    )
    ok = dispatch(tools, "send_message", {"account_id": acct, "body": "hi"}, terminal_style="crisp")
    assert miss.is_error and miss.error_type == "not_found"
    assert not ok.is_error and acct in ok.extracted_ids


def test_large_output_tool_reports_embedded_ids() -> None:
    world = World()
    acct = Account(id="A-7731", holder="Jane Doe")
    world.accounts[acct.id] = acct
    world.tickets["T-1"] = Ticket(
        id="T-1", account_id=acct.id, subject="x",
        transcript="...big transcript mentioning A-4402 and A-9981...",
        embedded_ids=("A-4402", "A-9981"),
    )
    r = dispatch(
        make_tools(world, "A"),
        "get_full_ticket_history",
        {"account_id": acct.id},
        terminal_style="crisp",
    )
    assert not r.is_error
    assert "A-4402" in r.extracted_ids and "A-9981" in r.extracted_ids
    assert r.size_tokens > 0


def test_get_ticket_returns_transcript_and_embedded_ids() -> None:
    world = World()
    acct = Account(id="A-7731", holder="Jane Doe")
    world.accounts[acct.id] = acct
    world.tickets["T-1"] = Ticket(
        id="T-1", account_id=acct.id, subject="x",
        transcript="...transcript mentioning A-4402...", embedded_ids=("A-4402",),
    )
    tools = make_tools(world, "A")
    ok = dispatch(tools, "get_ticket", {"ticket_id": "T-1"}, terminal_style="crisp")
    assert not ok.is_error and "A-4402" in ok.extracted_ids and ok.size_tokens > 0
    miss = dispatch(tools, "get_ticket", {"ticket_id": "T-9"}, terminal_style="crisp")
    assert miss.is_error and miss.error_type == "not_found"


def test_terminal_style_crisp_vs_soft_differ() -> None:
    crisp = render_error("not_found", "order O-0000", terminal_style="crisp")
    soft = render_error("not_found", "order O-0000", terminal_style="soft")
    assert crisp != soft
    assert "O-0000" in crisp  # crisp is specific/actionable


# --- refund tier (#4-v2) --------------------------------------------------
def _refund_world() -> World:
    world = World(accounts={"A-1": Account(id="A-1", holder="Jane Doe")})
    # O-1 → 200×0.25 = 50.00 (target); O-2 → 160×0.30 = 48.00 (competitor)
    world.orders["O-1"] = Order("O-1", "A-1", days_ago=5, base_price=200.0,
                                discount=0.25, description="trail-running shoes")
    world.orders["O-2"] = Order("O-2", "A-1", days_ago=5, base_price=160.0,
                                discount=0.30, description="road-running shoes")
    return world


def test_apply_adjustment_surfaces_amount_and_renders_per_shape() -> None:
    world = _refund_world()
    for shape, must_have, must_lack in [
        ("flat", "50.00", "trail-running shoes"),   # flat = amount only, NO item tag
        ("tagged", "trail-running shoes", None),     # tagged re-states the binding
        ("structured", '"item"', None),              # structured object
    ]:
        tools = make_refund_tools(world, return_shape=shape)
        r = dispatch(tools, "apply_adjustment", {"order_id": "O-1"})
        assert not r.is_error and r.extracted_ids == ["50.00"]  # surfaces the needle amount
        assert must_have in r.content
        if must_lack is not None:
            assert must_lack not in r.content


def test_apply_adjustment_not_found() -> None:
    tools = make_refund_tools(_refund_world())
    r = dispatch(tools, "apply_adjustment", {"order_id": "O-9"})
    assert r.is_error and r.error_type == "not_found"


def test_list_adjustments_returns_all_pairs() -> None:
    tools = make_refund_tools(_refund_world())
    r = dispatch(tools, "list_adjustments", {})
    assert not r.is_error
    assert set(r.extracted_ids) == {"50.00", "48.00"}  # all amounts (re-fetch path)
    # both descriptions present → re-fetch removes memory load but NOT semantic discrimination
    assert "trail-running shoes" in r.content and "road-running shoes" in r.content


def test_issue_refund_write_success_and_not_found() -> None:
    tools = make_refund_tools(_refund_world())
    ok = dispatch(tools, "issue_refund", {"order_id": "O-1", "amount": 50.0})
    assert not ok.is_error  # the write-boundary signals success
    miss = dispatch(tools, "issue_refund", {"order_id": "O-9", "amount": 50.0})
    assert miss.is_error and miss.error_type == "not_found"


def test_doc_quality_changes_descriptions_not_behavior() -> None:
    terse = {t.name: t.description for t in make_refund_tools(_refund_world(), doc_quality="terse")}
    verbose = {t.name: t.description
               for t in make_refund_tools(_refund_world(), doc_quality="verbose")}
    # the verbose arm adds binding guidance; behavior (amount) is identical
    assert len(verbose["issue_refund"]) > len(terse["issue_refund"])
    assert "binding" in verbose["issue_refund"].lower()


# --- recency tier (#4-v2) -------------------------------------------------
def _recency_world() -> World:
    world = World(accounts={"A-1": Account(id="A-1", holder="Jane")})
    world.orders["O-1"] = Order(
        "O-1", "A-1", days_ago=5,
        running_totals=("50.00", "60.00", "70.00"), reasons=("a", "b", "c"),
    )
    return world


def test_recency_apply_adjustment_is_stateful() -> None:
    tools = make_recency_tools(_recency_world())
    seen = [dispatch(tools, "apply_adjustment", {"order_id": "O-1"}) for _ in range(4)]
    # advances one running total per call, then exhausts WITHOUT re-surfacing the final
    assert [r.extracted_ids for r in seen] == [["50.00"], ["60.00"], ["70.00"], []]
    assert "already applied" in seen[3].content  # no late shortcut to the final total


def test_recency_tools_have_no_current_value_query() -> None:
    tools = make_recency_tools(_recency_world())
    assert {t.name for t in tools} == {"apply_adjustment", "issue_refund"}  # bypass guard
    assert not dispatch(tools, "issue_refund", {"order_id": "O-1", "amount": 70.0}).is_error
    assert dispatch(tools, "issue_refund", {"order_id": "O-9", "amount": 70.0}).is_error


# --- rolebind tier (#4-v2) ------------------------------------------------
def _rolebind_world() -> World:
    world = World(accounts={"A-1": Account(id="A-1", holder="Jane")})
    world.orders["O-1"] = Order("O-1", "A-1", days_ago=5, base_price=100.0,
                                discount=0.25, description="snake plant")
    world.orders["O-2"] = Order("O-2", "A-1", days_ago=5, base_price=80.0,
                                discount=0.50, description="pothos")
    return world


def test_rolebind_get_refund_request_is_gated() -> None:
    tools = make_rolebind_tools(_rolebind_world(), cue="the trailing vine")
    assert dispatch(tools, "get_refund_request", {}).is_error  # nothing computed yet
    dispatch(tools, "apply_adjustment", {"order_id": "O-1"})
    assert dispatch(tools, "get_refund_request", {}).is_error  # only 1/2 done → still gated
    dispatch(tools, "apply_adjustment", {"order_id": "O-2"})
    revealed = dispatch(tools, "get_refund_request", {})
    assert not revealed.is_error and "the trailing vine" in revealed.content  # all done → cue


def test_rolebind_apply_and_list() -> None:
    tools = make_rolebind_tools(_rolebind_world(), cue="x")
    r = dispatch(tools, "apply_adjustment", {"order_id": "O-1"})
    assert not r.is_error and r.extracted_ids == ["25.00"]  # 100 × 0.25
    lst = dispatch(tools, "list_adjustments", {})
    assert set(lst.extracted_ids) == {"25.00", "40.00"} and "snake plant" in lst.content
