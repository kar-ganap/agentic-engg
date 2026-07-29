# Phase 2.1 B8 — Framework bake-off (Module 6 L192): raw loop vs LangGraph vs CrewAI

> "Run the same agent across 3 frameworks on one task set; compare success/cost/latency." Model held
> **constant** (Haiku) — the IV is the framework. Task: lookup-and-report-id over the §1.10 selection
> toolset; success = target id in the final answer (containment DV, cross-framework-clean). Held-out
> seeds 101+. Substrate: Claude Haiku (framework tool-calling is best-supported on Claude; not a
> model claim).

## Frameworks
- **raw loop** — a ~30-line tool loop (call → execute tool → feed result → repeat).
- **LangGraph** — `create_react_agent(ChatAnthropic, tools)`.
- **CrewAI** — **DEFERRED**: won't install on this platform (x86_64 macOS, Py 3.12) — its dependency
  chain pulls `lancedb==0.30.0`, which ships no x86_64-macOS wheel. This is itself a
  framework-heaviness data point: CrewAI transitively requires a vector DB just to import.

## Result
**Success (density 3, with the §1.10 attractor present):** both **1.00** — both reliably complete,
recovering from a wrong first tool (`lookup_user`) when it fires.

**Cost / latency at density 3 is NOISY and does NOT isolate the framework.** The aggregate *flipped*
between a 3-seed run (raw cheaper) and a 5-seed run (LangGraph cheaper) because it is dominated by
§1.10 **tool-path stochasticity**: a run that hits the attractor first takes 2 tool calls (~2650 tok)
vs 1 (~1650 tok) — a ~1000-token swing that dwarfs any framework difference.

**Controlled overhead (density 1 — no attractor, so every run is exactly one tool call):**

| framework | success | tok (mean) | latency (mean) |
|---|---|---|---|
| raw       | 1.00 | 1437 | 2.1s |
| LangGraph | 1.00 | 1437 | 2.2s |

Per-seed near-identical (1436/1438, 1430/1434, 1434/1434, …). **LangGraph's react-agent adds no
measurable token or latency overhead** over the raw loop here — the density-3 variance was entirely
the task path, not the framework.

## Adoption threshold (the honest call)
On a simple tool task the framework **buys nothing measurable** — same success, same cost, same
latency as a ~30-line raw loop, plus a dependency and an abstraction layer. **The raw loop is the
right default.** LangGraph earns its keep only for what this task does *not* exercise — durable
checkpointing, human-in-the-loop interrupts, and the decision-support query surface (Module 6.5 /
Phase 2.2). This matches the curriculum's caution against premature framework abstraction; CrewAI's
install failure is a sharper form of the same lesson (the heavier the framework, the more it costs
before it helps).

**Scope:** single-step-ish task, one model (Haiku), N=5, 2 of 3 frameworks. A multi-turn task (where
orchestration/state actually matters) is where a framework could plausibly pull ahead — untested here
and the natural place to revisit in 2.2.

## Reproduce
    uv run python experiments/phase-2.1/bakeoff.py --seeds 5 --go               # density 3 (attractor)
    uv run python experiments/phase-2.1/bakeoff.py --seeds 5 --density 1 --go   # isolate overhead
