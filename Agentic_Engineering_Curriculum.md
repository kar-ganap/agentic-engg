# The Agentic Engineering Curriculum: A Self-Directed Syllabus and Annotated Landscape

## TL;DR

- **This is a 9-module, ~14–18 week curriculum** that builds from the conceptual anatomy of an agent (the harness, the loop, context as a first-class resource) through coding agents (Claude Code, Codex) and a deep memory drilldown, with the central thesis that **"context engineering" — not model choice — is the dominant determinant of agent reliability**, and that most apparent multi-agent and memory needs are context-management problems in disguise.
- **The field's hardest-won, most defensible lessons are reductive**: start with the simplest thing (a single augmented LLM in a loop), add complexity only when measurement demands it, treat the context window as a scarce budget subject to "context rot," and be deeply skeptical of dedicated memory frameworks and multi-agent architectures until a strong single-agent baseline plateaus.
- **The genuinely contested frontiers** you should hold loosely: single-agent vs. multi-agent (Anthropic's +90.2% research result vs. Cognition's "Don't Build Multi-Agents"), RAG/embeddings vs. grep/long-context, dedicated memory systems vs. filesystem-as-memory (where a no-memory full-context baseline sometimes beats the frameworks), and a proliferating, only-partly-converging agent-protocol stack (MCP + A2A winning; payments a "wild west").

## Key Findings

1. **Context engineering subsumes prompt engineering and is the central skill.** Anthropic's September 29, 2025 engineering post, *Effective Context Engineering for AI Agents*, reframes the discipline around the question "what configuration of context is most likely to generate our model's desired behavior?" Its operational definition: "good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome." Context "must be treated as a finite resource with diminishing marginal returns," drawing on an "attention budget." This is the spine of the whole curriculum.

2. **Context rot is real and mechanistically important.** Chroma's 2025 research (*Context Rot: How Increasing Input Tokens Impacts LLM Performance*, by Kelly Hong, Anton Troynikov, and Jeff Huber) states verbatim: "we evaluate 18 LLMs, including the state-of-the-art GPT-4.1, Claude 4, Gemini 2.5, and Qwen3 models. Our results reveal that models do not use their context uniformly; instead, their performance grows increasingly unreliable as input length grows." Capacity is the wrong metric; signal-to-noise ratio is what matters. This is the empirical justification for aggressive context management and a counterweight to "just use long context."

3. **The single-agent vs. multi-agent debate has matured into a decision rule.** Anthropic reported that "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval," but at high cost — "agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats." Cognition argued the opposite for coding. The 2026 synthesis: single-agent baseline first; multi-agent only for parallelizable, read-heavy, weakly-coupled tasks; never for sequential or shared-state work like most coding.

4. **Memory ≠ context management, but they overlap heavily.** Short-term/working memory *is* the context window; long-term memory (episodic/semantic/procedural) is external store that must be *retrieved into* context to matter. The MemGPT/Letta "virtual context management" paradigm is the canonical mechanism. But dedicated memory frameworks (Mem0, Zep, Letta, LangMem) are under genuine attack from simpler filesystem-as-memory approaches, and their benchmarks are contested.

5. **Coding-agent best practices are stabilizing but several primitives are still in flux.** CLAUDE.md/AGENTS.md as durable project "constitution," planning-first and test-driven workflows, and subagents-for-context-isolation are established. Skills-vs-slash-commands-vs-CLAUDE.md, spec-driven development, and grep-vs-embeddings are not settled.

6. **The protocol layer is converging on governance while proliferating at the edges.** MCP (tools) and A2A (agent-to-agent) are the two winners, both under the Linux Foundation; IBM's ACP merged into A2A; payments protocols remain a "wild west."

7. **Production agent economics are dominated by KV-cache hit rate.** Manus's engineering team (Yichao "Peak" Ji, *Context Engineering for AI Agents: Lessons from Building Manus*, July 2025) argues the KV-cache hit rate is "the single most important metric for a production-stage AI agent," because agents accumulate context every turn while emitting short outputs (Manus reports a ~100:1 input-to-output token ratio) and cached input tokens cost roughly 10× less than uncached (≈$0.30 vs ≈$3.00/MTok on Claude Sonnet at the time of writing). This elevates prefix stability, append-only context, and deterministic serialization from micro-optimizations to first-order design constraints. [ESTABLISHED practitioner consensus; the specific ratios are one team's reported figures.]

## Details

---

### How to use this curriculum

Each module lists **learning objectives**, **key resources** (with enough detail to find them), and **hands-on exercises/projects**. Effort estimates are relative. The recommended path is sequential through Phase 1, but Phases 2 (coding agents) and 3 (memory) can be reordered to taste. Given the learner's profile (deep LLM knowledge, published multi-agent orchestration work), **Modules 0, 4, and 6 can be skimmed for vocabulary alignment**; the highest-leverage new material is in Modules 1 (context engineering), 5 (protocols), 7–8 (memory), and the coding-agent harness internals in Module 6B.

A note on epistemics: this field is ~2 years old as a named discipline. Throughout, **[ESTABLISHED]** marks consensus, **[EMERGING]** marks promising-but-unproven, and **[CONTESTED]** marks genuine live debate.

---

## PHASE 1 — GENERIC, APPLICATION-AGNOSTIC AGENT FOUNDATIONS

### Module 0 — The Anatomy of an Agent (skim for the sophisticated learner) — ~3–5 hrs

**Objectives:** Establish precise vocabulary. Distinguish *workflow* (LLM + tools orchestrated through predefined code paths) from *agent* (LLM dynamically directing its own process and tool use). Decompose an agent into: the LLM as reasoning engine, the **agent loop** (perception → reasoning → action → observation), the **harness/scaffold** (the deterministic code that runs the loop, manages context, parses tool calls, enforces guardrails), **tools**, and **context** as a first-class concern.

**Key resources:**
- Anthropic, *Building Effective Agents* (Erik Schluntz & Barry Zhang, Dec 2024) — the foundational practitioner text. Read the "augmented LLM" building block and the workflow patterns (prompt chaining, routing, parallelization, orchestrator-worker, evaluator-optimizer).
- The companion `anthropics/claude-cookbooks` `patterns/agents` reference implementations on GitHub.
- The augmented-LLM mental model: an LLM enhanced with retrieval, tools, and memory that generates its own search queries and decides what to retain.

**Exercise:** Implement a bare agent loop in ~50 lines of Python against a raw LLM API (no framework): a while-loop that calls the model, parses a tool call, executes it, appends the observation, and repeats until a stop token. This is the "build it from scratch first" discipline Anthropic recommends.

---

### Module 1 — Context Engineering & Context Management *(highest priority)* — ~14–18 hrs

**Objectives:** Master the discipline that turns an LLM into a reliable agent. Understand what goes in the window and in what order (system instructions → memory/retrieved context → tool definitions → message history); context-window *budgeting*; the prompt-engineering vs. context-engineering distinction; retrieval-augmented context; compaction/summarization; context degradation over long horizons; and the production-serving mechanics (KV-cache) that make context discipline economically load-bearing.

