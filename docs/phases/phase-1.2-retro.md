# Phase 1.2 — Back-fill: Compaction, Tool-selection, Coverage Ledger — Retro

> Stage-1 back-fill of two Module-1/2 exercises that a fidelity audit found stranded (lessons §0.26).
> Plan: `~/.claude/plans/snuggly-launching-graham.md`. Branch `phase-1.2-backfill`.

## Summary

Three threads. **Thread 0** installed the systematic anti-lapse fix (`tasks/coverage.md` + lessons
§0.26). **Thread A** (tool-selection) resolved position #2 → **§1.10 `tool-selection`, candidate
78**: confusable-sibling *presence* — not count — degrades first-tool selection; a sibling whose
NAME matches the request verb captures the call (step-function; causally pinned by a verb-swap;
cross-provider DeepSeek+Haiku); namespacing recovers. **Thread B** (compaction) resolved §1.2 →
**`compaction-preserve-failures`, candidate 74**: preserving failures *verbatim* beats summarizing
— **iff the agent's reasoning is ephemeral**; with persisted reasoning the model self-rescues
(null, cross-provider). Both DVs are **mechanical** (first-tool match / ref-recall — no LLM judge,
so cheap and no grader-validation caveat). Thread B's substrate investigation is the phase's biggest
story (below).

## Concept-stream output (synthesis-anchored)

- **§1.10 (new):** tool selection is governed by lexical name↔request alignment, not tool count. The
  verb-swap is a clean causal isolation. 55 → 78.
- **§1.2 (literature-only → candidate):** compaction should preserve failures *verbatim* — iff
  reasoning is ephemeral. Reasoning-persistence is the boundary; the persist-regime is a *null*
  (self-rescue), the strip-regime is the *bite*. 65 → 68 (prereg) → 74. Refutes the pre-registered
  down-5–10 softening ("preserve the signal not the format") — `flag ≡ uniform`, so **verbatim**
  matters.
- **§2.1 (tension):** given a mechanism-level resolution — Manus-keep-it-in and Chroma-rot partition
  by *what carries the signal*; preserve a failure iff the model won't self-rescue it.

## Decisions made

- **Substrate switch to Haiku for compaction** (from the DeepSeek-primary default) — forced, not
  chosen: DeepSeek's stateful `reasoning_content` defeats content ablation (§0.27). This is exactly
  the CLAUDE.md carve-out ("compaction = Claude-anchor experiment"), now grounded in a repro.
- **Reasoning-persistence as the IV** — the recurring "the model rescued it anyway" confound became
  the independent variable that maps the §1.2 boundary. The key design move of Thread B.
- **Confidence calls (user-owned):** #2 → 78; §1.2 prior 68 → 74. Both moved only with the user.
- **Mechanical DVs** for both threads — deliberately no LLM judge (unlike Phase 2.0), removing the
  grader-validation caveat and the dominant cost.

## Validation gate

- `make check` green throughout (**244 tests**, +15 for compaction/selection; ruff + mypy --strict).
- **TDD** for `compaction.py` + the loop hook; **stash-proofed** twice (the preserve-vs-summarize
  invariant; the cache-inclusive trigger).
- **Substrate Discipline #1 honored** — both #2 and §1.2 pre-registered (falsifier + prior) *before*
  the powered spend; all smokes/design-iteration were explicitly pre-prereg instrument-tuning.
- **Reproducibility** — every number regenerates from a versioned script (`run_selection.py`,
  `run_selection_control.py`, `run_compaction.py`, prereg/record scripts); graph records match their
  scripts byte-for-byte (verified).

## Three-reviewer pass outcome (critical boundary — the load-bearing event of the close)

All three Opus reviewers (method-rigor / framing-stress / prior-art) **converged** — the measurements
are sound, the **framing and confidences were over-claimed**. It caught real issues, exactly like
Phase 2.0. Actioned (≥80):

