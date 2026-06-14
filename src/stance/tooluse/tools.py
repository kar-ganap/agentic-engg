"""ToolResult contract + a representative customer-support tool suite (Phase 1.1).

The error contract is uniform and **loud->data** (never raises): every dispatch
yields a `ToolResult` with two faces — model-facing (`content`, `is_error`) and
logging (`error_type`, `extracted_ids`, `response_format`, `size_tokens`). Errors
come in two layers: universal/structural (harness, in `dispatch`) and semantic
(per-tool `fn`). `extracted_ids` are the ids ACTUALLY rendered in `content`
(format-aware, no text parsing). The `arm` controls the return format
(A=detailed / B=concise / D=handle-block fixed; C exposes an agent-set param).
See docs/phases/phase-1.1-plan.md § "Error contract" / "decision #4".

This is a *representative* set establishing every pattern — the user extends the
full ~12-tool suite + writes the per-tier task builders + the loop on top.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from stance.tools import Tool
from stance.tooluse.domain import Order, World

_FORMATS = {"A": "detailed", "B": "concise", "D": "handle"}


def _est_tokens(text: str) -> int:
    return len(text) // 4


@dataclass
class ToolResult:
    """The uniform result of any dispatch (success or error). Two faces:
    model-facing (`content`, `is_error`) and logging (the rest)."""

    content: str
    is_error: bool = False
    error_type: str | None = None
    extracted_ids: list[str] = field(default_factory=list)
    response_format: str | None = None
    size_tokens: int = 0


# --- error messages: the terminal_style seam (crisp now, soft a thin stub) ---
_CRISP = {
    "unknown_tool": "UNKNOWN_TOOL: no tool named '{d}'. Use only the declared tools.",
    "schema:missing": "INVALID_ARGS: a required argument is missing ({d}).",
    "schema:type": "INVALID_ARGS: an argument has the wrong type ({d}).",
    "schema:enum": "INVALID_ARGS: an argument is not an allowed value ({d}).",
    "schema:unknown_arg": "INVALID_ARGS: unexpected argument ({d}).",
    "not_found": "NOT_FOUND: {d} not found; verify the id from a prior result, do not retry it.",
    "empty": "EMPTY: no results for {d}; refine the query, do not repeat it.",
    "exception": "ERROR: the tool failed ({d}).",
}


def render_error(error_type: str, details: str, terminal_style: str = "crisp") -> str:
    """Render an error message. `terminal_style` is the terminal-state IV — `crisp`
    is definitive + actionable; `soft` is an opaque stub (filled in for that tier)."""
    if terminal_style == "soft":
        return f"Error: {error_type}."
    return _CRISP.get(error_type, "ERROR: {d}").format(d=details)


# --- universal (Layer-1) schema validation (dependency-free; covers the four
#     schema:* error_types). Structured tool-calling makes these rare → kept as
#     a control, not over-built. ---
_PY: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _type_ok(value: Any, json_type: str | None) -> bool:
    if json_type is None:
        return True
    py = _PY.get(json_type)
    return isinstance(value, py) if py is not None else True


def _validate(raw_input: dict[str, Any], schema: dict[str, Any]) -> str | None:
    props: dict[str, Any] = schema.get("properties", {})
    for r in schema.get("required", []):
        if r not in raw_input:
            return "schema:missing"
    for k, v in raw_input.items():
        if k not in props:
            return "schema:unknown_arg"
        spec = props[k]
        if not _type_ok(v, spec.get("type")):
            return "schema:type"
        if "enum" in spec and v not in spec["enum"]:
            return "schema:enum"
    return None


# --- format rendering: which ids end up in `content` (the #6 mechanism) ---
def _render(prose: str, ids: dict[str, str], fmt: str) -> tuple[str, list[str]]:
    if fmt == "concise":
        return prose, []  # ids omitted — handle NOT available
    if fmt == "detailed":
        inline = ", ".join(f"{k} {v}" for k, v in ids.items())
        return f"{prose} ({inline})", list(ids.values())
    if fmt == "handle":
        block = ", ".join(f"{k}={v}" for k, v in ids.items())
        return f"{prose}\n[ids: {block}]", list(ids.values())
    raise ValueError(f"unknown format: {fmt!r}")


def make_tools(world: World, arm: str, terminal_style: str = "crisp") -> tuple[Tool, ...]:
    """Per-run tool factory. `arm` ∈ {A,B,C,D}: A/B/D fix the return format and
    expose NO `response_format` param; C exposes the enum param (agent-set) — the
    schema difference IS the #6 treatment (choice vs no-choice)."""
    agent_chooses = arm == "C"
    if arm == "C":
        fixed: str | None = None
    elif arm in _FORMATS:
        fixed = _FORMATS[arm]
    else:
        raise ValueError(f"unknown arm: {arm!r}")

    def resolve(rf: str | None) -> str:
        if agent_chooses:
            return rf or "concise"
        assert fixed is not None
        return fixed

    def schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
        p = dict(props)
        if agent_chooses:
            p["response_format"] = {"type": "string", "enum": ["concise", "detailed"]}
        return {"type": "object", "properties": p, "required": required}

    def err(error_type: str, details: str) -> ToolResult:
        return ToolResult(
            content=render_error(error_type, details, terminal_style),
            is_error=True,
            error_type=error_type,
        )

    def ok(content: str, ids: list[str], fmt: str) -> ToolResult:
        return ToolResult(
            content=content,
            extracted_ids=ids,
            response_format=fmt,
            size_tokens=_est_tokens(content),
        )

    def get_order(order_id: str, response_format: str | None = None) -> ToolResult:
        order = world.orders.get(order_id)
        if order is None:
            return err("not_found", f"order {order_id}")
        fmt = resolve(response_format)
        ticket_ids = [t.id for t in world.tickets_for(order.account_id)]
        elig = "eligible" if order.eligible else "not eligible"
        prose = (
            f"Order placed {order.days_ago} days ago, {elig} for return; "
            f"{len(ticket_ids)} related ticket(s)"
        )
        # surface the account (the needle) + the ticket handles (for the review sub-goal);
        # reviewing a ticket goes by ticket_id, so it does NOT re-touch the needle (#4 hold).
        ids = {"order": order.id, "account": order.account_id}
        for i, tid in enumerate(ticket_ids):
            ids[f"ticket{i}"] = tid
        content, rendered = _render(prose, ids, fmt)
        return ok(content, rendered, fmt)

    def search_users(query: str, response_format: str | None = None) -> ToolResult:
        users = world.search_users(query)
        if not users:
            return err("empty", f"query '{query}'")
        fmt = resolve(response_format)
        if len(users) > 1:
            # AMBIGUOUS terminal state — the loop-guard tier's bait, rendered per
            # terminal_style: crisp resolves (list + anti-repeat), soft loops (vague).
            ids = [u.id for u in users]
            if terminal_style == "soft":
                content = f"Found {len(users)} results. More results may be available."
            else:
                listing = "; ".join(f"{u.id} {u.name}" for u in users)
                content = (
                    f"AMBIGUOUS: {len(users)} users match '{query}' ({listing}). "
                    f"Pick one by id or refine the query; do not repeat this search."
                )
            return ToolResult(
                content=content, is_error=True, error_type="ambiguous",
                extracted_ids=ids, response_format=fmt, size_tokens=_est_tokens(content),
            )
        content, rendered = _render(f"Found 1 user: {users[0].name}", {"user": users[0].id}, fmt)
        return ok(content, rendered, fmt)

    def get_full_ticket_history(account_id: str, response_format: str | None = None) -> ToolResult:
        if world.get_account(account_id) is None:
            return err("not_found", f"account {account_id}")
        fmt = resolve(response_format)
        tickets = world.tickets_for(account_id)
        text = "\n\n".join(t.transcript for t in tickets) or "(no ticket history)"
        embedded = [eid for t in tickets for eid in t.embedded_ids]
        return ok(text, [account_id, *embedded], fmt)

    def get_ticket(ticket_id: str, response_format: str | None = None) -> ToolResult:
        ticket = world.tickets.get(ticket_id)
        if ticket is None:
            return err("not_found", f"ticket {ticket_id}")
        fmt = resolve(response_format)
        # large output keyed by ticket_id (NOT the needle); surfaces the competitor ids it embeds.
        return ok(ticket.transcript or "(empty)", [ticket_id, *ticket.embedded_ids], fmt)

    def send_message(account_id: str, body: str, response_format: str | None = None) -> ToolResult:
        if world.get_account(account_id) is None:
            return err("not_found", f"account {account_id}")
        fmt = resolve(response_format)
        prose = f"Message sent to the holder of account ({len(body)} chars)"
        content, ids = _render(prose, {"account": account_id}, fmt)
        return ok(content, ids, fmt)

    return (
        Tool(
            "get_order",
            "Look up an order by id; returns its status and the owning account.",
            schema({"order_id": {"type": "string"}}, ["order_id"]),
            get_order,
        ),
        Tool(
            "search_users",
            "Find users whose name matches a query.",
            schema({"query": {"type": "string"}}, ["query"]),
            search_users,
        ),
        Tool(
            "get_full_ticket_history",
            "Return the full conversation history for an account (large).",
            schema({"account_id": {"type": "string"}}, ["account_id"]),
            get_full_ticket_history,
        ),
        Tool(
            "get_ticket",
            "Return the full transcript of one support ticket by id (large).",
            schema({"ticket_id": {"type": "string"}}, ["ticket_id"]),
            get_ticket,
        ),
        Tool(
            "send_message",
            "Send a message to an account holder.",
            schema(
                {"account_id": {"type": "string"}, "body": {"type": "string"}},
                ["account_id", "body"],
            ),
            send_message,
        ),
    )