**Core concepts to internalize:**
- **Context engineering = curating and maintaining the optimal set of tokens during inference**, including everything that lands in context outside the prompt itself. The operational target (Anthropic, Sept 29, 2025) is "finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome," treating context as "a finite resource with diminishing marginal returns" against an "attention budget." It is the natural successor to prompt engineering.
- **Context as a finite resource.** Strategies: be selective about message history; **just-in-time retrieval** (fetch via lightweight identifiers at runtime, mirroring how humans use notes/bookmarks); **compaction** (summarize as the window fills); hybrid up-front + runtime approaches.
- **Context rot** [ESTABLISHED]: Chroma's 2025 study (Kelly Hong, Anton Troynikov, Jeff Huber) evaluated 18 LLMs (GPT-4.1, Claude 4, Gemini 2.5, Qwen3) and found "models do not use their context uniformly; instead, their performance grows increasingly unreliable as input length grows" — driven by needle-question similarity, distractors, and haystack structure. Distinct from context-window *overflow*. The "lost in the middle" phenomenon is the well-known antecedent.
- **KV-cache hit rate as the dominant cost/latency lever** [ESTABLISHED]: In production the context grows every turn while outputs stay short (Manus reports a ~100:1 input-to-output ratio), so prefilling dominates decoding and prefix caching becomes essential to economic viability — cached vs. uncached input tokens differ ~10× in price. The discipline (Manus, *Context Engineering for AI Agents: Lessons from Building Manus*, Yichao "Peak" Ji, July 2025): (1) **keep the prompt prefix stable** — a single-token change, e.g. a timestamp precise to the second in the system prompt, invalidates the cache from that token onward; (2) **make context append-only** and use deterministic serialization — never edit prior actions/observations, and beware that a reordered JSON dictionary silently breaks the cache; (3) **place explicit cache breakpoints** where manual cache management is required; (4) in distributed serving, use sticky/session-consistent routing so requests reuse the same cache. This is the mechanistic reason "context discipline" is not aesthetic preference but cost survival.
- **Manipulating attention via recitation** [EMERGING]: to counter goal drift and the lost-in-the-middle effect on long-horizon tasks, have the agent maintain and repeatedly rewrite a running `todo.md` (or equivalent), pushing the live objective into the most recent (highest-attention) tokens. Manus uses this deliberately; treat it as a context-engineering technique, not a UI nicety.
- **Keep the wrong stuff in** [EMERGING/CONTESTED]: leaving failed actions, error messages, and stack traces in context — rather than silently retrying on a cleaned history — gives the model evidence to adapt and reduces repeated mistakes. A counterintuitive Manus practice that trades a slice of context budget for error-recovery signal; weigh it against context-rot pressure on very long runs.
- **The "files are all you need" thread** [EMERGING/CONTESTED]: the filesystem as a context interface, with databases as persistence underneath.

**Key resources:**
- Anthropic Engineering, *Effective Context Engineering for AI Agents* (Sept 29, 2025) — the canonical text. Authoritative on system-prompt structure, just-in-time retrieval, and compaction.
- Manus, *Context Engineering for AI Agents: Lessons from Building Manus* (Yichao "Peak" Ji, July 2025, manus.im/blog) — a first-party engineering retrospective and the canonical practitioner source for KV-cache discipline, logit-masking over tool mutation (see Module 2), filesystem-as-context, recitation, and "keep the wrong stuff in." Pairs directly with the Anthropic post; read both back-to-back.
- Chroma Research, *Context Rot* (trychroma.com/research/context-rot) + Kelly Hong's talk on Hamel Husain's blog (hamel.dev) and the Maven session. Read the shuffled-context and distractor experiments.
- Anthropic Engineering, *Writing Effective Tools for AI Agents* (the tool-context budgeting argument: agents have limited context whereas computer memory is cheap — design tools that return *curated* not *exhaustive* results; namespacing like `asana_search` vs `jira_search`).
- The RAG-vs-long-context evidence base: *Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach* (Li et al., arXiv:2407.16833) — proposes SELF-ROUTE; finds LC and RAG agree on >60% of queries, RAG far cheaper. Plus the 2025 "sufficient context" framing (ICLR 2025).
- **[EMERGING] Agentic Context Engineering (ACE)**: *Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models* (Zhang et al., Stanford/SambaNova/UC Berkeley, arXiv:2510.04618, Oct 2025). Treats context as an evolving "playbook" maintained by Generator/Reflector/Curator roles via incremental delta updates; explicitly targets "brevity bias" and "context collapse." Reports +10.6% on agents and +8.6% on finance with large reductions in adaptation latency and rollout cost; on the AppWorld leaderboard, ReAct+ACE (59.4%) roughly matched IBM's GPT-4.1-based CUGA (60.3%) using the smaller open-source DeepSeek-V3.1. Positions context engineering as an alternative to fine-tuning.

