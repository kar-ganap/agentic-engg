# Phase 1.1 #4-v2 — Self-generated interference: five designs, one structural conclusion

> The #4 "self-inflicted context rot" investigation, re-instrumented after the chain null.
> **Outcome: #4(i) does not manifest across four high-discriminability agentic designs; a fifth
> (low-discriminability) design *does* induce a collapse — but it is the §1.8 identification
> failure, occurring identically active vs passive. So #4 ⊆ §1.8: agentic self-generation gives
> the needle an accessibility advantage §1.8's collapse regime lacks, and is neither cause nor
> cure.** Written 2026-06-13 (diffuse design + banking 2026-06-14). Numbers regenerate from
> `runs/phase-1.1/{binding,refund,recency,rolebind,diffuse}/*summaries.jsonl` + the committed runners.

---

## 0. The question, and why it took four designs

**#4(i) (prior 60):** *in a multi-step agentic trajectory, competition among the agent's own
self-generated values degrades retrieval* — "self-inflicted context rot." The fix-lever #4(ii)
(prior 50): return-shape beats description-quality at depth.

Two earlier results forced the re-instrumentation:
- **#4 v1 (chain sweep):** 55/55 correct-use — a clean **null**, but **inconclusive**: the
  competitors were present-but-not-rivals (§0.20 presence ≠ rivalry). It moved volume + presence,
  not genuine discrimination pressure.
- **Prior art (arXiv:2506.08184):** the bare "many items collapse retrieval" effect is *already
  documented* (log-linear in # tracked items, error = retrieve an interfering value,
  length-independent, on DeepSeek-V3 among others). So #4 cannot claim that effect. Its defensible
  novelty narrows to: **agentic & self-generated** interference + the **return-shape lever** +
  **cross-provider**.

**Method — corner the effect by removing "rescue mechanisms."** Each design strips one reason the
agent might trivially succeed, to force the interference to manifest (or prove it doesn't):

| # | design | rescue it removes | hardest cell | result |
|---|---|---|---|---|
| 1 | exact-key binding | — (baseline) | 100 rivals @ 953k | **held** (15/15) |
| 2 | semantic role-binding (1-phase) | exact-match; lexical shortcut | high overlap, N=6 | **held** (5/5) |
| 3 | recency (proactive interference) | exact-match (cue by recency) | N=40 self-gen totals | **held** (5/5) |
| 4 | rolebind (2-phase, large-N) | small-N, recency, lexical, **+ burial** | N=16 confusable, **37k buried** | **held** (5/5) |
| 5 | diffuse (low-disc cue) | **discriminability** (the §1.8 condition) | weak cue + same-type lures | **collapses** (lure-capture, active = passive) |

All on DeepSeek **v4-flash** (the cheap workhorse; weak → should collapse *earlier* than frontier,
making the holds more striking). Designs 1–4 (high-discriminability) produced **zero mis-binds**;
design 5 (low-discriminability) produced the **only** mis-binds — lure-captures, identical active
vs passive (§6b) → **#4 ⊆ §1.8**.

---

## 1. Design 1 — exact-key binding (active vs passive)

**Task.** The agent must `send_message(account_id=…)` to the holder of a target order. The needle
(the account id) is reached either by **fetching** it (`get_order` → account, *active*) or it is
**dumped** in a directory of N same-format rivals in the prompt (*passive*). Rivals exist in the
world so a mis-bind is a valid-but-wrong send. Ramp: N rivals × fill, to **953k tokens**.

**Result** (`binding/high_summaries.jsonl`, passive, n_rivals=100):

| fill (peak tokens) | 125k | 250k | 499k | 747k | **953k** |
|---|---|---|---|---|---|
| correct-use | 3/3 | 3/3 | 3/3 | 3/3 | **3/3** |

Active matched it. **0 mis-binds at 953k with 100 same-frame rivals.**

**What it taught.** The needle is an **exact, unique string**; retrieving it is exact-substring
match, which attention does position-invariantly. There is **no signal-to-noise gradient** for
§1.8's diffuse-competition collapse to act on. → **Rescue #1 = exact-key.** (This also bounded
§1.8: it is a claim about *prose/semantic* retrieval, not structured exact-key lookup.)

---

## 2. Design 2 — semantic role-binding, single-phase (refund tier)

**The idea.** Remove the exact key: identify the target by a **semantic paraphrase cue** among
**confusable** items, with **lexically-distinct** values (so a mis-bind is unambiguous routing,
not a transcription slip). The cousins/gifts shape — N legitimate (item→amount) bindings; the
*referents* blur; the failure is crossed wires.

