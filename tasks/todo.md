# TODO

> Current-phase open items only. Future-phase items live in their respective phase plans (`docs/phases/phase-X.Y-plan.md`).

## Phase 1.0 — Context Engineering (Module 1) — **ACTIVE**

Branch: `phase-1.0-context-engineering`. Plan: `docs/phases/phase-1.0-plan.md`. **Critical boundary** (three-reviewer pass at close).

### Backlog (priority-ordered; core = 1–4)
- [x] **1. Infra** — `eval/accuracy.py` ✅ · `rot/haystack.py` (essay + tool_stream + diversity/same-item + benign-domain fix) ✅ · `rot/corpus.py` + P&P corpus ✅ · `rot/runner.py` ✅ · `experiments/phase-1.0/run_config.py` ✅. **61 tests green; committed (bda5d1d).** Benign-domain redesign after real-API smoke caught safety refusals (lessons §0.9).
- [ ] **2. A-baseline** — clean vs. distractor on essay haystack → validate harness reproduces Chroma mechanism.
- [ ] **3. A-structure-1** — tool-call/observation stream → `(ceiling, knee, slope)` + passband?
- [ ] **4. B** — KV-cache instrumentation + anti-pattern break/restore.
- [ ] **5. A-structure-2** — research-agent stream (distractor-rich). *(may slip to extension)*
- [ ] **6. A-§3.4** — failure-shaped vs random padding. *(may slip to extension)*
- [ ] **7. (stretch)** — Sonnet validation; more conditions.

### Open load-bearing decisions (user)
- [ ] Needle + question design (deterministically checkable).
- [ ] Structure-class construction parameters (tool-call/obs; research-doc).
- [ ] Operational definition of the "knee".
- [ ] Accuracy criterion (containment? normalized match?).
- [ ] Anti-patterns to inject for Exercise B.

### Gate
- [ ] `make check` green; predictions pre-registered; positions updated; retro + `/learn` + 3-reviewer pass.

### Budget
- [ ] Track all runs in `tasks/spend.md` (cap ~$50).