# Selection tier: confusable siblings (pre-namespace) vs disambiguated (post).
_SIBLINGS_PRE = ["find_user", "lookup_user", "search_accounts", "search_kb", "search"]
_SIBLINGS_POST = ["account_search", "kb_search", "ticket_search", "order_search", "entity_search"]


def make_selection_tools(
    world: World, density_n: int, namespaced: bool = False
) -> tuple[Tool, ...]:
    """Build a selection-tier toolset: the correct user-search tool + `density_n`
    confusable siblings. Pre-namespace siblings are synonyms/cross-entity (confusable);
    post-namespace are `{entity}_search` (disambiguated). The §0.18 sweet-spot lives in
    how confusable the *names* are. Returns tools that each take a `query`."""
    correct = "user_search" if namespaced else "search_users"
    siblings = (_SIBLINGS_POST if namespaced else _SIBLINGS_PRE)[:density_n]
    schema = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}

    def user_fn(query: str) -> ToolResult:
        users = world.search_users(query)
        if not users:
            return ToolResult(content="No matching users.", is_error=True, error_type="empty")
        names = "; ".join(f"{u.id} {u.name}" for u in users)
        return ToolResult(content=f"Users: {names}", extracted_ids=[u.id for u in users],
                          size_tokens=_est_tokens(names))

    def sibling_fn(query: str) -> ToolResult:
        return ToolResult(content="No matching records.", is_error=True, error_type="empty")

    tools = [Tool(correct, "Find a customer (user) by name.", schema, user_fn)]
    for name in siblings:
        tools.append(Tool(name, f"Search {name.replace('_', ' ')}.", schema, sibling_fn))
    return tuple(tools)


