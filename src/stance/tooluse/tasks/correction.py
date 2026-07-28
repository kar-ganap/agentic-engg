"""Correction-tier task builder (§1.2 BEHAVIORAL supervision test, Phase 1.2 Thread C).

Tests §1.2's *actual stated claim* — failures as behavioral supervision (the agent adapts its
ACTIONS from the failure, Reflexion-style) — with a **task-success** DV, not payload survival. The
isolating structure defeats every self-rescue channel:

  1. FORMAT CHECK — the agent submits a test record with a raw code → INVALID teaches the RULE
     (dash after the first 3 chars); the test record is NOT resubmitted (no success to re-teach it).
  2. AUDIT — a distractor chain (`check_shipment`) fills context past the budget → compaction drops
     the early failure.
  3. SUBMIT — the agent submits the real records R2/R3; under ephemeral reasoning the rule survives
     ONLY if the failure was preserved.

DV = do the LATE submits apply the rule on first try (task-success). `preserve` keeps it →
success; `summarize` drops it → the agent submits the raw (unformatted) code → INVALID. Reuses
`make_correction_tools`. See docs/phases/phase-1.2-plan.md § Thread C.
"""

from __future__ import annotations

import random

from stance.tooluse.domain import World, gen_id
from stance.tooluse.tasks.base import TaskInstance, Write
from stance.tooluse.tasks.compaction import _LOG_LINES
from stance.tooluse.tools import correct_code

_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_DIGITS = "0123456789"


def _raw_code(rng: random.Random) -> str:
    """A 7-char raw code (3 letters + 4 digits) — correct form inserts a dash after char 3."""
    return ("".join(rng.choice(_LETTERS) for _ in range(3))
            + "".join(rng.choice(_DIGITS) for _ in range(4)))


def _ship_body(rng: random.Random, oid: str, n_lines: int = 5) -> str:
    """A moderate (~90-token) OK shipment log — pure distractor filler (no rule, no ref)."""
    lines = [f"Audit log for order {oid}: shipped normally, no exceptions."]
    lines.extend(rng.choice(_LOG_LINES) for _ in range(n_lines))
    return " ".join(lines)


def build_correction_task(
    *, seed: int, n_distractor: int = 7, n_measured: int = 2
) -> tuple[World, TaskInstance]:
    """Stage a format-check probe (`R1-TEST`) + `n_measured` real records (R2, R3, …) + an
    `n_distractor`-order audit that compacts the probe failure before the real submits."""
    rng = random.Random(seed)
    taken: set[str] = set()

    records: dict[str, str] = {"R1-TEST": _raw_code(rng)}
    measured_ids = [f"R{i + 2}" for i in range(n_measured)]
    for rid in measured_ids:
        records[rid] = _raw_code(rng)

    chain: list[str] = []
    for _ in range(n_distractor):
        oid = gen_id(rng, "O", taken)
        taken.add(oid)
        chain.append(oid)
    chain_bodies = {oid: _ship_body(rng, oid) for oid in chain}

    prompt = (
        "Complete these steps IN ORDER.\n"
        f"1. FORMAT CHECK: call submit_record(record_id='R1-TEST', code='{records['R1-TEST']}'). "
        "Read the feedback — it gives the required code format. Do NOT resubmit R1-TEST.\n"
        f"2. AUDIT: from {chain[0]}, call check_shipment on each order (each result names "
        "the next) until you reach the last order.\n"
        "3. SUBMIT the two real records, each code formatted as required: "
        + ", ".join(f"record_id='{rid}' raw code '{records[rid]}'" for rid in measured_ids) + "."
    )
    task = TaskInstance(
        prompt=prompt,
        expected_writes=[
            Write("submit_record", {"record_id": rid, "code": correct_code(records[rid])}, 1)
            for rid in measured_ids
        ],
        ivs={"tier": "correction", "n_distractor": n_distractor, "n_measured": n_measured},
        seed=seed,
        notes={"records": records, "chain": chain, "chain_bodies": chain_bodies,
               "measured_ids": measured_ids,
               "true_codes": {rid: correct_code(records[rid]) for rid in measured_ids}},
    )
    return World(), task
