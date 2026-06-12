# Phase 1.1 — #4 chain sweep (results)

> Does the §1.8 diffuse-competition collapse reproduce when the haystack is the
> agent's **own** tool returns? **Outcome: a clean NULL on DeepSeek-v4-flash — but
> INCONCLUSIVE for #4**, because the competitors weren't same-frame *rivals* for the
> needle's slot (only same-format presence), and agentic self-production likely
> immunizes. Run 2026-06-12; numbers regenerate from `run.py` + `score.py`.

## Setup

`build_chain_task` (get_order **produces** the needle `account_id` early → agent
reviews competitor-laden tickets by ticket_id → `send_message` **consumes** the
needle late). 11 cells (anchor + fill/depth/position/competition one-factor sweeps)
× 5 seeds = **55 runs**, DeepSeek-v4-flash, arm A, **$0.77** (exact from usage).
Cells in `run_config.py`; raw in `runs/phase-1.1/` (gitignored, regenerable).

## Headline: 55/55 correct-use

| sweep | cells | critical_outcome | success |
|---|---|---|---|
| fill {low, mid(anchor), high} | 3 | **all correct-use** | 15/15 |
| depth {2,4,8,12} (fill-low) | 4 | **all correct-use** | 20/20 |
| position {0.1,0.5,0.9} (fill-mid) | 3 | **all correct-use** | 15/15 |
| competition {none,few,many} (fill-mid) | 3 | **all correct-use** | 15/15 |

**0 mis-bind, 0 fabricate, 0 re-fetch, 0 redundant calls — every cell, every seed.**
(The scorer is not stuck on "correct-use": the 2026-06-12 e2e smoke produced `error`
when the agent declined to send, and the unit tests exercise mis-bind/fabricate. So
the null is real, not a classifier artifact.)

## The manipulation BIT (verified — this is not a "task didn't bite" null)

Per-cell achieved (from `summaries.jsonl`):
- **fill-high:** `fill_at_use ≈ 186k` tokens — the needle was genuinely buried under
  ~132–186k of context at the send. **competitors_surfaced = 8** (all present in the
  pool). **redundant_call_count = 0** → the agent recalled the needle from memory, it
  did **not** re-fetch.
- A high-fill trajectory (`chain-fill-d8-high-p0.9-many-s1`): `get_order(O-7066)→A-7763`
  (t0) → reviews 8 tickets surfacing 8 competitor account-ids `A-9074…A-7505` (ctx→132k,
  t2) → `send_message(A-7763)` correctly (t3, ctx=132k). It recalled its own fetched
  value under heavy, competitor-laden burial.

So the volume and competitor *presence* were real; the agent retrieved correctly anyway.

## Interpretation — INCONCLUSIVE for #4 (a §1.8-clause-(b)-style outcome)

The §1.8 diffuse-rot does **not** appear here. Three confounded explanations, in
order of how much they likely matter:

1. **Agentic self-production + structured findability (leading).** The needle is the
   agent's **own labeled `get_order` result** ("the account I looked up for this
   order") — structurally findable, unlike §1.8's anonymous needle sentence in prose.
   This is exactly the **agentic-vs-passive** distinction we reframed #4 around: the
   proactive-interference / WM-limit literature (arXiv:2506.08184) finds the collapse
   in a **passive** key-value setting; here the value is **actively fetched + held**,
   which may immunize.
2. **Competitor framing weaker than §1.8 (real limitation).** Our competitors are
   *passing ticket mentions* ("account A-9074 had a similar issue") — same-*format* but
   not same-*frame* **rivals** for "the holder of order O." §1.8's competitors were
   same-frame claims ("catalog number for [other] manuscript"). So there's little
   genuine **discrimination pressure** — competitor *presence* ≠ competitor *rivalry*.
3. **Capability (least likely).** v4-flash could just be robust — but the WM literature
   shows current models (incl. DeepSeek-V3) **do** degrade in the passive setting, so
   the difference is more plausibly active-vs-passive than raw capability (§0.8).

(1) and (2) are entangled, so this is **inconclusive, not a refutation** — the same
shape as §1.8's open clause (b): the cross-setting generalization is **harder than
anticipated** and needs a better stimulus.

## Disposition

- **#4 stays at its prior (60) — neither confirmed nor refuted.** No mis-binding was
  observed, but the design didn't create same-frame rivalry, and agentic findability
  confounds. Do **not** update confidence on this run.
- **Contribution candidate (promising):** *agentic self-fetched values resist the
  diffuse rot that collapses passive retrieval* — the agentic-vs-passive angle. Logged
  to `tasks/contribution-candidates.md`; needs the stronger test below before any claim.

## What would make it conclusive (deferred)

1. **Same-frame rivals.** Competitors that are plausible answers to "the holder of
   order O" — e.g., several `order → account` mappings the agent must disambiguate, so
   the needle competes for its slot (a needle/competitor redesign; the §0.18 sweet-spot
   on *rivalry*, not just format).
2. **Active-vs-passive A/B.** Run the *same* needle/competitors **passively** (dumped
   in a transcript, not agent-fetched) vs. actively — to isolate explanation (1).
3. **Claude spot-anchor** (§0.8) — confirm the null isn't v4-flash-specific.

## Process lesson (→ tasks/lessons.md)

- **§0.20 (proposed):** *competitor PRESENCE ≠ competitor RIVALRY.* The manipulation
  bit on volume (186k fill-at-use) and presence (8 in pool), yet induced no
  mis-binding because the competitors weren't same-frame alternatives for the needle's
  slot. For a retrieval-collapse effect you must verify the stimulus creates genuine
  **discrimination pressure** (plausible rival answers), not just volume + same-format
  noise. (Generalizes §0.18 from the static-haystack case to agentic tasks.)

## Cost (logged in `tasks/spend.md`)

#4 chain sweep $0.773 (55 runs) + depth pilot $0.016. Exact from `response.usage`.