# --- refund tier (#4-v2): self-generated semantic role-binding interference ---
# `return_shape` is the #4ii fix lever (how apply_adjustment re-states each binding);
# `doc_quality` is the competing lever (tool-description guidance) for the ordering test.
_REFUND_DOCS = {
    "terse": {
        "apply_adjustment": "Compute the refund for an order.",
        "list_adjustments": "List every refund computed so far.",
        "issue_refund": "Issue a refund for an order.",
    },
    "verbose": {
        "apply_adjustment": (
            "Compute the negotiated refund for ONE order (base price × the agreed discount). "
            "Call once per order; the returned amount is authoritative — record which order it "
            "belongs to, since amounts are easy to confuse across similar items."
        ),
        "list_adjustments": (
            "Re-list every refund computed so far, each with its item, so you can re-confirm "
            "the correct amount before issuing rather than relying on memory."
        ),
        "issue_refund": (
            "Issue a refund for an order. Use the EXACT amount computed for THAT order — "
            "double-check the item↔amount binding; a wrong amount refunds the wrong sum."
        ),
    },
}
_RETURN_SHAPES = ("flat", "tagged", "structured")


def make_refund_tools(
    world: World,
    *,
    return_shape: str = "flat",
    doc_quality: str = "terse",
    terminal_style: str = "crisp",
) -> tuple[Tool, ...]:
    """Refund-tier toolset. The agent computes a distinct refund per item via
    `apply_adjustment` (the in-flight, self-generated value — no tool exposes the base
    price, the bypass guard), then `issue_refund(amount=…)` routes one to a referent.
    `return_shape` controls how each computed binding renders (flat = amount only, no item
    tag → max interference; tagged/structured re-state the item↔amount binding → the #4ii
    fix). `list_adjustments` is the measured re-fetch path (re-derives all pairs; removes
    memory load but NOT the semantic discrimination among confusable descriptions)."""
    docs = _REFUND_DOCS.get(doc_quality)
    if docs is None:
        raise ValueError(f"unknown doc_quality: {doc_quality!r}")
    if return_shape not in _RETURN_SHAPES:
        raise ValueError(f"unknown return_shape: {return_shape!r}")

    def err(error_type: str, details: str) -> ToolResult:
        return ToolResult(
            content=render_error(error_type, details, terminal_style),
            is_error=True,
            error_type=error_type,
        )

    def amount_of(order: Order) -> str:
        assert order.base_price is not None and order.discount is not None
        return f"{round(order.base_price * order.discount, 2):.2f}"

    def render_one(order: Order, amount: str) -> str:
        if return_shape == "flat":
            return f"Refund amount: ${amount}"  # no item tag — binding only in the call arg
        if return_shape == "tagged":
            return f"{order.description} → refund ${amount}"
        return f'{{"item": "{order.description}", "amount": {amount}}}'  # structured

    def result(content: str, ids: list[str]) -> ToolResult:
        return ToolResult(content=content, extracted_ids=ids, size_tokens=_est_tokens(content))

    def apply_adjustment(order_id: str) -> ToolResult:
        order = world.orders.get(order_id)
        if order is None or order.base_price is None:
            return err("not_found", f"order {order_id}")
        amount = amount_of(order)
        return result(render_one(order, amount), [amount])  # surface the amount (the needle)

    def list_adjustments() -> ToolResult:
        items = [o for o in world.orders.values() if o.base_price is not None]
        lines = [f"{o.description} → refund ${amount_of(o)}" for o in items]
        body = "Computed refunds:\n" + "\n".join(lines) if lines else "(no refunds computed)"
        return result(body, [amount_of(o) for o in items])  # all pairs (re-fetch path)

    def issue_refund(order_id: str, amount: float) -> ToolResult:
        if world.orders.get(order_id) is None:
            return err("not_found", f"order {order_id}")
        content = f"Refund of ${amount} issued for order {order_id}."
        return result(content, [])

    def schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
        return {"type": "object", "properties": props, "required": required}

    return (
        Tool("apply_adjustment", docs["apply_adjustment"],
             schema({"order_id": {"type": "string"}}, ["order_id"]), apply_adjustment),
        Tool("list_adjustments", docs["list_adjustments"], schema({}, []), list_adjustments),
        Tool("issue_refund", docs["issue_refund"],
             schema({"order_id": {"type": "string"}, "amount": {"type": "number"}},
                    ["order_id", "amount"]), issue_refund),
    )


