# Working Plan — Agentic Engineering Curriculum

Companion to `Agentic_Engineering_Curriculum.md`. This is the *how we actually work through it* plan, tailored to:

- **Pace:** ~10 hrs/wk (steady) → ~16 weeks.
- **Background:** matches the curriculum's assumed learner profile (deep LLM knowledge + published multi-agent orchestration work). So we **skim Module 0, Module 4, and the vocabulary-level parts of 6B**, and reinvest that time in the high-leverage new material: **Module 1 (context engineering), Module 5 (protocols), Modules 7–8 (memory), and the Module 6B harness internals.**
- **Goal:** blend "build the capstone" with "apply to real work" — see below.

---

## Substrate (locked 2026-05-29): an evidence-based position-forming assistant for agentic engineering

We do **not** do disconnected exercises. We build one codebase that gains a capability per module. The substrate is an assistant that helps you **form, defend, and update positions on the field's contested debates** (single vs. multi-agent, RAG vs. grep, memory framework vs. filesystem, MCP/A2A adoption choices, etc.) — drawing on both **source evidence** (papers/blogs/specs) and **experimental evidence** (your own measurements). Its output IS the curriculum's capstone deliverable: a written synthesis report that takes positions on every contested axis with measured evidence.

The unifying data model: `Claim` + `Evidence` (source-type or experiment-type) + `Position` (your stance + supporting evidence + last reviewed).

**Working name:** TBD — pick one this week so package names and exports are coherent from Week 1. Candidates: *Praxis*, *Receipts*, *Anvil*, *Stance*, or yours.

### The throughline bet (decided 2026-05-29)

We design for **years, not 16 weeks**. The curriculum is the *seed dataset* (its papers, blogs, specs, and exercises). The *substrate* is "agentic engineering as a discipline you intend to stay on top of for years." Four design commitments are first-class from Week 1 and built into specific modules:

1. **Stay-current ingest loop** — arXiv + RSS + GitHub-release watching, with a digest filtered to *position-relevant* changes. The position-relevance filter is the value-add over a feed reader and where most of the design work goes. **Built Week 9 (Module 5, MCP).**
2. **Decision-support query surface** — queryable in the moment of building: *"what did past-me decide about X, and what was the evidence?"* This is the load-bearing affordance for **dev-as-skill** — without it the tool is research-only. **Built Week 8 (Module 6.5, LangGraph)** as a checkpointed query session.
3. **Position re-evaluation cadence** — each position has a review timer; old positions get re-surfaced as new evidence arrives or N months pass. **Built Week 7 (Module 6, eval)** as a scheduled agent + staleness metric.
4. **Contribution surface** — exports cleanly into things you ship (blog post per debate, paper sections, OSS reference impls). **Built Weeks 11–12 (Module 6B, coding agents)** as a one-command pipeline.

**Phase split (unchanged):**
- **Weeks 1–5:** toy/synthetic substrate for the mechanics exercises (context-rot curve, KV-cache break/restore, tool-selection accuracy). These need controlled tasks to isolate one variable.
- **Weeks 6+:** real substrate — your actual reading and your actual experiments accrete into the evidence graph. Multi-session usage becomes real, not contrived.
- **Capstone (Weeks 16–18):** the synthesis report is produced *by* the tool, not separately.

### Falsification test — 6 months post-curriculum