- **§1.2 — reverted 74 → 68** (user-confirmed). Two reviewers judged the 68→74 up-move unearned:
  (a) the bite's sign is **engineered-guaranteed** (§0.28 removes every self-rescue channel, so
  "preserving info retains info" is near-tautological — the falsifier is near-vacuous);
  (b) the DV tests **payload survival**, not the stance's **behavioral-supervision** claim
  (Reflexion) — that stronger claim is **untested**; (c) the bite is **single-provider**. **Fixed:**
  the synthesis stance was **stale-unconditional** (contradicted its own conditional graph title) —
  rewritten to **lead with the null** + the operational framing ("depends on whether your compactor
  also strips reasoning"); the "down-5–10 REFUTED" over-generalization **reopened to untested**
  (flag≡uniform is a `keep_last` positional artifact + a random-token case, not the behavioral-lesson
  domain the softening covers); the "0.13, not an average artifact" magnitude framing corrected
  (honest contrast on *compacted* failures = 1.00 vs 0.00). **Prior-art hole closed:** base claim =
  **Reflexion/ReAct**; self-rescue = **scratchpad/CoT-faithfulness**; novelty scoped to the
  reasoning-persistence **boundary**. **New path-to-active** designed with the user: a
  behavioral-supervision test (corrective-the-agent-applies, task-success DV, non-reasoning provider).
- **§1.10 — shaved 78 → 74** (user-confirmed). The "degrades/failure/overriding-the-correct-
  description" framing is a **DV-labeling artifact** — the model applies the *same* rule in both arms;
  the DV calls a defensible synonym pick "wrong." **Retitled** to the earned mechanism ("models weight
  tool-NAME over tool-DESCRIPTION semantics"), reframed to **selection non-determinism, fixable by
  naming**; the namespacing leg (was 85) reframed as *entailed by* the mechanism (removes the
  collision), not an independent benefit. **Prior-art:** the mechanism *and* the causal design are
  both established (HANS / shortcut-learning) — contribution softened to "clean demonstration in tool
  selection"; add BFCL/MetaTool + a name-vs-description literature search.
- **§0.27 — reframed** from "DeepSeek anomaly" to a **documented provider-behavior class** (Anthropic
  `clear_thinking` + thinking-block replay; the persist/strip knob *is* that axis), + a verify-caveat
  (R1's documented behavior was the opposite of my v4-flash 400).
- **§2.1 — adjudicated toward Chroma** (eviction dominates; Manus keep-it-in is a narrow,
  usually-redundant special case; "signal-density > count" = importance-weighting, not novel).

**Author-judgment (60–79, appendix):** MetaTool/name-desc precedent search for §1.10; MemGPT/Generative-Agents
citations for §2.1; recursive-summarization citation for the `summarize_uniform` baseline. Ledgered
for the capstone literature pass, not blocking.

**Net:** two confidence corrections (both *down*), several reframes, no redo. The pass did precisely
its job — it stopped two over-claims (an unconditional §1.2 header carrying a 74; a "tool selection
fails" gloss) from being banked into the capstone. Graph trajectories: §1.2 **68→74→68**, tool-selection
**55→78→74** (corrections preserved in append-only history).

## Method wins (process-stream → `tasks/lessons.md`)

- **Coverage ledger (Thread 0)** — the anti-lapse counter (§0.26); generalizes the three-reviewer
  discipline to *coverage*, not just correctness.
- **Mechanical DV** — a deterministic DV (first-tool match / ref-recall) makes a whole experiment
  cheap and caveat-free; reach for it before an LLM judge.
- **Wire-level verification with an incompressible canary (§0.27)** — the only airtight test for "the
  model produced X unseen"; `cache_read` is not a cache-off signal.
- **Close every self-rescue channel to test tool-result compaction (§0.28)** — and turn the last one
  into the IV.
- **Docs-first on an extraordinary claim** — the user's "check the docs/web before concluding" turned
  a wrong "opaque server-side memory" framing into a grounded `reasoning_content` mechanism. The
  research subagent + a wire-level repro did what intuition couldn't.

## Rule changes (`/learn`)

- **`[ADD]`** §0.27 (DeepSeek `reasoning_content` statefulness defeats content ablation; verify at the
  wire with an incompressible value) + §0.28 (remove every self-rescue channel to test tool-result
  compaction). Both **filed** with triggers.
- **`[MODIFY]`** none needed — §0.21 (pilot validates the rig) and §0.24 (predict→verify) both fired
  as intended (the smokes validated the rig; the verb-swap prediction ≥0.80 verified at 1.00).
- **`[DELETE]` none.** Considered whether §0.28 is subsumed by §0.21 (pilot-validates-rig) —
  rejected: §0.21 is "validate the control at full N"; §0.28 is the substantive "compaction of
  results is a no-op unless self-rescue is blocked," which is itself the §1.2 finding.
- **Synthesis cleanup (post-review):** §1.2 moved off literature-only but **held at the prereg prior
  65→68** (the reviewer pass declined the 74 up-move) with a **lead-with-the-null** reframe + the
  down-5–10 clause **reopened to untested** (not refuted); §1.10 filed new then **shaved 78→74** and
  reframed to the mechanism; §2.1 adjudicated toward Chroma; §0.27 reframed as a documented behavior
  class. Two confidence corrections, both *down*, off the reviewer pass.

## Friction (where discipline slipped / cost time)

- **The substrate detour was long and I was wrong twice** — "stale KV cache," then "opaque
  server-side memory," before the docs + wire-level repro pinned it to `reasoning_content`. Cost: a
  large number of diagnostic cycles. *Root cause:* I trusted `cache_read=0` as a "cache-off" signal
  and reasoned about mechanisms instead of grepping the wire. §0.27 is the fix. (Mitigating: each
  wrong framing was falsified by the next control — the self-correction worked, just slowly.)
- **Five pre-prereg design iterations on the compaction task** (batching → cache-trigger → flavor-1
  redundancy → result-size → reasoning-strip). All legitimate (each a design flaw the smoke exposed),
  but it's a lot — the standing bar ("iterate only on design flaws / couldn't-have-known facts") held,
  and instrument-tuning-before-prereg (§0.28) kept it honest, but a sharper up-front model of "what
  can the model self-rescue" would have collapsed several rounds.
- **A patterned "incompressible" canary** (arithmetic-sequence refs) briefly re-introduced the
  reconstruction confound the research had just warned about — caught + fixed with `os.urandom`.

## Throughline property progress

- **No surface advanced** — Phase 1.2 is a Stage-1 back-fill; the first scheduled throughline surface
  is Phase 2.1 (Property 3). **Coverage ledger** (Thread 0) is a Property-adjacent *process* tool
  (anti-lapse), not one of the four surfaces.
- **Property 3 (re-evaluation) exercised in spirit** — two positions moved with pre-registered
  falsifiers (neither fired → confirm), not drift.
- **Property 4 (contribution):** three candidates — the §1.2 self-rescue-conditional finding, the
  §0.27 DeepSeek `reasoning_content` substrate finding (a crisp minimal repro worth reporting), and
  the reasoning-persistence-as-IV method.
- **FLAG (carried):** still zero built throughline surface across 1.0-ext / 1.1 / 2.0 / 1.2. **Phase
  2.1 must ship a runnable surface slice** (Property-3 staleness scheduler) — the coverage ledger's
  manual discipline is not the built surface.

## Carry-forward

- **§1.10 → active:** a 2nd task template / verb-pair (does lexical-capture generalize beyond
  "lookup"/"look up"?).
- **§1.2 → active: the behavioral-supervision test** (designed with the user at close) — the failure
  carries a *corrective the agent must APPLY* (a param-format rule / a precondition), learned early →
  applied late after a distractor stretch compacts it, with **task-success** as the DV (not payload
  survival) and **no intervening successful use** to re-teach it (else self-rescue via
  success-history) — run on a **non-reasoning provider** to restore cross-provider for the bite.
  Discharges three reviewer caps at once (behavioral DV + less-engineered + cross-provider).
- **Fresh-window half of the compaction exercise** → M7/8 memory bake-off (deferred, homed).
- **Held-out tool-eval set + eval methodology** → Phase 2.1 (the M6 eval module) — unchanged.
- **A non-reasoning DeepSeek model** could reach the `strip` regime → a possible cross-provider
  extension of the §1.2 bite (ledgered).
