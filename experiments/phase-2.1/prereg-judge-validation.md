# Pre-registration — Judge-validation for §1.9 (Phase 2.1, B2)

**Registered:** 2026-07-28, before any human label is entered. Discharges (or not) §1.9's grader
caveat. Module 6 (LLM-as-judge validation).

## Question
§1.9 (`reasoning-pattern`, candidate 63: *no universal best reasoning pattern; effectiveness = bias
× epistemic-structure*) is stuck at candidate because its DV is the fuzzy 5-criterion LLM judge
(`reasoning.grader`), never validated against a human. Is the judge a trustworthy instrument **for
§1.9's use** — i.e., does it rank reasoning quality the way a human does?

## Design
- **Blind human labels** (the author) on a **stratified N=15** sample of Phase-2.0 graded positions
  (spread across `grade_total` 0–20). Each item shows the **exact context the judge saw** — debate,
  labeled target/distractor evidence, correct-position key, the position — minus the judge's scores.
- Human scores the **same 5-criterion rubric** the judge used (0–4 each). Blindness on the honor
  system (`judge-validation-key-DONT-OPEN.json` withheld until scoring is done).
- **Metrics:** quadratic-weighted Cohen's κ per criterion (penalizes big disagreements more than
  adjacent) + **Spearman rank-correlation on `grade_total`** — the latter matches §1.9's DV (arm
  comparison by total; per-criterion noise and any constant judge offset wash out in the ranking).

## Pre-registered promotion rule
**§1.9 candidate 63 → active iff: Spearman(`grade_total`) ≥ 0.70 AND every criterion qw-κ ≥ 0.40.**

- Spearman ≥ 0.70 = the judge orders overall reasoning quality like the human (the §1.9-relevant
  agreement).
- κ ≥ 0.40 floor on *every* criterion = guard against **compensating errors** (a high total
  correlation produced by canceling per-criterion biases).

## Falsifier / retraction
- **Rule fails → §1.9 stays candidate.** The grader caveat stands: the judge is not validated as a
  §1.9 instrument. Next step = sharpen the rubric anchors, or gather more/independent labels, or
  switch §1.9 to a less judge-dependent DV — not promote.

## Caveats bounding the claim (honest scope)
- **Single labeler** → this is judge↔*author* agreement, not judge↔consensus. A pass means "the
  judge agrees with the author's rubric application," not "matches human consensus."
- **N=15** → the Spearman/κ confidence intervals are wide; treat a pass as *encouraging* and a clear
  fail as *informative*, neither as proof.
- **Circularity** → the author designed the rubric and labels against it; blind scoring + a
  stratified sample (incl. low-scorers) partially mitigate, but shared rubric-understanding inflates
  agreement. If §1.9 promotes, the promotion is flagged for the phase-close three-reviewer pass.
