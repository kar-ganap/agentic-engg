"""B8 — framework bake-off (Phase 2.1, Module 6 L192). The SAME agent across raw loop, LangGraph,
and CrewAI on one held-out task; compare success / cost / latency. The IV is the framework, so the
MODEL is held constant — Haiku (Claude), because LangGraph/CrewAI tool-calling is best-supported on
Claude and this is not a model claim. Adoption threshold (honest): if the raw loop wins, say so.

Task: "Look up the customer NAME and report their id" over the §1.10 selection toolset (search_users
+ confusable siblings incl. the `lookup_user` attractor). Success = the target id in the
final answer (cross-framework-clean containment DV). Held-out seeds (101+).

    uv run python experiments/phase-2.1/bakeoff.py --frameworks raw,langgraph --seeds 3   # dry
    uv run python experiments/phase-2.1/bakeoff.py --seeds 5 --density 1 --go   # isolate overhead
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from stance import secrets
from stance.eval.accuracy import is_hit
from stance.tooluse.tasks.selection import build_selection_task
from stance.tooluse.tools import make_selection_tools

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase-2.0"))
from llm_client import LLMClient  # noqa: E402

HAIKU = "claude-haiku-4-5-20251001"
SYSTEM = "You are a customer-support agent. Use the available tools to handle the request."
DENSITY = 3


@dataclass
class ArmResult:
    answer: str
    input_tokens: int
    output_tokens: int
    latency_s: float


def make_case(seed: int, density: int) -> tuple[str, tuple[Any, ...], str]:
    world, task = build_selection_task(seed=seed, density_n=density, namespaced=False)
    name = task.prompt.removeprefix("Look up the customer ").rstrip(".")
    target = next(u for u in world.users.values() if u.name == name)
    prompt = f"Look up the customer {name} and report their exact customer id."
    return prompt, make_selection_tools(world, density, False), target.id


def run_raw(prompt: str, tools: tuple[Any, ...]) -> ArmResult:
    client = LLMClient(provider="anthropic", model=HAIKU)
    specs = [t.api_spec() for t in tools]
    byname = {t.name: t for t in tools}
    msgs: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    t0 = time.perf_counter()
    answer = ""
    for _ in range(6):
        resp = client.complete(system=SYSTEM, messages=msgs, tools=specs, max_tokens=512)
        uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if not uses:
            answer = "".join(getattr(b, "text", "") for b in resp.content
                             if getattr(b, "type", None) == "text")
            break
        msgs.append({"role": "assistant", "content": resp.content})
        results = []
        for tu in uses:
            out = byname[tu.name].fn(**tu.input)
            results.append({"type": "tool_result", "tool_use_id": tu.id,
                            "content": out.content, "is_error": bool(out.is_error)})
        msgs.append({"role": "user", "content": results})
    return ArmResult(answer, client.meter.input_tokens, client.meter.output_tokens,
                     time.perf_counter() - t0)


def run_langgraph(prompt: str, tools: tuple[Any, ...]) -> ArmResult:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.tools import StructuredTool
    from langgraph.prebuilt import create_react_agent

    def mk(t: Any) -> Any:
        def _call(query: str) -> str:
            return str(t.fn(query=query).content)
        return StructuredTool.from_function(func=_call, name=t.name, description=t.description)

    model = ChatAnthropic(model=HAIKU, api_key=secrets.anthropic_api_key(), max_tokens=512)
    agent = create_react_agent(model, [mk(t) for t in tools], prompt=SYSTEM)
    t0 = time.perf_counter()
    out = agent.invoke({"messages": [("user", prompt)]})
    dt = time.perf_counter() - t0
    msgs = out["messages"]
    answer = str(msgs[-1].content)
    tin = sum((getattr(m, "usage_metadata", None) or {}).get("input_tokens", 0) for m in msgs)
    tout = sum((getattr(m, "usage_metadata", None) or {}).get("output_tokens", 0) for m in msgs)
    return ArmResult(answer, tin, tout, dt)


RUNNERS = {"raw": run_raw, "langgraph": run_langgraph}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frameworks", default="raw,langgraph")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--density", type=int, default=DENSITY,
                    help="sibling count; 1 = no attractor (isolates framework overhead)")
    ap.add_argument("--go", action="store_true")
    args = ap.parse_args()
    frameworks = [f.strip() for f in args.frameworks.split(",")]
    seeds = list(range(101, 101 + args.seeds))
    print(f"bake-off — model={HAIKU} (held constant); frameworks={frameworks}; seeds={seeds}; "
          f"density={args.density}")
    print(f"  {len(frameworks) * len(seeds)} runs; task=lookup+report-id over the §1.10 toolset")
    if not args.go:
        print("DRY-RUN — pass --go. DV = target id in final answer (success) + tokens + latency.")
        return

    results: dict[str, list[tuple[bool, ArmResult]]] = {f: [] for f in frameworks}
    for seed in seeds:
        prompt, tools, target_id = make_case(seed, args.density)
        for f in frameworks:
            r = RUNNERS[f](prompt, tools)
            ok = is_hit(r.answer, target_id)
            results[f].append((ok, r))
            print(f"  seed={seed} {f:<10} success={ok} "
                  f"tok={r.input_tokens + r.output_tokens} {r.latency_s:.1f}s")

    print(f"\n{'framework':<12} {'success':>8} {'tok(mean)':>10} {'lat(mean)':>10}")
    for f in frameworks:
        rs = results[f]
        sr = mean(ok for ok, _ in rs)
        tk = mean(r.input_tokens + r.output_tokens for _, r in rs)
        lt = mean(r.latency_s for _, r in rs)
        print(f"{f:<12} {sr:>8.2f} {tk:>10.0f} {lt:>8.1f}s")


if __name__ == "__main__":
    main()
