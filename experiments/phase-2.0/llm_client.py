"""Concrete anthropic/DeepSeek-backed Client for the Thread-B arms + judge. Kept in experiments/
(not src/) so src/stance/reasoning stays provider-agnostic — arms/grader depend only on the Client
protocol. DeepSeek goes through the Anthropic-compatible endpoint to reuse the SDK (§ substrate;
verify the declared-tools path with a smoke before a real run — lessons §0.17)."""

from __future__ import annotations

from typing import Any

import anthropic

from stance.reasoning.arms import Meter
from stance.secrets import anthropic_api_key, deepseek_api_key

_DEEPSEEK_BASE = "https://api.deepseek.com/anthropic"


class LLMClient:
    """Satisfies stance.reasoning.arms.Client (a `meter` + `complete`). One instance per run so the
    Meter measures exactly that run's usage."""

    def __init__(self, *, provider: str, model: str) -> None:
        if provider == "deepseek":
            self._c = anthropic.Anthropic(base_url=_DEEPSEEK_BASE, api_key=deepseek_api_key())
        else:
            self._c = anthropic.Anthropic(api_key=anthropic_api_key())
        self.model = model
        self.meter = Meter()

    def complete(
        self, *, system: str, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None, max_tokens: int = 1024,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model, "system": system, "messages": messages, "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        resp = self._c.messages.create(**kwargs)
        self.meter.add(resp.usage)
        return resp
