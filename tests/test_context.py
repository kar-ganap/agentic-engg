"""CategorizedContext tests.

Specifies the contract:
- snapshot has the four canonical keys, always; retrieved is 0 in Phase 0.0
- set_system, set_tools REPLACE (not accumulate); None / [] clear
- append_message accumulates history
- messages property returns a copy (cannot bypass the counter via mutation)
- snapshot returns a copy
- count_fn is called with the expected kwargs (wiring contract with Anthropic API)
"""

from __future__ import annotations

from stance.context import CategorizedContext
from stance.tools import ADD, ECHO
from tests.conftest import FakeCounter

# ---------------------------------------------------------------------------
# Snapshot shape
# ---------------------------------------------------------------------------


def test_snapshot_has_four_canonical_keys() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    snap = ctx.snapshot()
    assert set(snap.keys()) == {"system", "tools", "history", "retrieved"}
    assert all(isinstance(v, int) for v in snap.values())
    assert snap["retrieved"] == 0  # always 0 in Phase 0.0


# ---------------------------------------------------------------------------
# set_system: replaces; None clears
# ---------------------------------------------------------------------------


def test_set_system_replaces_does_not_accumulate() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    ctx.set_system("short")
    first = ctx.snapshot()["system"]
    ctx.set_system("much longer prompt here")
    second = ctx.snapshot()["system"]
    assert second > first
    # If it accumulated, re-setting to "short" would not return to `first`.
    ctx.set_system("short")
    third = ctx.snapshot()["system"]
    assert third == first


def test_set_system_none_clears_bucket() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    ctx.set_system("something")
    assert ctx.snapshot()["system"] > 0
    ctx.set_system(None)
    assert ctx.snapshot()["system"] == 0
    assert ctx.system is None


# ---------------------------------------------------------------------------
# set_tools: replaces; [] clears
# ---------------------------------------------------------------------------


def test_set_tools_replaces_does_not_accumulate() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    ctx.set_tools([ECHO])
    first = ctx.snapshot()["tools"]
    ctx.set_tools([ECHO, ADD])
    second = ctx.snapshot()["tools"]
    assert second > first
    ctx.set_tools([ECHO])
    third = ctx.snapshot()["tools"]
    assert third == first


def test_set_tools_empty_clears_bucket() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    ctx.set_tools([ECHO, ADD])
    assert ctx.snapshot()["tools"] > 0
    ctx.set_tools([])
    assert ctx.snapshot()["tools"] == 0
    assert ctx.tools == []


# ---------------------------------------------------------------------------
# append_message: accumulates
# ---------------------------------------------------------------------------


def test_append_message_accumulates_history() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    assert ctx.snapshot()["history"] == 0
    ctx.append_message({"role": "user", "content": "hello"})
    after_one = ctx.snapshot()["history"]
    assert after_one > 0
    ctx.append_message({"role": "assistant", "content": "world!"})
    after_two = ctx.snapshot()["history"]
    assert after_two > after_one  # second append adds, doesn't replace


def test_assistant_tool_use_count_is_deferred_until_paired() -> None:
    """Assistant messages with tool_use blocks defer counting until the
    matching tool_result message is appended. Without this deferral the
    real Anthropic count_tokens 400s on the incomplete conversation.
    """
    spy = FakeCounter()
    ctx = CategorizedContext(spy, model="test-model")
    calls_after_init = len(spy.calls)

    # Append assistant message with tool_use → should NOT trigger count_fn.
    ctx.append_message(
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "t1", "name": "echo", "input": {"text": "hi"}}
            ],
        }
    )
    assert len(spy.calls) == calls_after_init  # deferred
    assert ctx.snapshot()["history"] == 0  # history not bumped yet

    # Append matching tool_result user message → cumulative count fires,
    # history catches up to include both deferred + new contributions.
    ctx.append_message(
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "hi"}],
        }
    )
    assert len(spy.calls) == calls_after_init + 1  # one count_fn call now
    assert ctx.snapshot()["history"] > 0  # bumped, includes both messages


# ---------------------------------------------------------------------------
# Encapsulation: properties and snapshot return copies
# ---------------------------------------------------------------------------


def test_messages_property_returns_a_copy() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    ctx.append_message({"role": "user", "content": "hi"})
    snapshot_before = ctx.snapshot()
    msgs = ctx.messages
    msgs.append({"role": "user", "content": "sneaky"})
    # Internal state unaffected by mutation of the returned list
    assert len(ctx.messages) == 1
    assert ctx.snapshot() == snapshot_before


def test_snapshot_returns_a_copy() -> None:
    ctx = CategorizedContext(FakeCounter(), model="test-model")
    snap = ctx.snapshot()
    snap["system"] = 9999
    # Internal state unaffected by mutation of the returned dict
    assert ctx.snapshot()["system"] == 0


# ---------------------------------------------------------------------------
# Wiring: count_fn called with the expected kwargs (Anthropic API contract)
# ---------------------------------------------------------------------------


def test_count_fn_called_with_expected_kwargs() -> None:
    spy = FakeCounter()
    ctx = CategorizedContext(spy, model="claude-test")

    # __init__ → one call: baseline (stub message only, no system, no tools)
    assert len(spy.calls) == 1
    init_call = spy.calls[0]
    assert init_call["model"] == "claude-test"
    assert init_call["messages"] == [{"role": "user", "content": "."}]
    assert init_call["system"] is None
    assert init_call["tools"] is None

    # set_system → call with system=PROMPT + stub message
    ctx.set_system("test prompt")
    sys_call = spy.calls[-1]
    assert sys_call["model"] == "claude-test"
    assert sys_call["system"] == "test prompt"
    assert sys_call["messages"] == [{"role": "user", "content": "."}]

    # set_tools → call with tools=api_spec dicts (NOT Tool objects)
    ctx.set_tools([ECHO])
    tools_call = spy.calls[-1]
    assert tools_call["tools"] == [ECHO.api_spec()]
    assert isinstance(tools_call["tools"][0], dict)  # crucial: dict, not Tool

    # append_message → call with messages=[the message]
    msg = {"role": "user", "content": "hello there"}
    ctx.append_message(msg)
    append_call = spy.calls[-1]
    assert append_call["model"] == "claude-test"
    assert append_call["messages"] == [msg]
    assert append_call["system"] is None
    assert append_call["tools"] is None
