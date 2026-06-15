# Ingest Backlog (manual stand-in for Throughline Property 1)

> **Purpose.** A holding pen for *position-relevant* items found in the wild **before the
> stay-current ingest loop (Property 1, built Phase 2.3 / Module 5) exists.** This is the manual
> version of that loop: when something the field ships touches a position we hold or a debate we
> track, it lands here with its primary-source pointers, curriculum anchors, and the *testable
> hypotheses* it surfaces — so it isn't lost to a closed conversation (the exact failure Property 1
> is meant to prevent). **Drains into the real ingest pipeline when Phase 2.3 builds it.**
>
> **Discipline.** (1) Cite **primary** sources, verified firsthand (§0.16) — newsletters/blogs are
> pointers, not evidence. (2) Separate *durable content* from *hype framing*. (3) Practitioner
> assertions are **hypotheses to test on our substrate**, not facts to adopt — record them as such.
> (4) Tag each item with the synthesis §/phase it bears on, and a status.
>
> Format per entry: **title** · found-date · status · primary sources (verified?) · curriculum
> anchors · testable hypotheses · what NOT to adopt.

---

## [INGEST] Loop engineering — "design loops that prompt your agents"

- **Found:** 2026-06-14 (AlphaSignal newsletter, "loop engineering & loopmaxxing"). Surfaced by the user; manually triaged.
- **Status:** OPEN — parked for Phase 2.4 (multi-agent) + Phase 3.0/3.1 (Module 6B coding agents); a §2.3 data point now.
- **One line:** the leverage point is moving from crafting prompts to **designing the control loop that orchestrates agents over time**; the emerging anti-pattern is **"loopmaxxing"** — open-ended `while(true)` without deterministic exit conditions (burns credits, degrades observability, accrues "comprehension debt").

**Primary sources (all verified firsthand 2026-06-14 via WebSearch):**
- **Boris Cherny** (Head of Claude Code, Anthropic) — *"I don't prompt Claude anymore… my job is to write loops"* (interview, June 2026; ~700k views). Runs `/loops` + a couple hundred agents reading his GitHub/Slack/Twitter. Context: Dec 2025 — 259 PRs, IDE not opened for a month; Mar 2026 — Claude Code 100% written by Claude Code. → `officechai.com/ai/i-now-just-write-loops-to-prompt-claude-code-claude-code-creator-boris-cherny/`
- **Peter Steinberger** (steward, **OpenClaw** — fastest-growing OSS AI project) — *"You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents"* (X, `x.com/steipete/status/2063697162748260627`, June 7 2026). Also "I ship code I don't read" (Pragmatic Engineer). Critics' caveat: *"works well when compute is free… a budgeting question."*
- **Addy Osmani** (Google) — *Loop Engineering* (`addyosmani.com/blog/loop-engineering/`) + *Agent Harness Engineering*. The six primitives: automations (triggers), worktrees (isolation), skills (on-disk project knowledge), connectors/MCP, **maker/checker split** (one agent proposes, a different one verifies), memory (on disk — *"the model forgets everything between runs"*).
- **Andrej Karpathy** — **autoresearch** (GitHub, ~21k stars; Mar 7 2026): a 630-line Python loop running ML experiments overnight, keeping changes that beat best, committing to git; driven by a plain-English `program.md`. 700 experiments / 2 days / +11% on a competitive benchmark; Shopify's Lütke reported +19%. → `thenewstack.io/karpathy-autonomous-experiment-loop/`. **Note: this is the shape of *our own* experiment-loop substrate.**

**Curriculum anchors (where this bears, in priority order):**
1. **synthesis §2.3** — "How much infrastructure to build around the model (Garry-school vs Manus-school)." This is a strong **Manus-school** data point (strict control loops; deterministic code handles execution; LLM only for dynamic decisions). *Add as a dated source when §2.3 is next revised.*
2. **Phase 3.0/3.1 (Module 6B, coding agents)** — the direct topic. The pragmatic-path checklist = a Module 6B reading note: minimal loop + human verify → automate proven steps → separate task/check agents → trace-logging → iteration caps (≤2–3 retries) → explicit human handoff.
3. **Phase 2.4 (Module 4, multi-agent)** — the maker/checker split ("an agent looping over its own flawed logic reinforces mistakes rather than fixes them → use a separate evaluator"). A **position on the single-vs-multi-agent debate** (verifier isolation). Tensions with **§1.2** (errors-as-signal): is a failed sub-agent trace noise to terminate, or signal to preserve?
4. **Phase 2.1 (Module 6, eval)** — "loops need verifiable success (tests/compile/exit code); fuzzy goals → infinite drift." Eval-as-exit-condition.
5. **Module 7/8 (memory)** — Osmani's *"memory must be on disk, not in context"* is a data point for the **memory-framework-vs-filesystem** debate.

**Testable hypotheses it surfaces (convert to Claim/Evidence on our substrate — not facts yet):**
- *Loopmaxxing cost:* open-ended iteration burns "millions of tokens" vs a bounded control loop — a measurable cost claim (ties to §3.3 / KV-cache economics; and to our own spend-cap discipline).
- *Self-review reinforces errors:* a single agent reviewing its own output reinforces mistakes; a **separate** verifier fixes them. → the Phase 2.4 verifier-isolation experiment. (We can test: same-agent self-check vs separate-scorer on our harness.)
- *Subagent cost-vs-value:* sub-agents "burn more tokens — spend them where a second opinion is worth paying for" (Osmani) — a cost/benefit threshold, testable.

**What NOT to adopt (hype framing, per §0.16 critical read):**
- "You shouldn't be prompting anymore / prompting is dead / loop engineering is the new core skill" — the "X is the new Y" rhetoric. The *durable* content is the anti-pattern taxonomy + the pragmatic-path checklist, not the obituary for prompting.
- **"Cognitive surrender" cuts against learning-first.** Cherny/Steinberger's "I ship code I don't read" is the *opposite* of this project's load-bearing principle. Note as a **tension**, not a model to emulate: their goal is throughput; ours is the user's own learning + defensible positions. The article's own "comprehension debt / no cognitive surrender" warning is the part that aligns with us.

**Validation-of-us bonus:** we *independently* built much of the prescribed "pragmatic path" — `run_tool_loop` has a loop-guard (stuck-termination), iteration caps, error-as-data + crash-robustness (trace-logging/observability), and a separate scorer (maker/checker). Lesson §0.22 (loop-guard idempotency) is a loop-exit-condition finding. → a [CANDIDATE-CONTRIBUTION] angle: our disciplined harness as a worked instance of strict-control-loop engineering.
