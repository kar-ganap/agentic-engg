# Phase 1.0 Extension — Cross-Provider Validation + Substrate Adoption (Retro)

**Closed:** 2026-06-10 (experimental work concluded 2026-06-05)
**Branch:** `phase-1.0-ext-deepseek`
**Critical phase boundary?** **No** — the cross-family attempt was *inconclusive* and committed **no new position** (§1.8 held + caveated; §3.8 abstention note caveated). The substrate adoption (§0.19) is a methodology choice carrying its own trigger statement, to be stress-tested in practice and reviewed at the **Phase 1.1 close** (where the real position commitments #4/#6/#3 land). → **three-reviewer pass deferred to Phase 1.1.**

> Scope note: this branch also carries **Phase 1.1 prep** (the 40% mis-attribution fix, `c0f8e8d`) and the **Phase 1.1 plan** (`fad256c`/`0d1787b`/`19723eb`). Those belong to Phase 1.1, not this extension; they ride along on the branch and are documented under Phase 1.1.

## Summary

"Migration-as-validation": replicate the §1.8 headline on a **non-Anthropic family (DeepSeek)** to (1) discharge §1.8's open retraction **clause (b)** (cross-family), (2) counter Anthropic selection bias (§0.8), (3) stand up DeepSeek as the cheap workhorse.

- **Built** (reused the DI seams — no harness rewrite): DeepSeek provider wiring via the **Anthropic-compatible endpoint** (`secrets.deepseek_api_key`/`has_deepseek_key`, pricing rows `deepseek-v4-flash`/`-pro`, `run.py --provider`), counting tokens on **Anthropic-Haiku** for a consistent cross-provider x-axis. Step-0 endpoint gate passed.
- **Outcome: INCONCLUSIVE for clause (b)** — two genuine walls + a more important finding:
  - `tool_call_stream` on DeepSeek **confounded by the DSML tool-call leak** (the §0.11 no-tools fix is Anthropic-specific); diffuse → **abstention**, not collapse.
  - `clean_essay` (provider-neutral) on Haiku: **the neutral control broke** (low-sim folio-wrinkle wrecks the control on prose).
  - **Finding:** the diffuse-collapse is entangled with **structure × needle-question-similarity** → it does not replicate straightforwardly across providers/structures with the current needle. **Clause (b) remains OPEN and harder than anticipated** (needs a structure-invariant needle). See `experiments/phase-1.0/results-cross-family.md`.
- **Substrate decision:** **DeepSeek-primary / Claude-anchor** (§0.19; CLAUDE.md Code Rule) — cost (years-horizon affordability) + cross-provider validity by construction.

## Decisions made

| Decision | Choice | Why |
|---|---|---|
| Cross-family endpoint | **Anthropic-compatible** (`api.deepseek.com/anthropic`) | reuse the pipeline byte-identical → no format-translation confound |
| Token x-axis | count on **Anthropic-Haiku** even for DeepSeek runs | one consistent tokenizer across providers |
| §1.8 disposition | **hold at 78 + generality caveat** | within-regime result stands (don't demote); generalization unproven (don't raise); clause (b) open |
| §3.8 | record DeepSeek **abstention** as a 3rd failure mode, caveated | cross-family confound — characterizes, doesn't advance §3.8 |
| Substrate | **DeepSeek-primary / Claude-anchor** | ~7–18× cheaper + cross-provider; Claude-only-feature experiments carved out |
| Three-reviewer pass | **deferred to Phase 1.1 close** | no new position committed; substrate is methodology w/ trigger |

## Validation gate

| Gate | Status |
|---|---|
| Tests / `make check` | green |
| Reproducibility | numbers regenerate from committed code + pinned seeds/prices; `results-cross-family.md`; spend logged |
| Pre-registration | the attempt tested §1.8's pre-existing retraction **clause (b)** |
| Retro written | this file |
| `/learn` written | `tasks/lessons.md` — extension entry (§0.17/0.18/0.19 filed; structured entry appended) |
| Three-reviewer pass | **N/A — deferred to Phase 1.1** (rationale above) |

## Concept-stream output (synthesis-anchored)

- **§1.8 — held 78 + generality caveat.** The diffuse collapse is established in the `tool_call_stream` × low-sim regime; **cross-structure / cross-provider generality is NOT established** and is entangled with needle design. Clause (b) open and harder (structure-invariant needle needed). *Honest non-confirmation, not a demotion.*
- **§3.8 — third failure mode added (caveated).** DeepSeek-flash under diffuse degrades by **abstention** (empty / tool-call-retreat) — distinct from Haiku-confabulate and Sonnet-refuse-with-text. Recorded with the cross-family confound; does not on its own advance §3.8 (stays 45).
- **§3.6 — cross-provider row: inconclusive** (structure×similarity entanglement).

## Throughline property progress

- **No throughline *surface* advanced** — expected at Stage 1 (surfaces begin in Stage 2). Flagged per the gate; not a concern this stage.
- **Property 3 (re-evaluation) exercised in spirit:** the extension re-evaluated §1.8/§3.8 against cross-family evidence and recorded an honest "held-with-caveat / inconclusive" rather than drifting — the anti-drift discipline working.
- **Property 4 (contribution):** the substrate decision improves cross-provider grounding (feeds future contribution); the structure×similarity entanglement is a candidate methodological caveat.

## Carry-forward

- **Clause (b) deferred** — needs a structure-invariant needle (mid-similarity; control holds on both prose and tool-stream). A mid-similarity probe (~$3) is the cheap first step.
- **Substrate re-validated per new experiment type** (§0.16/0.17) — first such validation is the Phase 1.1 declared-tools + prefill smoke tests.