# --- rolebind tier (#4-v2, the decisive two-phase large-N test) ---------------------------
def make_rolebind_tools(
    world: World, *, cue: str, terminal_style: str = "crisp"
) -> tuple[Tool, ...]:
    """Two-phase role-binding toolset. `apply_adjustment(order_id)` computes one refund (flat —
    the item↔amount binding lives only in the call); `list_adjustments` is the measured re-fetch
    (all pairs; at high overlap the cue→item match is still hard). `get_refund_request` is GATED:
    it reveals the consume `cue` only after EVERY order has been adjusted — so the agent can't
    shortcut to the target, and the target was computed mid-sequence (no recency rescue)."""
    adjusted: set[str] = set()
    refund_orders = {oid for oid, o in world.orders.items() if o.base_price is not None}

    def err(error_type: str, details: str) -> ToolResult:
        return ToolResult(content=render_error(error_type, details, terminal_style),
                          is_error=True, error_type=error_type)

    def amount_of(order: Order) -> str:
        assert order.base_price is not None and order.discount is not None
        return f"{round(order.base_price * order.discount, 2):.2f}"

    def apply_adjustment(order_id: str) -> ToolResult:
        order = world.orders.get(order_id)
        if order is None or order.base_price is None:
            return err("not_found", f"order {order_id}")
        adjusted.add(order_id)
        amount = amount_of(order)
        content = f"Computed refund: ${amount}."  # flat — binding only in the call args
        return ToolResult(content=content, extracted_ids=[amount], size_tokens=_est_tokens(content))

    def list_adjustments() -> ToolResult:
        items = [o for o in world.orders.values() if o.base_price is not None]
        lines = [f"{o.description} → refund ${amount_of(o)}" for o in items]
        body = "Computed refunds:\n" + "\n".join(lines) if lines else "(none computed)"
        return ToolResult(content=body, extracted_ids=[amount_of(o) for o in items],
                          size_tokens=_est_tokens(body))

    def get_refund_request() -> ToolResult:
        if not refund_orders <= adjusted:  # GATE: all must be computed first
            done, total = len(adjusted & refund_orders), len(refund_orders)
            return ToolResult(content=f"Compute the refund for all items first ({done}/{total} "
                              f"done).", is_error=True, error_type="empty")
        content = f"Issue the refund for: {cue}."
        return ToolResult(content=content, size_tokens=_est_tokens(content))

    def issue_refund(order_id: str, amount: float) -> ToolResult:
        if world.orders.get(order_id) is None:
            return err("not_found", f"order {order_id}")
        content = f"Refund of ${amount} issued for order {order_id}."
        return ToolResult(content=content, size_tokens=_est_tokens(content))

    def schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
        return {"type": "object", "properties": props, "required": required}

    return (
        Tool("apply_adjustment", "Compute the refund for one order.",
             schema({"order_id": {"type": "string"}}, ["order_id"]), apply_adjustment),
        Tool("list_adjustments", "List every refund computed so far, with its item.",
             schema({}, []), list_adjustments),
        Tool("get_refund_request", "Reveal which single refund to issue (only after all are "
             "computed).", schema({}, []), get_refund_request),
        Tool("issue_refund", "Issue a refund for an order.",
             schema({"order_id": {"type": "string"}, "amount": {"type": "number"}},
                    ["order_id", "amount"]), issue_refund),
    )