**Build.** `Order` gained `base_price`/`discount`/`description`; `gen_amount` (collision-filtered
distinct refunds). `make_refund_tools`: `apply_adjustment` (computes the in-flight refund —
**bypass guard**: no tool exposes the base price, so the amount is obtainable only by computing
it), `list_adjustments` (the measured re-fetch), `issue_refund` (write-boundary). The **scorer**
needed two changes: (a) **numeric normalization** so `52` / `52.0` / `$52.00` all match the
needle, and (b) a **needle-surfacer** re-fetch definition (counting calls that surface the
*needle*, not all producer calls — otherwise N per-item `apply_adjustment` calls misread
correct-use as re-fetch). Both stash-proofed.

**The lexical × semantic deconfound (a necessary control).** A "semantic" collapse must be shown
*not* to be mere lexical surface-matching. The first-draft cues **leaked** — each shared a word
stem with its target (`off-road trails` ↔ `trail-running`), so the agent could keyword-match. The
**stem-checker** (`shared_stems`) caught this. The redesign added: no-leak cues (semantically
near, lexically far), and a **lexical lure** competitor type (shares a *cue* stem, semantically
unrelated) — if the agent grabs a lure, it's lexical-shortcutting; if it resists, it's semantic.

**Result** (`refund/pilot_…_summaries.jsonl`, no-leak cues, fill 8k):

| cell | result |
|---|---|
| low overlap (distinct, N=3) | 5/5 correct |
| high overlap (confusable, **N=6**) | 5/5 correct (4 from memory, 1 re-fetch) |
| lure (lexical decoys, N=6) | 3 correct, **0 mis-bind**, 2 abstain |

**What it taught.** Cues fixed (low-overlap holds → solvable; lure not captured → *not* naively
lexical). But the positive control **still didn't fire**: depth=7 traces show the agent computes
all 6 then recalls 1-of-6 **from memory** — trivial. The prior art's collapse needs N in the
*tens*; 6 is far below it. → **Rescue #2 = small-N recall** (and Rescue #3, lexical shortcut,
closed by the no-leak cues). The curated confusable pool caps N at ~6, which is the wall here.

---

## 3. Design 3 — recency / proactive interference

**The idea.** Scale N **for free** — the interfering items are *successive values of one slot*
(a running total revised N times), so N is a `range(N)` knob, not authored content. Needle = the
**final** total; competitors = the agent's own stale totals.

**Build.** `make_recency_tools`: a **stateful** `apply_adjustment` (each call advances a per-order
cursor and returns the next running total), and **no current-value query** (bypass guard — the
agent must track the latest from its own returns). Secondary modifier `semantic_similar`: blurry
reasons (loyalty/member/rewards discount…) vs distinct ones.

**Harness bug found (worth banking).** The first run **loop-guarded every cell** at the 2nd call:
the loop-guard flags repeated identical *(tool, args)* signatures as a loop, but a stateful
`apply_adjustment(order_id="O-1")` is called N times with **identical args** *by design*. The
guard assumes **idempotent tools**; stateful tools violate it. Fix: `loop_guard=False` for this
tier. (→ relevant to the #7 loop-guard tier's assumptions.)

**Result** (`recency/pilot_…`, fill 0):

| cell | result |
|---|---|
| N=5 | 5/5 correct |
| **N=40** (distinct reasons) | **5/5 correct, 0 mis-bind** |
| **N=40** (similar reasons) | **5/5 correct, 0 mis-bind** |

**What it taught.** depth=41 (40 applies + issue), `peak_fill≈4k`, **no re-fetch**: the agent used
the **most-recent** tool result. The needle is *structurally* the last turn, so message-recency
rescues it — and **no amount of N or fill can change that** (the target is always the last thing
generated). → **Rescue #4 = message-recency.** A somewhat-expected null, but it cleanly eliminated
the "scale N" path and validated the instrument (post loop-guard fix).

---

## 4. Design 4 — rolebind: two-phase, large-N (the decisive one)

**The idea.** Remove **all** rescues simultaneously. The cue is by **referent** (not "the latest"
→ kills recency) over a **confusable** pool with a **no-leak** cue (kills lexical), at **large N**
(kills small-N recall), in **two phases** so the cue can't be shortcut and the target is computed
mid-sequence:

> STEP 1 — compute the refund for **all** N items (`apply_adjustment` per order). STEP 2 — only
> after all N are computed does a **gated** `get_refund_request` reveal *which* to issue.

So the agent computes all N *before knowing the target* → it can't special-case it; the target was
computed somewhere mid-sequence → not most-recent. Then `issue_refund(amount)`. Pool = confusable
houseplants (16), each with a distinctive no-leak cue ("the elegant bloomer grown in bark chips" →
moth orchid). Then we **buried** the prompt under fill up to 37k.

**Result** (`rolebind/{pilot,fill}_…`):

| cell | peak tokens | result |
|---|---|---|
| low overlap (distinct), N=16 | 2k | 5/5 correct |
| high overlap, N=6 | 1k | 5/5 correct |
| high overlap, **N=16** | 2k | **5/5 correct** |
| high overlap, N=16, fill mid | 9k | 5/5 correct |
| high overlap, N=16, **fill high** | **37k** | **5/5 correct** |

**What it taught.** depth=18 (16 applies + `get_refund_request` + issue), the gate forced all 16
first, and it issued **from memory — no `list_adjustments`**: among 16 confusable houseplants
buried under 37k, it mapped the no-leak cue to the right plant and recalled *that* plant's
self-generated amount. The decisive design — *every* easy-out removed — still **held**.

**The residual easy-out (the key observation).** At fill=0 the context is tiny (16 short results,
~few k) — everything's visible. And crucially, **prompt-fill buries the cue→item directory, not
the amounts**: the amounts are the agent's *recent tool results*, which arrive *after* the prompt,
so they're never buried. This is what sent us to the dead-ends below.

---

## 5. Two diagnostic dead-ends (why we stopped adding stress)

We considered two obvious "stress it harder" axes and ruled both out **on the logic**, not by
spending:

- **More burial (370k–740k fill).** Burial only pressures the **passive sub-component** — the
  cue→item→order directory living in the *prompt*. The **amounts are self-generated recent tool
  results**, structurally unburiable by prompt-fill. So a collapse at 740k would be the agent
  failing to find the cued item in a buried wall = the **§1.8 length effect we already
  characterized** (v4-flash held neutral retrieval to ~94k, noisy past), *not* #4 interference.

- **Longer self-generation.** Self-generated values are **compact tool results that stay recent
  and scannable**; more of them doesn't bury the target (you'd need infeasibly many, or huge
  per-result blobs). It re-reduces to §1.8/length on self-generated content — which needs the
  diffuse regime to collapse anyway.

