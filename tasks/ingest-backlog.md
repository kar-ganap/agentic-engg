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

---

## [INGEST] Self-repairing agent harness — Opik / Comet ML (trace → diagnose → fix → regression)

- **Found:** 2026-06-15 (AlphaSignal, **sponsored issue** — Comet ML). User-surfaced; manually triaged.
- **Status:** OPEN — primarily Phase 2.1 (eval) + Phase 3.0/3.1 (coding agents); §1.2 + Property-4 tie-ins.
- **Source class: LOWEST TRUST — vendor marketing** ("sponsored," "don't forget to star 🌟," "worth a look"). Per §0.16: extract the *pattern*, discard the product claims.
- **One line:** observability that stops at the trace is the wrong abstraction; the real work is *after* the trace — diagnose → propose fix → rerun against the failing input → **lock the failure as a regression test**. Opik automates that loop (human approval is the one manual step — so it does *not* "close on its own," contra the copy).

**Verified firsthand 2026-06-15 (WebFetch `github.com/comet-ml/opik`):** real; **~19.7k stars** (newsletter said 19.3K — consistent). Confirmed features: automatic **tracing** (`@opik.track`, 50+ frameworks), **LLM-as-judge** eval (hallucination/RAG/moderation), **regression/pytest** integration, **Agent Optimizer** (prompt/tool optimization). **NOT independently confirmed:** the *"Ollie"* trace→diagnose→fix *coding-agent* specifically — repo surfaces "Agent Optimizer," not a named self-repair coding agent; treat "Ollie" as newer/vendor-forward framing pending firsthand check.

**Durable pattern (what to keep):** the **closed debug loop** — *regression-from-real-failures* (every debugged failure becomes a test), trace→root-cause→diff→rerun→lock, plain-English assertions compiled to LLM-as-judge, an end-to-end agent sandbox.

**Curriculum anchors:**
1. **Phase 2.1 (Module 6, eval) — strongest.** Regression-from-real-failures + plain-English-assertions→LLM-as-judge. *Caveat:* sold as clean pass/fail; judge calibration/noise is a known hard problem Module 6 must confront, not a solved one.
2. **Phase 3.0/3.1 (Module 6B, coding agents).** The self-repair loop = a coding-agent harness; raises a **build-vs-adopt** question for our own harness (we already have ad-hoc tracing in `events.py` + a scorer).
3. **§1.2 (failures are high-signal tokens).** "Regression from real failures" is the productionized form of "preserve failures, they carry signal."
4. **§2.3 (Manus-school vs Garry-school).** Maximal-infrastructure-around-the-model — another Manus-school data point.

**Meta (the strongest hit): a commercial cousin of our own method.** Opik's loop ≈ what we already practice — "every debugged failure → regression test" = our **stash-based bug-fix proof** + TDD failing-first; "rerun against the exact failing input, side-by-side" = our **reproducibility**; "human approval is the one manual step" = **learning-first**; "harness gets harder to break each cycle" = accreting `lessons.md` + 194-test suite. → strengthens the **Property-4 [CANDIDATE-CONTRIBUTION]** ("disciplined research-software-with-AI") and is a positioning reference.

**What NOT to adopt:**
- Vendor claims unverified; "the loop closes on its own" is overstated (human approval remains).
- Same **cognitive-surrender** risk as the loop-engineering item — approve-diffs-without-understanding runs against learning-first.
- **Don't reflexively adopt a heavy vendor framework** — we *write* the load-bearing harness on purpose (minimal-code / learning-first). Opik is a reference/comparison, not a dependency to pull in.

**Testable hypotheses it surfaces:** LLM-as-judge agreement vs human grading on our position-forming tasks (the eval-reliability question, Phase 2.1); whether regression-from-real-failures measurably hardens a harness over cycles (we have the data — `lessons.md` + test growth).

---

## [INGEST] Curriculum-currency note — newer agentic-reasoning survey (Module 3)

- **Found:** 2026-06-15 (verifying the Phase 2.0 / Module 3 reading list). Type: **curriculum currency** (a cited resource has a newer companion that postdates the curriculum).
- **Status:** OPEN — read for Phase 2.0 Thread B; consider a Module 3 reading-list refresh.
- **Finding:** `Agentic_Engineering_Curriculum.md:120` cites survey **arXiv:2508.17692** (Zhao et al., *LLM-based Agentic Reasoning Frameworks: A Survey from Methods to Scenarios*, Aug 2025) **and** the `weitianxin/Awesome-Agentic-Reasoning` list. Verified firsthand: that list is actually the companion to a **newer** survey — **"Agentic Reasoning for Large Language Models," arXiv:2601.12538 (Jan 2026)** — which postdates the curriculum. Both surveys are real; the Jan-2026 one is the repo's actual basis and its taxonomy (foundational → self-evolving → collective reasoning) is directly on-point.
- **Action:** prefer **arXiv:2601.12538** for Module 3 orientation; optionally refresh the curriculum's Module 3 resource line (the curriculum is the seed dataset, not gospel — keep it current as the field moves). The three seminal primaries (ReAct 2210.03629, Reflexion 2303.11366, ToT 2305.10601) + Plan-and-Solve 2305.04091 are all verified and unchanged.
- **Anchors:** Module 3 / Phase 2.0 reasoning thread; the project's own stay-current ethos (this is a manual Property-1 hit on our *own* curriculum).