Throughline holds if at 6 months **all** of these are true:
- ≥N real-project dev decisions were made better by querying the position store.
- ≥M major field developments were caught via the ingest loop without manually trawling.
- ≥K positions shifted because new evidence came in.
- ≥1 shipped artifact (post / paper / OSS) was meaningfully easier because of the tool.
- ≥1 *new problem* (outside the curriculum's seed dataset) was plugged in and evaluated against the position store — preconditions matched, evaluator run — without writing bespoke problem-specific glue. (The plug-and-play target; see `docs/conceptual.md` § design invariants and `tasks/lessons.md` §0.7.)

If those are zero at 6 months, kill it — it was a sandbox after all. The tool's value is **decisions changed** and **evidence preserved that you'd otherwise have forgotten**. Anything else is theater.

---

## Cross-cutting principles (apply every week, from day one)

These are the curriculum's load-bearing meta-rules. We hold them throughout:

1. **Raw API first.** No framework until a raw loop plateaus on your eval at acceptable cost. (Threshold: if the raw-loop agent already passes your task eval cheaply, *don't* adopt LangGraph yet.)
2. **Wire observability + an eval harness on day one** — not month six. We build the skeleton in Week 1 and grow it.
3. **Instrument context budget *and* KV-cache hit rate from the start.** They're first-order cost levers, not micro-optimizations.
4. **Re-derive every leaderboard/benchmark claim on your own data.** Treat all numbers in the curriculum as snapshots.
5. **Context engineering is the spine.** Treat the multi-agent and memory debates as *special cases of context management*, not separate topics.

## How we work together (learning-first)

**Your own learning is the primary goal — equal to or more important than the artifact.** The plan optimizes for *you developing the chops*, not for me producing code fast. Concretely:

- **You write/decide the load-bearing parts** — the raw loop, context instrumentation logic, tool-design refactors, reasoning loops, memory tiers, and every design tradeoff. That's where the learning lives.
- **I build only the pure plumbing/boilerplate** around them (repo setup, log formatting, harness wiring, server skeletons) so your 10 hrs/wk go to concepts, not scaffolding.
- **When you're stuck, I hint and surface the tradeoff space before giving answers.** No turnkey solutions on the conceptual material. (No hand-holding on basics either — you know the territory.)
- **I make my reasoning visible** — the *why* behind a choice, so you take away the judgment, not just the result.
- **We treat the contested debates as yours to settle** — I lay out the evidence on each side; you form the position. We check understanding rather than racing to deliverables.

---

## Week-by-week

### Week 1 — Setup + foundations skim + instrumentation skeleton
*(Module 0 skim + cross-cutting infra)*
- Read (fast, for vocabulary): Anthropic *Building Effective Agents* (augmented LLM, the 5 workflow patterns).
- Build: the bare **~50-line raw agent loop** against a raw LLM API (no framework).
- Build (cross-cutting): skeleton of the **token-budget logger** (tokens by category: system / tools / history / retrieved, per turn) and an empty **eval-harness** module.
- Set up: git repo, Python env, LLM API access.
- **Deliverable:** raw loop + per-turn token-by-category logging + git history. *(I scaffold the logger + repo; you write the loop.)*

### Weeks 2–3 — Context Engineering (the highest-priority module)
*(Module 1 — the spine)*
- Read back-to-back: Anthropic *Effective Context Engineering for AI Agents* (Sept 2025) + Manus *Context Engineering: Lessons from Building Manus* (July 2025) + Chroma *Context Rot*.
- Exercises:
  1. **Context-rot curve** — fix a task, pad with distractors, plot accuracy vs. input length. *(toy substrate)*
  2. **Compaction** + a **fresh-window** alternative (write state to filesystem, restart clean).
  3. **KV-cache instrumentation** — measure hit rate over a multi-turn run; deliberately break it (per-turn timestamp in system prompt, non-deterministic tool-schema serialization); quantify the latency/cost delta; restore the append-only/stable-prefix invariant and confirm recovery.
- Defer: SELF-ROUTE (RAG-vs-LC router) — fold into Module 8.
- **Deliverable:** instrumented raw-loop agent with KV-cache discipline + a plotted context-rot curve. **This is the load-bearing module — budget the full two weeks.**

### Weeks 4–5 — Tool Use & Function Calling
*(Module 2)*
- Read: Anthropic *Writing Effective Tools for AI Agents*; Manus (logit-masking over tool mutation — already read).
- Build a **10–15 tool suite with deliberate overlap**; measure selection accuracy; refactor with **namespacing + curated returns**; re-measure.
- Implement the durable tool primitives we reuse all curriculum: **return-a-reference** (large output → handle + summary), **explicit terminal states** (SUCCESS/FAILURE + reason), **harness loop-guard** (sliding-window duplicate-call blocker).
- Build a small **held-out tool eval set**.
- **Deliverable:** a real, cache-safe, reference-returning tool layer on the agent + tool-selection metrics. *(I scaffold the suite + eval set; you do the design refactor and read the results.)*

### Week 6 — Reasoning & Planning Patterns
*(Module 3 — move fast, you know the territory; substrate transitions toy → real here)*
- Implement **ReAct**, **plan-and-execute**, and a **reflection loop** against the *same* task suite; compare success / token cost / latency.
- Small **Tree-of-Thoughts** search on a constraint task (Game of 24) — compute/accuracy frontier.
- **Real substrate kicks in:** the task suite now includes *"form a position on debate X given this evidence set"* tasks drawn from your actual reading. The reasoning-loop comparison gets evaluated on a real evidence-graph operation, not a synthetic one.
- **Schema decision (load-bearing, you design):** by end of week, v0 of the `Claim` / `Evidence` / `Position` schema exists (SQLite or JSON — keep it simple). Subsequent modules read/write through this.
- **Deliverable:** reasoning-loop comparison report + the winning loop wired into the spine + v0 evidence-graph schema with a handful of real claims/positions seeded from your Module-1 reading.

### Week 7 — Evaluation, Observability, Reliability
*(Module 6 — "do not skip")*
- Formalize the eval harness started Week 1: **LLM-as-judge rubric**, **trajectory logging**, **OpenTelemetry tracing** (Langfuse).
- Implement the **deterministic vs. probabilistic verifier** split (linters/type-checkers/tests as cheap binary sensors; LLM-judge reserved for subjective criteria); format deterministic failures as corrective signals injected back into context.
- Read the benchmark-skepticism material (arXiv:2507.02825; τ-bench) — internalize *why* leaderboard numbers mislead.
- **Throughline Property 3 — Position re-evaluation cadence:** add a per-position **staleness metric** (time since last review × evidence-flux since) and a **scheduled agent** that surfaces stale positions for review. The staleness signal becomes its own eval target — *"did the tool surface the position that needed revisiting before I made a decision against it?"* You design the staleness function (load-bearing); I scaffold the scheduler.
- **Deliverable:** real eval harness (judge + OTel + deterministic-verifier layer) + position-staleness scheduler.

### Week 8 — Orchestration-Layer Tooling (LangGraph deep dive)
*(Module 6.5)*
- Rebuild the spine agent in **LangGraph**: conditional-edge **generator→critic** loop + a **durable checkpointer** + one **human-in-the-loop interrupt**. Also build it in **CrewAI** and compare to the raw loop (LOC, debuggability, where the abstraction helps vs. hurts).
- Apply the threshold honestly: **adopt LangGraph only if you actually need durable state / checkpoints / HITL / cyclic control flow.** If the raw loop still wins on your eval, note that and keep it.
- **Throughline Property 2 — Decision-support query surface:** the LangGraph checkpointed session IS the in-the-moment query surface. HITL interrupts let you steer mid-session. **You start *using* the tool for real decisions this week** — at minimum one non-curriculum question put through it (e.g., a real design call you're facing in your other work). If the tool can't be used yet for a real decision, that's the signal something is missing.
- **Deliverable:** agent runnable in raw loop + LangGraph; framework-comparison notes; explicit keep/adopt decision; ≥1 real decision-support session captured and reviewed.

### Week 9 — Agentic Protocols (learner-flagged priority + new material)
*(Module 5)*
- Build and register an **MCP server** (stdio) exposing the substrate's ingest + query tools: at minimum an **arXiv ingester**, an **RSS/blog ingester** (Anthropic / OpenAI / Manus / Chroma / Cognition / LangChain feeds), a **GitHub-release watcher** (MCP/A2A/LangGraph/Letta/Mem0/Zep), and an evidence-graph **query tool**. Connect it to **Claude Code** and to a custom client.
- Stand up **two A2A agents** with Agent Cards (`/.well-known/agent-card.json`): a **paper-summarizer specialist** and an **experiment-runner specialist**; have the core agent delegate to each.
- Read: modelcontextprotocol.io spec + the A2A site. Note the security surface (MCP servers run sandboxed, scoped perms).
- **Throughline Property 1 — Stay-current ingest loop:** wire the ingesters above to a daily/weekly cron + a **position-relevance filter** that surfaces only items touching a position you hold or a debate you're tracking. The filter design is the load-bearing part — *your* curation logic, not generic feed filtering. This is where the tool stops being a curriculum companion and starts being a years-long instrument.
- **Deliverable:** working ingest pipeline producing a daily position-relevant digest + two A2A specialists. The digest's first delivery is *itself* an eval — does it surface things that actually shifted your thinking?

### Week 10 — Multi-Agent Systems (skim debate, do the one experiment)
*(Module 4 — you have prior work here; calibrate light)*
- Skim the three-way debate (Anthropic +90.2% / Cognition "Don't Build Multi-Agents" / LangChain synthesis) and the MAST failure taxonomy — for *vocabulary alignment*, fast.
- The experiment that matters: take one task framed both ways; build a **single-agent** and an **orchestrator-worker** version; measure success / token-multiplier / latency / coherence; **locate the isolation boundary empirically.**
- Hold the 2026 reframing: "your apparent multi-agent problem is often a context-window problem in disguise."
- **Deliverable:** the ablation + a measured isolation-boundary finding for your task type.

### Weeks 11–12 — Coding Agents in Practice
*(Module 6B — skim vocabulary, invest in the high-leverage parts)*
- **Week 11 (foundations + authoring):** Skim the parts you know (you live in Claude Code). Invest in what *dominates output quality*: author a strong **CLAUDE.md and AGENTS.md** for the assistant's own repo; run the **Explore→Plan→Implement→Commit** cycle; a **TDD workflow** end-to-end (failing tests → implement → green, *don't modify the tests*); the **deterministic feedback loop**.
- **Week 12 (harness + headless):** Build a **headless CI flow** (`claude -p` / `codex exec` running lint/test and proposing a PR). Run the harness-comparison experiment (same model, different harness — observe the scaffolding swing). Set up a **read-only review subagent** + a **parallel-exploration subagent**; note where each helps vs. is "agent theater."
- **The coding arm's target IS the assistant itself** — Claude Code/Codex headlessly evolves the assistant's codebase (schema migrations, new MCP ingesters, new agent variants for experiments). Recursive in the right way.
- **Throughline Property 4 — Contribution surface:** add an **export pipeline**: position → blog-post draft, debate → paper section, agent variant → OSS-ready package (with README, license, eval harness wired in). The pipeline itself is a coding-arm exercise. Goal: at the end of any debate, shipping a public artifact is one command, not a manual repackage.
- **Deliverable:** strong CLAUDE.md/AGENTS.md for the assistant repo + headless coding flow + export pipeline that has produced at least one shipped draft.

### Week 13 — Memory Foundations
*(Module 7)*
- Read: CoALA (arXiv:2309.02427) as the scaffold; MemGPT (arXiv:2310.08560).
- Build: a **MemGPT-style three-tier agent** (core / recall / archival) with self-editing memory tools in **Letta**.
- Build: a **Generative-Agents memory stream** (recency × importance × relevance retrieval) + a **nightly reflection** step that consolidates episodic logs into semantic rules.
- **Deliverable:** tiered memory + a consolidation pipeline on the agent.

### Weeks 14–15 — Memory Frameworks & the Contested Frontier
*(Module 8 — teach the contest explicitly)*
- The bake-off: stand up **Mem0**, **Zep**, a plain **filesystem-memory baseline**, and a **full-context baseline** against the *same multi-session task* (use your real usage). Measure accuracy / p95 latency / token cost. **Reproduce the "full-context beats the framework" comparison** for yourself.
- Implement both **hot-path** (in-loop ADD/UPDATE/DELETE) and **cold-path** (background consolidation + pre-inference profile injection) writes.
- Adversarial: inject a stale/contradictory fact and a poisoned "successful experience"; observe drift.
- Apply the **decision rule:** adopt Mem0/Zep/Letta *only if* it beats the filesystem + full-context baselines on *your* data at acceptable cost.
- Fold in the deferred **SELF-ROUTE** RAG-vs-long-context router here.
- **Deliverable:** a measured memory-architecture decision for your project, with the baselines beaten (or not).

### Weeks 16–18 — Capstone integration + synthesis
*(everything is already a component)*
- Wire the pieces: LangGraph core loop + checkpointer + context/KV instrumentation + MCP tools + A2A specialist + multi-agent ablation mode + coding arm + tiered memory + the eval harness.
- Run the full eval; produce the **written synthesis report that takes a measured position on every contested axis** (single vs. multi-agent, RAG vs. grep/long-context, dedicated memory vs. filesystem vs. full-context, protocol stack) — backed by *your* numbers, not the curriculum's.
- **Deliverable:** the integrated real-work assistant + the synthesis report. This is both the capstone *and* the v1 of your applied tool.

---

## Schedule at a glance

| Weeks | Focus | Modules | Depth |
|-------|-------|---------|-------|
| 1 | Setup + foundations + instrumentation | 0 (skim) | light |
| 2–3 | **Context engineering (the spine)** | 1 | **deep** |
| 4–5 | Tool use | 2 | deep |
| 6 | Reasoning/planning | 3 | medium |
| 7 | Eval / observability | 6 | deep |
| 8 | Orchestration tooling (LangGraph) | 6.5 | medium |
| 9 | **Protocols (MCP/A2A)** | 5 | **deep** |
| 10 | Multi-agent | 4 | skim + 1 experiment |
| 11–12 | Coding agents | 6B | skim vocab, deep on authoring |
| 13 | Memory foundations | 7 | deep |
| 14–15 | **Memory frontier + bake-off** | 8 | **deep** |
| 16–18 | Capstone + synthesis | all | integrative |

Re-check docs/benchmarks quarterly — the field moves monthly.

---

## Stage / Phase mapping

The week-by-week above maps to the Stage/Phase model in `CLAUDE.md` (adopted 2026-05-29 from the `crit-thinking → synthoracle → epibench` template lineage + ccupa governance). Each phase = **PLAN → TEST → IMPLEMENT → VERIFY → RETRO → `/learn`**.

| Phase | Weeks | Module | Title |
|-------|-------|--------|-------|
| 0.0 | 1 | Module 0 (skim) | Foundations + instrumentation skeleton |
| 1.0 | 2–3 | Module 1 | Context engineering (the spine) |
| 1.1 | 4–5 | Module 2 | Tool design |
| 2.0 | 6 | Module 3 | Reasoning patterns + evidence-graph schema v0 |
| 2.1 | 7 | Module 6 | Eval + position-staleness scheduler **(Property 3)** |
| 2.2 | 8 | Module 6.5 | LangGraph + decision-support query surface **(Property 2)** |
| 2.3 | 9 | Module 5 | Protocols + stay-current ingest loop **(Property 1)** |
| 2.4 | 10 | Module 4 | Multi-agent ablation |
| 3.0 | 11 | Module 6B.A | Coding-agents foundations + authoring |
| 3.1 | 12 | Module 6B.B | Headless + harness comparison + contribution surface **(Property 4)** |
| 3.2 | 13 | Module 7 | Memory foundations |
| 3.3 | 14–15 | Module 8 | Memory bake-off + contested frontier |
| 4.0 | 16–18 | Capstone | Integration + synthesis report |

**Critical phase boundaries** (require ccupa-style three-reviewer parallel pass with confidence-scoring ≥80):
- **1.0 → 1.1** — context-engineering spine commitment
- **2.2 → 2.3** — LangGraph adopt/keep decision
- **2.4 → 3.0** — multi-agent isolation-boundary commitment
- **3.3 → 4.0** — memory architecture commitment
- **4.0 closeout** — synthesis-report position claims

See `CLAUDE.md` § Validation Gates for the full per-phase requirement and § Throughline Property Gate for the cross-cutting check.

---

## What I need from you to specialize this

1. ~~Real-project target~~ — **locked 2026-05-29**: evidence-based position-forming assistant for agentic engineering, designed for years (throughline bet).
2. ~~Language/stack~~ — **Python** (confirmed 2026-05-29).
3. ~~`git init`~~ — **done** (repo on `main`, Python `.gitignore` in place; nothing committed yet).
4. **Working name** — *still open*. Candidates: Praxis, Receipts, Anvil, Stance, or yours. Lock it this week so the repo's package name and exports are coherent from Week 1.
