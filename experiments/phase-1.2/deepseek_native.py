"""DeepSeek NATIVE (OpenAI-format /chat/completions) complete_fn for run_tool_loop — to localize
the content-recovery anomaly seen on the /anthropic shim (does DeepSeek's own endpoint honor
content ablation, or reproduce it too?). Raw httpx (no openai dep); translates the loop's
Anthropic-format messages <-> OpenAI format, returns an Anthropic-shaped response object.

If native HONORS the ablation (removed value stays removed), the anomaly is the shim and we can
measure §1.2 on DeepSeek-native. If native reproduces it too, it's deeper. Optional per-request
wire capture (`on_wire`) for airtight verification of what native receives.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import httpx
from anthropic.types import TextBlock, ToolUseBlock

_NATIVE_URL = "https://api.deepseek.com/chat/completions"


def _to_openai_messages(
    system: str, messages: list[dict[str, Any]], remap_salt: str | None = None
) -> list[dict[str, Any]]:
    """Translate Anthropic-format messages to OpenAI format. If `remap_salt` is set, every tool
    call gets a FRESH id (consistent within this request, different across requests) — to test
    whether the DeepSeek content-recovery anomaly is keyed on stable tool_call_ids."""
    id_map: dict[str, str] = {}

    def _rid(old: str) -> str:
        if remap_salt is None:
            return old
        if old not in id_map:
            id_map[old] = f"call_{remap_salt}_{len(id_map)}"
        return id_map[old]

    out: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for m in messages:
        role, content = m["role"], m["content"]
        if role == "user":
            if isinstance(content, str):
                out.append({"role": "user", "content": content})
            else:  # a tool_result carrier (list of blocks)
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        out.append({"role": "tool", "tool_call_id": _rid(b["tool_use_id"]),
                                    "content": str(b.get("content", ""))})
                    elif isinstance(b, dict) and b.get("type") == "text":
                        out.append({"role": "user", "content": b.get("text", "")})
        else:  # assistant: list of anthropic block objects (TextBlock / ToolUseBlock)
            text_parts, tool_calls = [], []
            for b in content if isinstance(content, list) else []:
                t = b.get("type") if isinstance(b, dict) else getattr(b, "type", None)
                if t == "text":
                    text_parts.append(b["text"] if isinstance(b, dict) else b.text)
                elif t == "tool_use":
                    bid = b["id"] if isinstance(b, dict) else b.id
                    name = b["name"] if isinstance(b, dict) else b.name
                    args = b["input"] if isinstance(b, dict) else b.input
                    tool_calls.append({"id": _rid(bid), "type": "function",
                                       "function": {"name": name, "arguments": json.dumps(args)}})
            msg: dict[str, Any] = {"role": "assistant",
                                   "content": "".join(text_parts) if text_parts else None}
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)
    return out


def _from_openai_response(data: dict[str, Any]) -> SimpleNamespace:
    msg = data["choices"][0]["message"]
    blocks: list[Any] = []
    if msg.get("content"):
        blocks.append(TextBlock(type="text", text=msg["content"], citations=None))
    for tc in msg.get("tool_calls") or []:
        fn = tc["function"]
        try:
            args = json.loads(fn["arguments"] or "{}")
        except json.JSONDecodeError:
            args = {}
        blocks.append(ToolUseBlock(type="tool_use", id=tc["id"], name=fn["name"], input=args))
    stop = "tool_use" if (msg.get("tool_calls")) else "end_turn"
    u = data.get("usage", {})
    usage = SimpleNamespace(
        input_tokens=u.get("prompt_tokens", 0), output_tokens=u.get("completion_tokens", 0),
        cache_read_input_tokens=u.get("prompt_cache_hit_tokens", 0), cache_creation_input_tokens=0,
    )
    return SimpleNamespace(content=blocks, stop_reason=stop, usage=usage)


def make_native_complete_fn(
    *, api_key: str, on_wire: Callable[[bytes], None] | None = None, bust_cache: bool = False,
    remap_ids: bool = False,
) -> Callable[..., Any]:
    """Return a complete_fn(model, system, tools, messages, max_tokens) hitting DeepSeek native.
    `remap_ids` gives every tool call a fresh per-request id (breaks cross-request id linkage)."""
    client = httpx.Client(timeout=120.0)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    n = {"i": 0}

    def complete(*, model: str, system: str, tools: list[dict[str, Any]],
                 messages: list[dict[str, Any]], max_tokens: int) -> Any:
        n["i"] += 1
        sys_prompt = f"[req {n['i']:05d}-nc] {system}" if bust_cache else system
        salt = f"{n['i']:05d}" if remap_ids else None
        oai_tools = [{"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
            for t in tools]
        payload = {"model": model, "messages": _to_openai_messages(sys_prompt, messages, salt),
                   "tools": oai_tools, "max_tokens": max_tokens}
        body = json.dumps(payload).encode()
        if on_wire is not None:
            on_wire(body)
        resp = client.post(_NATIVE_URL, headers=headers, content=body)
        resp.raise_for_status()
        return _from_openai_response(resp.json())

    return complete