**Exercises:**
1. **Context budget instrumentation:** Build a harness that tracks token allocation by category (system, tools, history, retrieved) per turn and logs it. Reproduce a mini context-rot curve: hold a task fixed, pad context with distractors, and plot accuracy vs. input length.
2. **Compaction:** Implement summarization-based compaction with a "fresh window" alternative (write state to the filesystem, start clean — Anthropic's recommended pattern for multi-window tasks).
3. **SELF-ROUTE replication:** Build a router that decides per-query between RAG and full-context.
4. **KV-cache instrumentation:** Measure cache-hit rate across a multi-turn run; then deliberately break it (inject a per-turn timestamp into the system prompt, or non-deterministically serialize tool schemas) and quantify the latency/cost delta. Confirm that restoring the append-only, stable-prefix invariant recovers the hit rate.

---

### Module 2 — Tool Use & Function Calling — ~8–10 hrs

**Objectives:** Mechanics of function calling (schema specification, the model emitting structured calls, the harness executing and returning observations); tool *design* best practices; error handling; tool selection under many tools; and the cache- and loop-safety properties of a good tool interface.

**Core concepts:**
- Tools are "a new kind of software — a contract between deterministic systems and non-deterministic agents" (Anthropic). Re-orient from deterministic to evaluation-driven design.
- **Tool affordances:** don't merely wrap API endpoints; design for the agent's limited context (return curated results, not all rows). Too many overlapping tools degrade selection — use **namespacing**.
- **Evaluation-driven tool development:** generate realistic eval tasks, measure tool-use success, let an agent help optimize tool descriptions. In Anthropic's *Writing Effective Tools for AI Agents*, a tool-testing agent that repeatedly used flawed tools then rewrote their descriptions produced "a 40% decrease in task completion time for future agents using improved descriptions"; the same post notes "Claude Sonnet 3.5 achieved state-of-the-art performance on the SWE-bench Verified evaluation after we made precise refinements to tool descriptions."
- **Stable tool sets and logit-masking over mutation** [EMERGING]: dynamically adding/removing tools mid-task invalidates the KV-cache (the tool block sits near the front of the prefix) and can orphan references to now-missing tools in the history. Manus's approach is to keep tool *definitions* stable and instead **mask token logits** at decode time to constrain which tools are selectable in a given state — preserving the cache and preventing schema violations. Prefer state-conditioned masking to swapping the toolset.
- **Return references, not payloads** [ESTABLISHED]: tools that can emit large outputs (log dumps, file contents, query results) should write the payload to external state (filesystem/store) and return a lightweight handle/identifier plus a short summary, so the agent pulls detail just-in-time. This is the operational form of just-in-time retrieval and the primary defense against a single tool call blowing the context budget.
- **Explicit terminal states** [ESTABLISHED]: design tool responses to resolve to unambiguous SUCCESS/FAILURE with a reason, rather than soft signals like "more results may be available," which induce repeated identical calls. Pair with a harness-level loop guard (a sliding-window check that blocks duplicate call signatures and returns a corrective message) for defense in depth.
- **Long-running tools — return-and-poll** [ESTABLISHED]: for slow external calls, return a tracking ID immediately and have the agent poll a lightweight status tool, rather than blocking the loop on a synchronous call that risks gateway timeouts.
- The historical arc: **Toolformer** (model learns *when* to call tools via self-supervision, baked into weights) vs. **ReAct** (prompting-time tool use).

**Key resources:**
- Anthropic Engineering, *Writing Effective Tools for AI Agents* (the tool-evaluation cookbook process).
- Manus, *Context Engineering for AI Agents: Lessons from Building Manus* (July 2025) — for logit-masking over tool mutation and the cache implications of tool-set changes (also in Module 1).
- **Toolformer**: Schick et al., Meta AI, *Toolformer: Language Models Can Teach Themselves to Use Tools* (arXiv:2302.04761, NeurIPS 2023). A 6.7B Toolformer outperforms 175B GPT-3 zero-shot on downstream tasks.
- Berkeley Function Calling Leaderboard (BFCL) for current tool-use rankings.
- Tool documentation papers: *Tool Documentation Enables Zero-Shot Tool-Usage* (2023); *EASYTOOL*; ToolLLM (16,000+ APIs).

**Exercise:** Build a 10–15 tool suite with deliberate overlap; measure selection accuracy; then refactor with namespacing and curated returns and re-measure. Add a "large output" tool and convert it to the return-a-reference pattern; add a deliberately ambiguous tool and observe whether terminal states + a loop guard stop repeated calls. Build a small held-out tool eval set.

---

### Module 3 — Agent Loops, Reasoning & Planning Patterns — ~10–12 hrs

**Objectives:** Master the control-flow patterns and when to use each: ReAct, plan-and-execute, reflection/self-critique, tree-of-thought, and their tradeoffs.

**Core patterns:**
- **ReAct** (interleave reasoning traces with actions/observations) — the foundational loop. Versatile, adaptive, no fine-tuning required, but linear and can be myopic.
- **Plan-and-execute** — plan the whole strategy first, then execute; gives lookahead, reduces myopia, but plan-revision cadence needs tuning.
- **Reflexion** — verbal reinforcement: agent reflects on failures in natural language, stores reflections in episodic memory, retries. "A semantic gradient signal."
- **Tree of Thoughts** — explore multiple reasoning branches with BFS/DFS search and evaluation; powerful when early steps dominate outcomes. Graph-of-Thoughts generalizes further.

**Key resources (seminal papers with IDs):**
- **ReAct**: Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models* (arXiv:2210.03629, ICLR 2023). SOTA on HotpotQA/Fever, ALFWorld/WebShop; reduces hallucination vs. chain-of-thought.
- **Reflexion**: Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning* (arXiv:2303.11366, NeurIPS 2023). 91% pass@1 on HumanEval, surpassing GPT-4's then-80%.
- **Tree of Thoughts**: Yao et al. (arXiv:2305.10601, NeurIPS 2023). On Game of 24, 74% success vs. 4% for CoT-prompted GPT-4.
- Surveys: *LLM-based Agentic Reasoning Frameworks: A Survey from Methods to Scenarios* (arXiv:2508.17692); the `weitianxin/Awesome-Agentic-Reasoning` GitHub list.
- IBM's *What is a ReAct Agent?* explainer for grounding.

**Exercises:**
1. Implement ReAct, plan-and-execute, and a reflection loop against the *same* task suite; compare success rate, token cost, latency.
2. Implement a small ToT search for a constraint problem (e.g., Game of 24) and measure the compute/accuracy frontier.

---

### Module 4 — Multi-Agent Systems & Orchestration *(learner has prior work here — calibrate)* — ~8–10 hrs

**Objectives:** Single-agent vs. multi-agent tradeoffs; orchestrator-worker/hub-and-spoke, agent teams, sequential vs. parallel, supervisor patterns, handoffs; and crucially, **when multi-agent is NOT worth it.**

**The central debate [CONTESTED]:**
- **The case FOR (Anthropic, June 13, 2025, *How We Built Our Multi-Agent Research System*, by Jeremy Hadfield, Barry Zhang, Kenneth Lien, Florian Scholz, Jeremy Fox, Daniel Ford):** an orchestrator-worker architecture (a LeadResearcher plans and saves its plan to memory to survive the 200K-token truncation limit, spawns 3–5 parallel subagents with isolated context windows, then a CitationAgent attributes claims). Multi-agent (Opus 4 lead + Sonnet 4 subagents) "outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval." On the BrowseComp evaluation, "token usage by itself explains 80% of the variance, with the number of tool calls and the model choice as the two other explanatory factors." But these systems "use about 15× more tokens than chats." Scaling heuristics: simple fact-finding = 1 agent / 3–10 calls; comparisons = 2–4 subagents; complex research = 10+ subagents. Explicit caveat: "domains that require all agents to share the same context or involve many dependencies between agents are not a good fit for multi-agent systems today" (e.g., most coding).
- **The case AGAINST (Cognition, June 12, 2025, Walden Yan, *Don't Build Multi-Agents*):** parallel subagents make independent decisions on shared problems → conflicting, incoherent outputs (the "Flappy Bird with a Super Mario background" example). Favors single-threaded linear agents and continuous context flow. Coined "context engineering" in the process.
- **The synthesis (LangChain, *How and When to Build Multi-Agent Systems*):** both agree context-sharing is the crux. The decision variable is the **isolation boundary**: how much each subagent must know about the others. For research, near-zero (works great in parallel); for coding, near-total (multi-agent fails).
- **2026 reframing [EMERGING]:** build a strong single-agent baseline first; "your apparent multi-agent problem is often a context-window or prompt-engineering problem in disguise." See also the MAST taxonomy paper *Why Do Multi-Agent LLM Systems Fail?* (Cemri et al., Berkeley, 2025) for a failure-mode catalog.

**Key resources:** the three posts above; LangChain's synthesis; the MAST failure-modes paper.

**Exercise:** Take a task you can frame both ways. Build (a) a single-agent version and (b) an orchestrator-worker version. Measure success, token cost, latency, and coherence. Identify the isolation boundary empirically.

---

### Module 5 — Agentic Protocols: MCP, A2A, ACP, and the Emerging Stack *(learner-flagged priority)* — ~10–12 hrs

**Objectives:** Understand what each protocol does, its architecture, the differences, current adoption, and which are gaining traction.

**Model Context Protocol (MCP) — agent↔tools [ESTABLISHED winner]:**
- Created at Anthropic by David Soria Parra and Justin Spahr-Summers; open-sourced Nov 25, 2024. The "USB-C port for AI" solving the M×N integration problem.
- **Architecture:** a host application manages multiple clients, each with a 1:1 relationship to a server. Two layers: a **data layer** (JSON-RPC 2.0 protocol: lifecycle, primitives) and a **transport layer**.
- **Three server primitives:** **Tools** (executable functions, `tools/call`), **Resources** (contextual data, `resources/read`), **Prompts** (reusable templates, `prompts/get`), each with `*/list` discovery. **Client primitives:** roots, sampling (`sampling/createMessage`), elicitation.
- **Transports:** stdio (local) and Streamable HTTP with optional Server-Sent Events and OAuth.
- Moved under the Linux Foundation's Agentic AI Foundation (with 18,000+ community-indexed servers reported). *(The exact transfer date is reported variously around late 2025; verify before citing a specific month.)*
- **Security note:** because MCP servers can execute commands and touch the filesystem, they are a prompt-injection, tool-permission-escalation, and lookalike-tool attack surface; run them sandboxed with scoped permissions.

**Agent2Agent (A2A) — agent↔agent [ESTABLISHED winner]:**
- Launched by Google April 9, 2025 at Google Cloud Next with 50+ partners; donated to the Linux Foundation June 23, 2025 (Apache 2.0). 150+ supporting organizations by the one-year mark.
- **Architecture:** HTTP + JSON-RPC 2.0; **Agent Cards** (JSON manifests at `/.well-known/agent-card.json`) advertise identity, capabilities, endpoints, auth. Supports request-response, SSE streaming, and webhook callbacks for long-running tasks. A **task lifecycle** (submitted → working → input-required → completed/failed) and **artifacts** (structured deliverables) are first-class. Horizontal peer-to-peer delegation without exposing internal implementation — the complement to MCP's vertical tool access.
- **AP2 (Agent Payments Protocol):** a formal A2A extension for agentic commerce using cryptographically signed "Mandates" (W3C Verifiable Credentials); 60+ orgs (Mastercard, PayPal, Coinbase, American Express). The `x402` extension (reviving the HTTP 402 status code) adds stablecoin/crypto settlement.
- **Enterprise plumbing:** in Kubernetes environments, A2A traffic is increasingly fronted by protocol-aware gateways (e.g., the Linux Foundation's agentgateway) handling mTLS identity, rate limiting, and Agent-Card/Task-aware routing.

**Agent Communication Protocol (ACP) — merged:**
- IBM's ACP (from BeeAI) officially merged into A2A under the Linux Foundation (announced ~Aug 29, 2025). Kate Blair (IBM) joined the A2A Technical Steering Committee. New projects should target A2A directly. **Naming caution:** "ACP" is overloaded — IBM's Agent Communication Protocol, AGNTCY's Agent Connect Protocol, and OpenAI/Stripe's Agentic Commerce Protocol are three different things.

**Others:** **AGNTCY** (Cisco/Outshift + LangChain + Galileo, donated to Linux Foundation ~July 2025; "Internet of Agents" infrastructure — Directory, Identity, SLIM messaging, Observability); **ANP** (decentralized, W3C DIDs, not yet ecosystem-ready).

**Adoption skepticism [CONTESTED]:** analysts call the payments-protocol space a "wild west" (Shamus McGillicuddy, EMA). The convergence is on governance (Linux Foundation), not full unification. Practical baseline: run **MCP for tools + A2A for agent coordination** simultaneously; they are complements, not competitors.

**Key resources:** modelcontextprotocol.io (architecture docs + spec, current version 2025-11-25); Anthropic's MCP announcement; the A2A project site and Linux Foundation press releases; IBM's *What Is Agent2Agent (A2A) Protocol?* explainer; the 4sysops protocol-comparison article.

**Exercises:**
1. Build and register an MCP server (stdio) exposing 2–3 tools + 1 resource; connect it to Claude Code and to a custom client.
2. Stand up two A2A agents with Agent Cards and have one delegate a task to the other.

---

### Module 6 — Evaluation, Observability, Reliability & Cost — ~10–12 hrs

**Objectives:** How to evaluate agentic systems; trajectory evaluation; benchmarks and their pitfalls; observability; failure modes; guardrails; human-in-the-loop; and the cost/latency/efficiency frontier.

**Core concepts:**
- **Outcome vs. trajectory evaluation.** Anthropic's research-eval rubric scores factual accuracy, citation accuracy, completeness, source quality, and tool efficiency (0.0–1.0), using LLM-as-judge, starting from ~20 representative queries.
- **Deterministic vs. probabilistic verifiers** [ESTABLISHED lens]: distinguish cheap, binary, millisecond-latency **deterministic** checks (compilers, linters, type-checkers, unit tests) from expensive, non-deterministic **probabilistic** checks (LLM-as-judge, semantic review, visual diff). Build the verification stack to lean on deterministic sensors wherever the property is mechanically checkable, and reserve probabilistic judgment for genuinely subjective criteria. Format deterministic failures as corrective signals injected back into context rather than raw stack traces. This reframes a large part of "reliability": much of it comes from the deterministic feedback loop *around* the model, not from the model itself.
- **Reliability patterns** [ESTABLISHED]: the tool-side primitives from Module 2 are also eval/reliability concerns at the system level — explicit terminal states + a sliding-window loop guard to break silent infinite-reasoning loops, return-and-poll for slow tools, and return-a-reference to prevent context overflow. Agents "fail silently" (burning tokens on repeated failed calls, or emitting well-formatted but wrong output) far more than they crash, so these guards are first-order, not polish.
- **Benchmarks and their pitfalls [important]:** SWE-bench / SWE-bench Verified (real GitHub issues), τ-bench/τ²-bench (tool-agent-user interaction with policy adherence; introduces `pass^k` reliability), GAIA, WebArena, AgentBench. **Critical caveat:** *Establishing Best Practices for Building Rigorous Agentic Benchmarks* (arXiv:2507.02825) shows outcome-validity failures — e.g., a trivial empty-response agent scores 38% on τ-bench impossible tasks; ~24% of top-50 SWE-bench leaderboard positions may be wrong because passing tests ≠ resolving issues. Treat leaderboard numbers skeptically; build your own eval on your own data.
- **Observability:** OpenTelemetry-based tracing; tools like Langfuse, Arize. Wire this on day one, not month six. The mature pattern is a closed improvement loop: observe full production traces → cluster/enrich and annotate → convert failed traces into regression eval datasets → update prompts/tools/constraints — turning real failures into permanent test cases.
- **Cost/latency:** agents trade latency and cost for task performance; multi-agent ~15× tokens. Token usage dominates performance variance but also cost. (See also Module 1: KV-cache hit rate is the lever that most directly moves per-task cost and time-to-first-token.)

**Key resources:** the rigorous-benchmarks paper (arXiv:2507.02825); the τ-bench paper (Yao et al., arXiv:2406.12045) and `sierra-research/tau2-bench`; the ICLR 2026 blogpost *Ready For General Agents? Let's Test It.* on benchmark fragmentation; Langfuse's framework/observability writeups; LangChain's *The Agent Improvement Loop Starts with a Trace* for the observe→enrich→evaluate→update cycle.

**Exercise:** Build an evaluation harness with an LLM-as-judge rubric and trajectory logging; run the same agent across 3 frameworks (e.g., LangGraph, CrewAI, a raw loop) on one task set and compare success/cost/latency head-to-head. Add a deterministic-verifier layer (lint/test/compile) and measure how much of the quality gain comes from the feedback loop vs. the model.

---

### Module 6.5 — The Orchestration-Layer Tooling Landscape — ~10–14 hrs

**Objectives:** Understand the build-time frameworks, what each is good for, and how they compare — with LangGraph as the deep dive.

**LangGraph (deep dive) [ESTABLISHED for stateful production]:**
- Models an agent as a **directed graph with shared state**. Three primitives: **State** (a shared TypedDict/Pydantic schema with **reducers** controlling how node updates merge — default overwrite; `operator.add`/`add_messages` to accumulate), **Nodes** (Python functions that read state and return updates), **Edges** (routing — direct, or **conditional edges** where a function inspects state and returns the next node name). Inspired by Google's Pregel; executes in message-passing "super-steps." Compile before use.
- **Why it exists:** LangChain chains were DAGs; agents need **cycles** (loop: call tool → evaluate → maybe loop). Conditional edges are the agent's decision mechanism. The canonical teaching example is a self-correcting **generator → critic** loop: a conditional edge routes back to the generator while the critic flags `NEEDS_REVISION` and a revision counter is under its cap, else exits.
- **Production features:** persistent checkpointing (memory-based storage swapped for durable backends like a relational DB or a DynamoDB saver), crash recovery (resume from the last good checkpoint on an API timeout), time-travel debugging (reconstruct/branch from any historical checkpoint), human-in-the-loop interrupts (`interrupt()` pauses a thread before a high-risk action; a `Command(resume=...)` payload resumes it), graph-migration support, and **threads** (parallel sessions keyed by `thread_id`). "The only framework where 'what happens when step 7 fails' has a first-class answer."
- **When to use it:** durable state, checkpoints, human-in-the-loop, complex conditional/looping control flow. Overkill for linear 80%-of-queries tasks (an LCEL chain suffices).

**The broader landscape (when to use which):**
- **LangChain** — breadth/integrations; the orchestration "default" with large surface area.
- **LlamaIndex** — RAG/document-centric agents and retrieval quality.
- **CrewAI** — role-based multi-agent ("Planner/Researcher/Writer" crews); fast prototyping.
- **AutoGen / AG2** — conversational/event-driven multi-agent (GroupChat); AG2 is the community fork after Microsoft moved AutoGen toward the Microsoft Agent Framework.
- **OpenAI Agents SDK** — OpenAI-first, handoff model (triage → specialist → escalation), guardrails; production successor to Swarm.
- **Pydantic AI** — type-safe, contract-first agents; minimal abstraction; FastAPI-style DX.
- **Google ADK** — GCP/Gemini-native, multimodal, ready-made Sequential/Parallel/Loop agents, most mature A2A support.
- **smolagents** — minimalist, code-generating ("CodeAct") agents; "bring your own while-loop."
- **Claude Agent SDK** — Anthropic-first; the framework underlying Claude Code.

**Decision heuristic:** first-party SDK if you're single-vendor and want depth; LangGraph for durable/observable stateful orchestration; CrewAI for fast role-based prototyping; Pydantic AI for type safety; LlamaIndex for retrieval-heavy. And per Anthropic: start with raw APIs and add a framework only when you understand what it abstracts.

**Key resources:** LangGraph docs (Graph API overview at docs.langchain.com); LangChain's original LangGraph blog post; the LangGraph interrupts/human-in-the-loop docs and AWS's *Build Durable AI Agents with LangGraph and Amazon DynamoDB* for the checkpointing pattern; the Langfuse and Uvik framework comparisons; the Anthropic caution against premature framework abstraction in *Building Effective Agents*.

**Exercise:** Build the *same* tool-using agent in LangGraph (with a conditional-edge generator→critic loop + a durable checkpointer + one human-in-the-loop interrupt), in CrewAI, and in raw Python. Compare lines of code, debuggability, and where each abstraction helps or hurts.

---

## PHASE 2 — CODING AGENTS (USING THEM EFFECTIVELY)

### Module 6B — Coding Agents in Practice: Claude Code, Codex, and the Harness Landscape — ~12–16 hrs

**Objectives:** Use the major coding agents effectively; understand how their harnesses manage context (filesystem-as-context, repo maps, prefix stability); master practical workflows (TDD, planning-first, code review, monorepos, multi-file edits, debugging); and agent legibility/observability.

**Claude Code [ESTABLISHED practices]:**
- **CLAUDE.md** — the agent's "constitution," auto-loaded every session; project conventions, build/lint/test commands, architecture, forbidden patterns. Keep it tight (professional monorepos ~13–25KB; a common rule of thumb is under ~200 lines, excluding things the model can infer by reading the code); phrase rules as "Prefer X over Y" rather than "Do not." Use `/init` to scaffold, `#` to append memory.
- **Context discipline** — `/context` to inspect the budget (note the auto-compact buffer reserves tokens); `/clear` between tasks; one thread per *task*, not per project.
- **Subagents** — specialized instances with their own context window, system prompt, and tool allow/deny lists; built-in **Explore** (read-only codebase exploration), **Plan**, and general-purpose types; custom ones in `.claude/agents/`. They keep the main context clean by returning only summaries.
- **Skills / slash commands** — `.claude/skills/<name>/SKILL.md` (custom commands have been *merged into skills*; `.claude/commands/` still works). Skills support progressive disclosure and `context: fork` (run in an isolated subagent).
- **MCP integration** — `claude mcp add ...` for GitHub, databases, browsers, internal tooling.
- **Planning workflows, permissions, hooks** — plan mode; scoped allow/ask/deny permissions in `.claude/settings.json` (auto-run read-only commands like `git status`, confirm risky ones like `git push`, block sensitive files like `.env`); hooks for formatting/validation (PostToolUse auto-format, Stop hooks to surface `git status`) — block at *submit* time, not *write* time, to avoid breaking reasoning chains.
- **The Explore → Plan → Implement → Commit cycle** — read structure and git history, produce a reviewable plan, execute while running tests, then summarize into a conventional commit / PR.
- **Headless/CI & multi-agent** — `claude -p` for headless; GitHub Actions for an auditable, self-improving "bugs → improved CLAUDE.md → better agent" flywheel; Agent Teams for parallel subagents (Feb 2026).

**Claude Code anti-patterns / [CONTESTED] areas:**
- **Subagents can be brittle:** "Importance is not the trigger. Context isolation is the trigger" — spawning a 5-subagent plan→code→test→review→commit *sequential* pipeline is worse than one agent doing them in order, because each subagent loses context the next needs. Subagents pay off for *parallel* exploration (sweet spot ~3–8 branches), not sequential pipelines. A concrete limitation: subagents cannot present interactive permission prompts — restrict them to read-only tools and defer Edit/Write/Bash to the parent. Shrivu Shankar's "Master-Clone" critique (blog.sshh.io) argues custom subagents are brittle vs. giving the main agent rich CLAUDE.md context and letting it self-delegate.
- **Skill auto-invocation is unreliable:** multiple practitioners report skills not firing unless explicitly named, and resort to slash commands or listing skills in CLAUDE.md (described as "a hack").

**OpenAI Codex [ESTABLISHED practices]:**
- **AGENTS.md** — the open, cross-tool "README for agents" (adopted by Codex, Cursor, Copilot, Jules, Factory, Amp, Aider, etc.). Codex builds an instruction chain walking from `~/.codex/AGENTS.md` (global) down through project and nested directories, with `AGENTS.override.md` precedence and `project_doc_fallback_filenames`. Lead with commands; keep under ~150 lines; nest per-package (OpenAI's own repo has dozens of AGENTS.md files).
- **Config & legibility** — `~/.codex/config.toml`, profiles, `project_doc_max_bytes`, sandbox/approval policies (keep tight by default; loosen for trusted repos). Codex is trained to run tests mentioned in AGENTS.md before finishing.
- **Workflows** — TDD ("write failing tests, commit them, implement until green, don't modify the tests"); Codex reviews 100% of OpenAI's PRs; subagent workflows for bounded offloading; skills (`.agents/skills`) + automations ("skills define the method, automations define the schedule"); Codex can run *as* an MCP server inside larger workflows.
- **Spec-driven development** — Codex is often paired with an SDD loop (author a spec with acceptance criteria → generate a task list → implement + test → a review pass validates against the spec), sometimes split across a spec-author/implementer/reviewer trio. Treat the multi-agent split as optional structure, not a requirement (see the SDD skepticism below).
- **Anti-patterns:** overloading the prompt with durable rules instead of AGENTS.md; not letting the agent see test/build output; treating it step-by-step instead of in parallel; one thread per project instead of per task; accepting output without running verification.

**How coding harnesses manage context [conceptual]:**
- **Filesystem-as-context / index-free retrieval** — Claude Code and Codex navigate via **grep/find/bash + reasoning**, not a vector DB. Anthropic notes latest models are effective at "discovering state from the filesystem," favoring a fresh window over compaction for multi-window tasks. The pro-grep evidence: Augment's founding engineer reported that for SWE-bench tasks, "grep and find were sufficient" and embedding-based retrieval was not the bottleneck. The counter [CONTESTED]: Cursor supplements structural search with embeddings, and critics argue grep fails for unstructured/multimodal enterprise data (see *GrepRAG*, arXiv:2601.23254, and the DCI "direct corpus interaction" paper).
- **Repo maps** — **Aider** maintains a "Repo Map" to hold repository-wide structure in a small context window.
- **Prefix stability and the "orientation tax."** Production coding harnesses assemble the system prompt from many conditional blocks and a task-scoped tool subset, but must preserve prefix integrity for KV-cache reuse (deterministic schema serialization, no volatile timestamps; see Module 1). Several harnesses also inject a repository map/topology up front to eliminate the "orientation tax" — the wasted opening turns an agent otherwise spends running search commands to learn an unfamiliar repo.

**The harness comparison [CONTESTED / fast-moving]:**
- **Claude Code** — agent-first, terminal-native, deepest reasoning + MCP; best for autonomous/overnight work and complex multi-file refactors; Anthropic-only models.
- **Codex (CLI/app)** — fast, strong autonomous background tasks, tight AGENTS.md/skills/MCP integration.
- **Cursor** — IDE-first, supervised; best at-the-keyboard DX, multi-model, parallel Agent Tabs; credit-based pricing requires spend-limit vigilance.
- **Aider** — open-source, terminal, git-native (commit-per-change), BYOM, token-efficient; best for surgical large refactors and cost control.
- **Key insight:** *the harness matters as much as the model* — the same model scores very differently across harnesses; scaffolding can swing results by 15+ points (e.g., Terminal-Bench differences between harnesses running the same model). Most productive teams use a combination (IDE agent for daily flow, terminal agent for hard problems).

**Spec-driven development [EMERGING/CONTESTED]:** GitHub Spec Kit, AWS Kiro, BMAD-METHOD. Martin Fowler's skeptical take: spec-kit "created a LOT of markdown files... verbose and tedious to review... I'd rather review code." Useful taxonomy: spec-first vs. spec-anchored vs. spec-as-source. Token overhead 20–40% higher per feature; doesn't fit small fixes. Vendor productivity claims (3–10×) are uncontrolled.

**Harness engineering (the regulated-system view) [EMERGING framing]:** a useful lens treats the coding agent as a controlled system regulated by **feedforward guides** (repo maps, architectural checklists, and code templates injected *before* the run) and **feedback sensors** (the deterministic linters/type-checkers/compilers/tests plus probabilistic LLM-as-judge/visual-diff review from Module 6). The claim — that much of coding-agent reliability is harness design rather than raw model capability — is consistent with the harness-swing evidence above.

**Key resources:** Anthropic's *Claude Code Best Practices* and the Claude Code docs (code.claude.com); OpenAI's *Codex Best Practices* and *AGENTS.md* guides (developers.openai.com/codex); agents.md; Shrivu Shankar's *How I Use Every Claude Code Feature*; alexop.dev's Claude Code stack guides; Martin Fowler's SDD article and *Harness engineering for coding agent users* (martinfowler.com); LangChain's *Improving Deep Agents with Harness Engineering* (build-side complement); the artificialanalysis.ai coding-agents comparison; the *Context Engineering for AI Agents in Open-Source Software* paper (arXiv:2510.21413) on version-controlled markdown instruction files.

**Exercises:**
1. Take a real repo; write a strong CLAUDE.md and AGENTS.md; run the same multi-file refactor in Claude Code and Codex; compare.
2. Run a TDD workflow end-to-end (failing tests → implement → green) with explicit "don't modify tests."
3. Build a headless CI flow (Claude Code in GitHub Actions or `codex exec`) that runs lint/test and proposes a PR.
4. Set up a read-only code-review subagent and a parallel-exploration subagent; observe where each helps vs. adds "agent theater."

---

## PHASE 3 — AGENT MEMORY (SYSTEMATIC DRILLDOWN)

### Module 7 — Memory Foundations: Types, Mechanisms, and the Context-Management Relationship — ~10–12 hrs

**Objectives:** Cleanly delineate **context management vs. memory**; master the memory taxonomy and mechanisms; understand the CoALA organizing framework and the MemGPT paradigm in depth.

**Context management vs. memory [the key distinction]:**
- **Short-term/working memory IS the context window** — the only memory the model directly reasons over.
- **Long-term memory is external** (vector store, KG, files) and must be **retrieved into the context window** to influence generation. So memory is a *superset* concern that includes — but extends beyond — context management: context management governs the working set; memory governs persistence, consolidation, and retrieval across sessions.

**The CoALA organizing framework [ESTABLISHED conceptual scaffold]:** *Cognitive Architectures for Language Agents* (Sumers, Yao, Narasimhan & Griffiths, Princeton; arXiv:2309.02427; TMLR 2024 — note the shared authorship with ReAct and Tree of Thoughts) is the canonical framework systematizing agent memory. It casts a language agent as **working memory** (the active context) plus optional **long-term memories** — **episodic** (past experience/trajectories), **semantic** (facts/knowledge), and **procedural** (skills/code/the agent's own logic) — operating over a **structured action space** (internal memory actions + external grounding actions) via a **decision cycle**: a planning stage that proposes and evaluates actions through reasoning and retrieval, then a selected learning or grounding action. Use CoALA as the scaffold onto which the specific mechanisms below hang; it also cleanly locates procedural memory as including CLAUDE.md/AGENTS.md-style instruction files and skill libraries.

**Memory types (Tulving-inspired, as systematized by CoALA):** two axes — retention (short vs. long term) × functional form. **Episodic** (specific past interactions/trajectories), **semantic** (facts, user profile, world knowledge), **procedural** (how-to/skills/behavior).

**Mechanisms:** retrieval-augmented memory (vector embeddings + semantic search), summarization-based memory, memory consolidation (episodic → semantic — e.g., abstracting repeated "compile failed: dependency missing" episodes into a durable rule "inspect package.json and install deps before compiling"), entity/knowledge-graph memory, and procedural memory (skill libraries — cf. Voyager). A useful encoding discipline (Tulving's binding principle): episodic writes should preserve the event *with* its temporal/causal/spatial context rather than pre-summarizing it away, since that context is what makes later retrieval and imitation useful; consolidate and evict on a separate, slower path.

**The MemGPT / virtual context management paradigm [ESTABLISHED conceptual anchor]:**
- Packer et al., *MemGPT: Towards LLMs as Operating Systems* (arXiv:2310.08560, UC Berkeley). Borrows OS **virtual memory paging**: a tiered hierarchy (main context = "RAM"; external = "disk") where the agent uses **function calls** to page information in/out, **self-edits** its own context, and uses **interrupts** to manage control flow. Three tiers in the Letta implementation: **core** (always-in-context memory blocks), **recall** (conversation history), **archival** (external store). Evaluated on document analysis and multi-session chat.

**Foundational memory-architecture papers:**
- **Generative Agents**: Park et al. (arXiv:2304.03442, UIST 2023) — the **memory stream** architecture: observation records → periodic **reflection** synthesis → **retrieval** (recency × importance × relevance) → planning. 25 agents, emergent social behavior; ablations show removing reflection/planning/memory degrades believability. The canonical episodic-memory + consolidation design.
- **Voyager**: Wang et al. (arXiv:2305.16291, NVIDIA/Caltech/Stanford/UT Austin; TMLR Mar 2024) — the **skill library** of executable code as **procedural memory**; lifelong learning in Minecraft. Per the paper: "It obtains 3.3x more unique items, travels 2.3x longer distances, and unlocks key tech tree milestones up to 15.3x faster than prior SOTA" (the 15.3× applies specifically to reaching the wooden-tool level).

**Key resources:** the four papers above; CoALA (arXiv:2309.02427) and its companion `ysymyth/awesome-language-agents` list; the DeepLearning.AI short course *LLMs as Operating Systems: Agent Memory* (with Letta founders Packer & Wooders); recent surveys — *Memory in the Age of AI Agents* (arXiv:2512.13564) and the `Shichun-Liu/Agent-Memory-Paper-List`; the NirDiamant `Agent_Memory_Techniques` repo (30 runnable notebooks covering buffers, vector stores, KGs, episodic/semantic, MemGPT, Mem0, Letta, Zep, Graphiti, LoCoMo).

**Exercises:**
1. Implement a MemGPT-style three-tier agent (core/recall/archival) with self-editing memory tools in Letta.
2. Implement a Generative-Agents-style memory stream with recency×importance×relevance retrieval and a nightly reflection step that consolidates episodic logs into semantic rules.

---

### Module 8 — Memory Frameworks, Production, Evaluation & the Contested Frontier — ~10–14 hrs

**Objectives:** Compare the major memory frameworks; know when you actually need memory; evaluate memory systems and their failure modes; and hold the contested benchmark debate honestly.

**Two memory-write paths [useful framing]:** memory can be written on the **hot path** (in-loop) — the agent itself decides, via tools, whether to ADD/UPDATE/DELETE/SKIP a memory during execution, giving it agency over its own long-term state — or on the **cold path** (out-of-loop) — a background/asynchronous process extracts and consolidates memories after the fact, and a pre-inference step injects a compact user/profile summary into the next session. Hot-path memory is more responsive but adds latency and tool-call surface to every turn; cold-path memory keeps the live loop lean but lags freshness. Mem0 and similar systems expose both; choose per latency/freshness needs. (This is the operational complement to the consolidation pipeline in Module 7.)

**The framework landscape:**
- **Mem0** — managed, drop-in memory API; three-tier scopes (user/session/agent) over a hybrid vector + graph + key-value store; best for personalization/chatbots; ~48K+ GitHub stars.
- **Zep / Graphiti** — **temporal knowledge graph** with validity windows; best when the agent must reason about *how facts change over time*; Graphiti engine is Apache-2.0 open source, Zep Cloud is managed.
- **Letta (formerly MemGPT)** — OS-style self-managed memory for long-running autonomous agents; LLM-driven memory management.
- **LangMem / LangGraph memory** — native long-term memory for LangChain/LangGraph stacks; semantic/episodic/procedural types + fact extraction and behavior-level memory; path of least resistance if you're already on LangGraph.
- **Others:** Cognee (graph reasoning, local-first), Redis Agent Memory Server (low-latency backend), Semantic Kernel/Kernel Memory (Azure).

**When you need memory:** user-facing copilots needing personalization/continuity across sessions; long-horizon autonomous agents; agents whose context exceeds a window over time. **When you may not:** batch/analytics agents; tasks that fit in one window; cases where filesystem state suffices.

**Evaluation & failure modes:**
- Benchmarks: **LoCoMo** (long multi-session conversations; single/multi-hop/temporal/open-domain QA) and **LongMemEval** (harder; 500 questions; knowledge-updates + multi-session recall; ~115K-token conversations; ICLR 2025).
- Failure modes: stale memory, contradictory memory, retrieval misses, and **memory poisoning** (e.g., MemoryGraft-style procedural-memory attacks via disguised "successful experiences"). See *A Survey on the Security of Long-Term Memory in LLM Agents* (arXiv:2604.16548).

**The contested frontier [CONTESTED — teach this explicitly]:**
- **The Mem0 vs. Zep benchmark war.** Mem0's paper (*Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory*, arXiv:2504.19413, ECAI 2025) claimed SOTA on LoCoMo (66.9% J-score vs. OpenAI memory 52.9%; ~91% lower p95 latency; ~90% fewer tokens) and reported Zep at 65.99%. Zep's rebuttal (*Lies, Damn Lies, & Statistics*, Chalef & Rasmussen, May 2025) claimed Zep actually scores 75.14% and that Mem0 mis-implemented it; Mem0's counter-rebuttal (GitHub getzep/zep-papers issue #5) re-ran and reported Zep at 58.44%. The Zep numbers in play across the dispute: 84% (Zep original) → 65.99% (Mem0's measurement) → 75.14% (Zep corrected) → 58.44% (Mem0's re-run). **Lesson: treat any single memory benchmark number with caution.**
- **LoCoMo is itself flawed:** conversations average only ~16K–26K tokens (fit in modern windows); a category lacks ground truth; only ~81 QA pairs in some counts. Most damning: a simple **full-context baseline (~73% J-score) beats Mem0's best (~68%)** on Mem0's own results — i.e., the specialized memory system loses to just stuffing the transcript in.
- **Filesystem-as-memory beats frameworks [EMERGING]:** Letta reported a simple filesystem memory scoring 74% on LoCoMo vs. Mem0's 68.5%. The broader "files are all you need" debate (Jerry Liu/LlamaIndex; Harrison Chase/LangChain; Anthropic Skills as markdown folders) reframes it: filesystem as *interface*, database as *persistence* — "both, in the right layers." Cloudflare pushes back (managed ingestion/retrieval pipelines beat raw filesystem access; memory must "stay useful as it grows, not just perform on a clean benchmark").
- The broader market parallel: agent memory in 2026 "feels like the vector-database space in 2022" — multiple approaches, benchmark wars, consolidation likely.

**Recent research [EMERGING]:** Agentic Context Engineering (ACE, arXiv:2510.04618); procedural-memory work (MemAgent arXiv:2507.02259; ProcMEM; Mem-α); context-rot mitigation architectures (General Agentic Memory; ARC, arXiv:2601.12030; GRU-Mem).

**Key resources:** the Mem0 and Zep papers + the public dispute (Zep blog + GitHub issue #5); the Atlan, Vectorize, and Agentmarketcap framework comparisons; the DeepLearning.AI Letta course; the surveys above.

**Exercises:**
1. Stand up Mem0, Zep, and a plain filesystem-memory baseline against the *same* multi-session task; measure accuracy, p95 latency, and token cost. Reproduce the "full-context baseline" comparison.
2. Inject a contradictory/stale fact and a poisoned "successful experience"; observe retrieval and behavior drift.

---

## Capstone — The Integrative Project

**Build a long-running, memory-augmented research-and-coding assistant**, then write an evaluation report comparing design choices. Concretely:

1. **Core agent (Phase 1):** a single-agent ReAct loop in LangGraph with a checkpointer, conditional-edge tool loop, explicit context-budget instrumentation, KV-cache hit-rate measurement, and a compaction/fresh-window strategy.
2. **Tools + protocols (Modules 2, 5):** expose your data sources via an MCP server; build tools that return references-not-payloads and resolve to explicit terminal states; add a second A2A-exposed specialist agent and let the core agent delegate to it.
3. **Multi-agent ablation (Module 4):** add an orchestrator-worker mode for the parallelizable research portion; measure the single vs. multi tradeoff (success, ~token multiplier, latency) and locate the isolation boundary empirically.
4. **Coding arm (Phase 2):** wire the assistant to drive Claude Code or Codex headlessly with a curated CLAUDE.md/AGENTS.md to implement and TDD-verify a feature in a real repo; add a deterministic-verifier feedback loop (lint/test/compile).
5. **Memory (Phase 3):** add a MemGPT-style tiered memory and a long-term store, with both hot-path and cold-path writes; then run the contested comparison — your memory framework vs. a filesystem-as-memory baseline vs. full-context — on a multi-session eval.
6. **Evaluation (Module 6):** an LLM-as-judge rubric + trajectory logging + OpenTelemetry tracing, plus the observe→enrich→evaluate→update improvement loop; a written report that takes positions on every contested axis with your own measured evidence.

This ties together context engineering (the spine), tool/protocol mechanics, the multi-agent and memory debates, and coding-agent harness usage.

---

## Recommended Sequencing & Effort

- **Phase 1 (Modules 0–6.5):** ~8–10 weeks. This is the foundation; do not skip Modules 1 (context engineering) and 6 (eval). Module 0 and parts of 4 are skim-only given the learner's background.
- **Phase 2 (Module 6B):** ~2–3 weeks, can run in parallel with late Phase 1.
- **Phase 3 (Modules 7–8):** ~3–4 weeks.
- **Capstone:** ~2–3 weeks, integrative.
- **Total:** ~14–18 weeks part-time.

**Sequencing principle:** Context engineering (Module 1) is prerequisite to *everything*, including the multi-agent and memory debates, which are best understood as special cases of context management.

## Recommendations

**Stage 1 — Build the spine (weeks 1–4).** Do Modules 0–2 with the "raw API first" discipline. **Benchmark that would change your path:** if your raw-loop agent already passes your task eval at acceptable cost, *do not* adopt a framework yet. Instrument context budgets — and KV-cache hit rate — from day one.

**Stage 2 — Patterns and tooling (weeks 4–8).** Modules 3–6.5. Build the three reasoning loops and the three-framework comparison. **Threshold:** adopt LangGraph only when you need durable state, checkpoints, human-in-the-loop, or genuine cyclic control flow; otherwise stay with chains/raw loops.

**Stage 3 — Coding agents (weeks 7–10, overlapping).** Module 6B. Invest most in CLAUDE.md/AGENTS.md quality, TDD workflows, and the deterministic feedback loop; these dominate output quality. **Threshold:** reach for subagents only when you have ≥4 genuinely parallel, weakly-coupled branches; otherwise a single agent is better.

**Stage 4 — Memory (weeks 10–14).** Modules 7–8. **Decision rule:** before adopting any memory framework, run the filesystem-as-memory and full-context baselines. Adopt Mem0/Zep/Letta *only* if they beat those baselines on *your* data at acceptable latency/cost. Choose by use case: Mem0 (personalization), Zep (temporal reasoning), Letta (long-running autonomy), LangMem (already on LangGraph).

**Stage 5 — Capstone & synthesis (weeks 14–18).** Take measured positions on every contested axis.

**Cross-cutting:** Wire observability and an eval harness on day one. Re-derive leaderboard claims on your own tasks. Treat the field as moving monthly — re-check docs and benchmarks quarterly.

## Caveats

- **Rapid evolution / dated specifics.** Tool versions, model names, pricing, benchmark scores, and feature sets (especially for Claude Code, Codex, Cursor, and the protocols) change monthly; treat all version-specific and price-specific details as snapshots requiring re-verification. The Manus cost figures (~100:1 token ratio; ~10× cached/uncached price gap; ≈$0.30 vs ≈$3.00/MTok) are one team's reported numbers from mid-2025 and will drift with pricing. Several 2026-dated sources are vendor/SEO content; primary sources are prioritized, but some forward-looking items (e.g., a rumored joint MCP/A2A spec, an "A2A v1.0" label, specific Linux Foundation transfer dates) are unconfirmed projections, not established fact.
- **Benchmark numbers are contested.** The agent-memory scores (Mem0 vs. Zep) are the subject of an active, public methodological dispute; the multi-agent "+90.2%" figure is an Anthropic *internal* eval on research tasks and should not be generalized to coding or other domains. Agentic benchmarks have documented validity problems (trivial agents scoring well; tests passing without resolving issues).
- **Some secondary claims could not be fully verified to primary sources**, including the "Tran & Kiela" single-agent-superiority paper, a "39–70% sequential reasoning degradation" stat attributed to Google Research, and certain incident-response multi-agent figures; these are flagged as emerging/unverified and should be checked before relying on them. A separately circulated claim that "populations with only 10% honest agents achieve 74% higher collective welfare than fully honest populations" could not be traced to a primary source and is omitted here pending verification.
- **Selection bias toward Anthropic/OpenAI/LangChain/Manus sources.** These organizations publish the most detailed practitioner guidance, which weights the curriculum toward their framing (e.g., "context engineering," "simplest thing first," KV-cache primacy). The contested-frontier modules are designed to counterbalance this with critical and competing views.