# --- recency tier (#4-v2, proactive interference) -----------------------------------------
def make_recency_tools(world: World, *, terminal_style: str = "crisp") -> tuple[Tool, ...]:
    """Recency-tier toolset. `apply_adjustment(order_id)` is STATEFUL — each call advances a
    per-order cursor and returns the next running total (the self-generated value the agent must
    later recall). There is deliberately NO current-total query (the bypass guard): the agent
    tracks the latest from its own returns. `issue_refund(order_id, amount)` is the write."""
    cursor: dict[str, int] = {}

    def err(error_type: str, details: str) -> ToolResult:
        return ToolResult(
            content=render_error(error_type, details, terminal_style),
            is_error=True, error_type=error_type,
        )

    def apply_adjustment(order_id: str) -> ToolResult:
        order = world.orders.get(order_id)
        if order is None or order.running_totals is None:
            return err("not_found", f"order {order_id}")
        totals = order.running_totals
        reasons = order.reasons or ()
        k = cursor.get(order_id, 0)
        if k >= len(totals):
            return ToolResult(content="All adjustments already applied; no further changes.",
                              size_tokens=4)  # no total re-surfaced (no late shortcut)
        cursor[order_id] = k + 1
        reason = reasons[k] if k < len(reasons) else "adjustment"
        total = totals[k]
        content = f"Adjustment {k + 1} of {len(totals)} ({reason}); running total ${total}."
        return ToolResult(content=content, extracted_ids=[total], size_tokens=_est_tokens(content))

    def issue_refund(order_id: str, amount: float) -> ToolResult:
        if world.orders.get(order_id) is None:
            return err("not_found", f"order {order_id}")
        content = f"Refund of ${amount} issued for order {order_id}."
        return ToolResult(content=content, size_tokens=_est_tokens(content))

    def schema(props: dict[str, Any], required: list[str]) -> dict[str, Any]:
        return {"type": "object", "properties": props, "required": required}

    return (
        Tool("apply_adjustment", "Apply the next negotiated adjustment to an order; returns the "
             "new running total.", schema({"order_id": {"type": "string"}}, ["order_id"]),
             apply_adjustment),
        Tool("issue_refund", "Issue a refund for an order.",
             schema({"order_id": {"type": "string"}, "amount": {"type": "number"}},
                    ["order_id", "amount"]), issue_refund),
    )


def dispatch(
    tools: Sequence[Tool],
    name: str,
    raw_input: dict[str, Any],
    *,
    terminal_style: str = "crisp",
) -> ToolResult:
    """Run one tool call — the universal (Layer-1) error layer. Never raises:
    unknown-tool / schema-invalid / fn-exception all become a `ToolResult`."""
    by_name = {t.name: t for t in tools}
    tool = by_name.get(name)
    if tool is None:
        return ToolResult(
            content=render_error("unknown_tool", name, terminal_style),
            is_error=True,
            error_type="unknown_tool",
        )
    schema_err = _validate(raw_input, tool.input_schema)
    if schema_err is not None:
        return ToolResult(
            content=render_error(schema_err, f"{name} {raw_input}", terminal_style),
            is_error=True,
            error_type=schema_err,
        )
    try:
        result = tool.fn(**raw_input)
    except Exception as e:  # loud->data: a tool bug is a data point, not a crash
        return ToolResult(
            content=render_error("exception", str(e), terminal_style),
            is_error=True,
            error_type="exception",
        )
    assert isinstance(result, ToolResult)
    return result