Both fail for the **same reason**: they can't remove the needle's accessibility advantage.

---

## 6. The structural explanation (why everything held)

Every design gave the needle an **accessibility advantage** that §1.8's collapse regime
specifically *lacks*:

| design | the needle's advantage |
|---|---|
| binding | exact-key (uniquely, position-invariantly matchable) |
| recency | the most-recent turn |
| role-binding | a distinctive cue + a compact, fully-visible context |
| rolebind (buried) | the amount is a **fresh self-generated tool result**, not in the buried wall |

§1.8 collapses only when the needle sits in a **diffuse wall with no such advantage** (low
cue-similarity + many similar competitors). **Agentic self-generation *inherently* confers the
advantage** — the value arrives fresh / labeled / recent. Therefore:

> **"Agentic self-fetch resists rot" is largely a structural near-tautology:** *fetching the needle
> replaces wall-retrieval with a fresh result, which sidesteps §1.8 rather than refuting it.* The
> only non-tautological residual is §1.8 **relocated to fetch-time** (can the agent identify *what*
> to fetch under a diffuse cue — which is the same diffuse-retrieval problem).

## 6b. Design 5 — the diffuse low-disc test (RUN): #4 ⊆ §1.8, illustrated

We then *built and ran* the missing condition: a **low-discriminability** cue (the §1.8 collapse
condition) over same-type competitors, **active vs passive** (`tasks/diffuse.py`,
`run_diffuse.py`, `diffuse/*summaries.jsonl`). It produced the **only mis-binds of the entire
arc** — and they were clean **lure-captures**:

> cue = *"the long-lasting indoor flower most often given as a gift"*; the agent issued the
> **peace lily's** refund (a same-type surface-lure) instead of the **moth orchid's** (the target)
> — surface-pull beating meaning, the textbook §1.8 failure.

Decisively, it occurred **identically in active and passive** (same scenario, same seed: low-active
*and* low-passive both mis-bound to the lure). The collapse is in **identification** (cue→item),
which self-generation **neither caused nor cured** → **#4 ⊆ §1.8, demonstrated**, not just argued.
The high-disc control held (`high-active`/`high-passive` = 0 mis-binds) → the cue is solvable; the
collapse is real (§0.18 gate passed).

**But a clean *rate* is precluded by a gradeable/luring tradeoff on this substrate.** A
strengthening pass with sharper *two-attribute* cues (target matches both, lures match the surface
attribute only) **over-corrected to 0/48**: the distinguishing attribute makes the cue *high-disc*
→ no lure. Meanwhile the vaguer luring cues have *fuzzy* answers (peace-lily-as-a-gift isn't
clearly wrong). So: **gradeable ⇒ no lure; luring ⇒ ungradeable** — there is no clean window for
v4-flash on fuzzy-semantic cues. The magnitude is sweet-spot-dependent and not cleanly quantifiable
here — §1.8's known sweet-spot difficulty (`results-cross-family.md`, §0.18), reconfirmed. A hard
number would require porting §1.8's *own* unique-answer needle (clear answer + low-sim question +
same-type distractors) into the agentic frame — a separate build.

