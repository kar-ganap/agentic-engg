"""Loop tests.

Specifies the loop's contract across the 8 fast unit tests + 1 slow real-API
smoke test:
  1. No-tool path returns text on `end_turn`.
  2. Single tool cycle: tool_use → dispatch → tool_result → final text.
  3. Multi-step chain: multiple tool turns accumulate correctly.
  4. max_turns hit → RuntimeError (loud failure invariant).
  5. Logger records exactly one entry per turn (instrumentation cadence).
  6. complete_fn called with the expected kwargs (wiring contract).
  7. _extract_text handles mixed/empty content correctly.
  8. Parallel tool_use blocks in one turn all get dispatched.
  9. [slow] Real-API single tool cycle against claude-haiku-4-5.
"""

from __future__ import annotations

import json
from itertools import count as _icount
from types import SimpleNamespace
from typing import Any

import pytest
from anthropic.types import TextBlock, ToolUseBlock

from stance.instrumentation import BudgetLogger
from stance.loop import _extract_text, run_loop
from stance.secrets import anthropic_api_key, has_anthropic_key
from stance.tools import ADD, ECHO
from tests.conftest import FakeCounter

# ---------------------------------------------------------------------------
# Test machinery
# ---------------------------------------------------------------------------


def _msg(content: list[Any], stop_reason: str = "end_turn") -> SimpleNamespace:
    """Build a Message-shaped object. Loop reads only .content and .stop_reason."""
    return SimpleNamespace(content=content, stop_reason=stop_reason)


def _text(s: str) -> TextBlock:
    return TextBlock(type="text", text=s, citations=None)


def _tool_use(id: str, name: str, input: dict[str, Any]) -> ToolUseBlock:
    return ToolUseBlock(type="tool_use", id=id, name=name, input=input)


def _fake_complete(responses: list[SimpleNamespace]):
    """Return a complete_fn that yields canned responses in order."""
    it = iter(responses)

    def _call(**_kw: Any) -> SimpleNamespace:
        return next(it)

    return _call


class _CompleteSpy:
    """Spy complete_fn: records each call's kwargs and yields canned responses."""

    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self._responses = iter(responses)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kw: Any) -> SimpleNamespace:
        self.calls.append(kw)
        return next(self._responses)


# ---------------------------------------------------------------------------
# 1. No-tool path
# ---------------------------------------------------------------------------


def test_no_tool_path_returns_text(tmp_path: Any) -> None:
    responses = [_msg(content=[_text("Hello!")], stop_reason="end_turn")]
    logger = BudgetLogger(tmp_path / "budget.jsonl")

    result = run_loop(
        task="Hi",
        system="Be brief.",
        tools=[],
        model="test-model",
        complete_fn=_fake_complete(responses),
        count_fn=FakeCounter(),
        logger=logger,
    )

    assert result == "Hello!"


# ---------------------------------------------------------------------------
# 2. Single tool cycle
# ---------------------------------------------------------------------------


def test_single_tool_cycle(tmp_path: Any) -> None:
    responses = [
        _msg(
            content=[
                _text("Let me add those."),
                _tool_use("toolu_1", "add", {"a": 7, "b": 12}),
            ],
            stop_reason="tool_use",
        ),
        _msg(content=[_text("7 + 12 = 19")], stop_reason="end_turn"),
    ]
    spy = _CompleteSpy(responses)
    logger = BudgetLogger(tmp_path / "budget.jsonl")

    result = run_loop(
        task="What's 7 + 12?",
        system="You are a calculator.",
        tools=[ADD],
        model="test-model",
        complete_fn=spy,
        count_fn=FakeCounter(),
        logger=logger,
    )

    assert result == "7 + 12 = 19"
    # Verify the second call saw the tool_result with the matching tool_use_id.
    second_call = spy.calls[1]
    last_msg = second_call["messages"][-1]
    assert last_msg["role"] == "user"
    result_block = last_msg["content"][0]
    assert result_block["type"] == "tool_result"
    assert result_block["tool_use_id"] == "toolu_1"
    assert result_block["content"] == "19"


# ---------------------------------------------------------------------------
# 3. Multi-step chain
# ---------------------------------------------------------------------------


def test_multi_step_chain(tmp_path: Any) -> None:
    responses = [
        _msg(
            content=[_tool_use("t1", "add", {"a": 3, "b": 4})],
            stop_reason="tool_use",
        ),
        _msg(
            content=[_tool_use("t2", "echo", {"text": "7"})],
            stop_reason="tool_use",
        ),
        _msg(content=[_text("Result: 7")], stop_reason="end_turn"),
    ]
    spy = _CompleteSpy(responses)
    logger = BudgetLogger(tmp_path / "budget.jsonl")

    result = run_loop(
        task="Add 3+4 then echo the result.",
        system="Be precise.",
        tools=[ADD, ECHO],
        model="test-model",
        complete_fn=spy,
        count_fn=FakeCounter(),
        logger=logger,
    )

    assert result == "Result: 7"
    assert len(spy.calls) == 3  # one per turn


# ---------------------------------------------------------------------------
# 4. max_turns safety
# ---------------------------------------------------------------------------


def test_max_turns_raises_runtime_error(tmp_path: Any) -> None:
    ids = _icount()

    def forever(**_kw: Any) -> SimpleNamespace:
        return _msg(
            content=[_tool_use(f"t{next(ids)}", "add", {"a": 1, "b": 1})],
            stop_reason="tool_use",
        )

    logger = BudgetLogger(tmp_path / "budget.jsonl")

    with pytest.raises(RuntimeError, match="max_turns=2"):
        run_loop(
            task="loop forever",
            system="",
            tools=[ADD],
            model="test-model",
            complete_fn=forever,
            count_fn=FakeCounter(),
            logger=logger,
            max_turns=2,
        )


