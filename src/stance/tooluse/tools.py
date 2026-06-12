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
from stance.tooluse.domain import World

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
        elig = "eligible" if order.eligible else "not eligible"
        prose = f"Order placed {order.days_ago} days ago, {elig} for return"
        content, ids = _render(prose, {"order": order.id, "account": order.account_id}, fmt)
        return ok(content, ids, fmt)

    def search_users(query: str, response_format: str | None = None) -> ToolResult:
        users = world.search_users(query)
        if not users:
            return err("empty", f"query '{query}'")
        fmt = resolve(response_format)
        prose = f"Found {len(users)} user(s): " + "; ".join(u.name for u in users)
        ids = {f"user{i}": u.id for i, u in enumerate(users)}
        content, rendered = _render(prose, ids, fmt)
        return ok(content, rendered, fmt)

    def get_full_ticket_history(account_id: str, response_format: str | None = None) -> ToolResult:
        if world.get_account(account_id) is None:
            return err("not_found", f"account {account_id}")
        fmt = resolve(response_format)
        tickets = world.tickets_for(account_id)
        text = "\n\n".join(t.transcript for t in tickets) or "(no ticket history)"
        embedded = [eid for t in tickets for eid in t.embedded_ids]
        return ok(text, [account_id, *embedded], fmt)

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
            "send_message",
            "Send a message to an account holder.",
            schema(
                {"account_id": {"type": "string"}, "body": {"type": "string"}},
                ["account_id", "body"],
            ),
            send_message,
        ),
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