So the immunity question resolves as anticipated: the collapse, when induced, is the §1.8
identification failure and is **provenance-blind** (active = passive). "Agentic self-fetch resists
rot" remains a structural near-tautology (fetching ≠ wall-retrieval); the residual is §1.8 at
fetch-time, and §1.8 itself is what fires when the cue goes low-disc.

---

## 7. Disposition

**Positions**
- **#4(i) — demote 60 → 25 (author-set, 2026-06-14).** "Self-inflicted context rot in
  self-generated trajectories" did **not** manifest across four high-disc designs; and when a
  collapse *was* induced (Design 5, low-disc) it was the **§1.8 identification failure**, occurring
  **identically active vs passive** — so #4(i) is **not a separate effect: #4 ⊆ §1.8.** The
  pre-registered retraction (correct-use flat w.r.t. competition/fill) was met four times; the
  residual 25 covers "rot can occur in agentic trajectories" (which is just §1.8 applying). Not a
  novel mechanism.
- **#4(ii) — park (untestable here).** The return-shape fix-lever can only be measured *once a
  collapse exists to fix*. The only collapse (Design 5) was an **identification** failure (cue→item
  lure-capture) — not a return-*shape* problem, so the lever has nothing to act on. Revive only
  with a design whose collapse is in value-rendering, not identification.

**Contribution candidate** — reframe **"agentic self-fetch resists diffuse rot" (novel effect)** →
**"agentic self-generation confers a structural accessibility advantage (fresh / recent /
uniquely-labeled) that sidesteps §1.8's wall-retrieval collapse."** Honest, defensible, but
*not* a novel separate mechanism — so a *weaker* contribution than originally hoped. (The
genuinely-novel agentic question is better posed later as **RAG-vs-grep** — tool-retrieval vs
in-context — than as "immunity.")

**Harness insights (bank)**
- **Loop-guard assumes idempotent tools** — stateful tools (identical args, different results)
  trip it; guard must be off (or signature-aware) for such tiers. → #7 loop-guard tier.
- **The stem-checker** (`shared_stems`) — a reusable cue-leak guard *and* lure-construction
  validator; it caught two real leaks (`shoe`/`shot`, `string`/`strands`) before they ran.
- **Numeric-amount scorer** (`_norm_value`/`_extract_type`) + the **needle-surfacer** re-fetch
  definition — both now general.

**Process lessons (→ `tasks/lessons.md`)**
- **The rescue-progression as a method:** corner an effect by removing one escape per design;
  when the *n*-th design still holds, the *reason it holds* is the finding. Here four removals
  converged on a single structural cause.
- **Self-generated needles carry an accessibility advantage by construction** — to test agentic
  interference you must **remove** it (diffuse regime), not **add** length or burial. Length/burial
  pressure the passive sub-components, never the self-generated needle.
- Reinforces §0.20 (presence ≠ rivalry) and §0.21 (validate the control at full seed-count).

---

## 8. Cost & reproduce

#4-v2 arc spend (DeepSeek v4-flash, exact from `summaries`): refund pilots ~$0.15 + recency
~$0.02 + rolebind pilot $0.044 + rolebind fill $0.524 + diffuse (pilot $0.016 + full $0.039) ≈
**$0.80**. (Design-1 binding was logged earlier, ~$1.49.) Project total ≈ **$74 / $100**. Logged
in `tasks/spend.md`.

```bash
# each tier is a self-contained runner (safe-by-default; --go to execute)
uv run python experiments/phase-1.1/run_binding.py  --ramp high --regimes passive --go   # design 1
uv run python experiments/phase-1.1/run_refund.py   --grid pilot --go                    # design 2
uv run python experiments/phase-1.1/run_recency.py  --grid pilot --go                    # design 3
uv run python experiments/phase-1.1/run_rolebind.py --grid pilot --go                    # design 4
uv run python experiments/phase-1.1/run_rolebind.py --grid fill  --go                    # design 4 (burial)
uv run python experiments/phase-1.1/run_diffuse.py  --grid full --n-seeds 12 --go        # design 5 (§1.8 low-disc)
```

## 9. Open / future

- **A hard collapse *rate*** — Design 5 *demonstrated* the §1.8 collapse agentically (lure-capture,
  active = passive) but couldn't *quantify* it (the gradeable/luring tradeoff, §6b). Getting a rate
  needs porting §1.8's own unique-answer needle (clear answer + low-sim question + same-type
  distractors) into the agentic frame — gradeable *and* luring — likely as part of the
  **RAG-vs-grep** debate (a later module), framed as tool-retrieval vs in-context disambiguation.
- The five tiers (binding/refund/recency/rolebind/diffuse) are reusable substrate; the confusable
  pools + no-leak cues are stem-validated and extensible for larger N or a capability ladder.
