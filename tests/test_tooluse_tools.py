"""Tests for the ToolResult contract + representative tool suite (Phase 1.1).

Covers the error contract (universal Layer-1 + semantic Layer-2, loud->data),
rendered (format-aware) extracted_ids, the A/B/C/D arm threading, and the
terminal_style seam.
"""

from __future__ import annotations

from stance.tooluse.domain import Account, Order, Ticket, World
from stance.tooluse.tools import ToolResult, dispatch, make_tools, render_error


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
