"""Tool surface tests.

Specifies the contract for `Tool` and the trivial `echo` + `add` tools:
- echo is a faithful round-trip (including empty input)
- add sums integers (including zero and negatives)
- the api_spec dicts match the Anthropic API's expected shape and exclude `fn`
- Tool instances are immutable (frozen dataclass invariant)
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from stance.tools import ADD, ECHO


def test_echo_roundtrips() -> None:
    assert ECHO.fn(text="hello world") == "hello world"
    assert ECHO.fn(text="") == ""


def test_echo_api_spec_shape() -> None:
    spec = ECHO.api_spec()
    assert set(spec.keys()) == {"name", "description", "input_schema"}
    assert spec["name"] == "echo"
    assert spec["input_schema"]["required"] == ["text"]
    assert "text" in spec["input_schema"]["properties"]


def test_tool_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        ECHO.name = "something_else"  # type: ignore[misc]


def test_add_sums_integers() -> None:
    assert ADD.fn(a=2, b=3) == 5
    assert ADD.fn(a=0, b=0) == 0
    assert ADD.fn(a=-3, b=5) == 2


def test_add_api_spec_shape() -> None:
    spec = ADD.api_spec()
    assert set(spec.keys()) == {"name", "description", "input_schema"}
    assert spec["name"] == "add"
    assert spec["input_schema"]["required"] == ["a", "b"]
    assert spec["input_schema"]["properties"]["a"]["type"] == "integer"
    assert spec["input_schema"]["properties"]["b"]["type"] == "integer"