# ---------------------------------------------------------------------------
# 5. Logger cadence: one entry per turn
# ---------------------------------------------------------------------------


def test_logger_records_one_entry_per_turn(tmp_path: Any) -> None:
    responses = [
        _msg(
            content=[_tool_use("t1", "add", {"a": 1, "b": 2})],
            stop_reason="tool_use",
        ),
        _msg(content=[_text("3")], stop_reason="end_turn"),
    ]
    log_path = tmp_path / "budget.jsonl"
    logger = BudgetLogger(log_path)

    run_loop(
        task="1+2",
        system="",
        tools=[ADD],
        model="test-model",
        complete_fn=_fake_complete(responses),
        count_fn=FakeCounter(),
        logger=logger,
    )

    lines = log_path.read_text().splitlines()
    assert len(lines) == 2  # 2 turns → 2 records (log fires once per model call)
    for line in lines:
        record = json.loads(line)
        assert set(record["categories"].keys()) == {
            "system",
            "tools",
            "history",
            "retrieved",
        }
        assert record["model"] == "test-model"


# ---------------------------------------------------------------------------
# 6. Wiring: complete_fn called with the expected kwargs
# ---------------------------------------------------------------------------


def test_complete_fn_called_with_expected_kwargs(tmp_path: Any) -> None:
    responses = [_msg(content=[_text("done")], stop_reason="end_turn")]
    spy = _CompleteSpy(responses)
    logger = BudgetLogger(tmp_path / "budget.jsonl")

    run_loop(
        task="hi",
        system="be brief",
        tools=[ECHO],
        model="claude-test",
        complete_fn=spy,
        count_fn=FakeCounter(),
        logger=logger,
        max_tokens=512,
    )

    assert len(spy.calls) == 1
    call = spy.calls[0]
    assert call["model"] == "claude-test"
    assert call["system"] == "be brief"
    assert call["max_tokens"] == 512
    assert call["tools"] == [ECHO.api_spec()]
    # Initial messages list contains just the user task at this point.
    assert call["messages"] == [{"role": "user", "content": "hi"}]


# ---------------------------------------------------------------------------
# 7. _extract_text behavior
# ---------------------------------------------------------------------------


def test_extract_text_handles_mixed_content() -> None:
    # Mixed: text + tool_use → only text concatenated, in order.
    blocks = [
        _text("First"),
        _tool_use("t1", "add", {"a": 1, "b": 2}),
        _text(" second"),
    ]
    assert _extract_text(blocks) == "First second"

    # Empty list → empty string.
    assert _extract_text([]) == ""

    # Only tool_use → empty string (no text to extract).
    assert _extract_text([_tool_use("t1", "add", {})]) == ""


# ---------------------------------------------------------------------------
# 8. Parallel tool_use blocks in one turn
# ---------------------------------------------------------------------------


def test_parallel_tool_calls_in_one_turn(tmp_path: Any) -> None:
    responses = [
        _msg(
            content=[
                _tool_use("t1", "add", {"a": 1, "b": 2}),
                _tool_use("t2", "echo", {"text": "hi"}),
            ],
            stop_reason="tool_use",
        ),
        _msg(content=[_text("done")], stop_reason="end_turn"),
    ]
    spy = _CompleteSpy(responses)
    logger = BudgetLogger(tmp_path / "budget.jsonl")

    run_loop(
        task="do both",
        system="",
        tools=[ADD, ECHO],
        model="test-model",
        complete_fn=spy,
        count_fn=FakeCounter(),
        logger=logger,
    )

    # Second call's last message is the user-role message containing
    # BOTH tool_results in a single content list.
    second_call = spy.calls[1]
    tool_results = second_call["messages"][-1]["content"]
    assert len(tool_results) == 2
    by_id = {tr["tool_use_id"]: tr["content"] for tr in tool_results}
    assert by_id == {"t1": "3", "t2": "hi"}  # add(1,2)=3; echo("hi")="hi"


# ---------------------------------------------------------------------------
# 9. Real-API smoke test (slow, opt-in via `make test-all`)
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(not has_anthropic_key(), reason="ANTHROPIC_API_KEY not in .env")
def test_real_api_single_tool_cycle(tmp_path: Any) -> None:
    """Smoke test against the real Anthropic API. Burns ~$0.001.

    Run via ``make test-all``. Verifies wiring against a live model end-to-end:
    the SDK signature, tool_use parse/dispatch, tool_result round-trip, and
    that the loop produces a sensible final text containing the computed sum.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=anthropic_api_key())

    def complete(**kw: Any) -> Any:
        return client.messages.create(**kw)

    def count(**kw: Any) -> int:
        return client.messages.count_tokens(**kw).input_tokens

    log_path = tmp_path / "budget.jsonl"
    logger = BudgetLogger(log_path)

    result = run_loop(
        task="What is 7 + 12? Use the add tool, then report the result.",
        system="You are a precise calculator. Use the add tool for any sum.",
        tools=[ADD],
        model="claude-haiku-4-5-20251001",
        complete_fn=complete,
        count_fn=count,
        logger=logger,
        max_turns=5,
    )

    assert "19" in result
    assert log_path.read_text().count("\n") >= 1
