"""Compaction-tier task builder (§1.2, Phase 1.2 Thread B) — failure-preservation under a squeeze.

A **breadcrumb-chain audit**: the agent walks a chain of orders via `check_shipment` (each result
names the next order → sequential by construction, so the model can't batch and context accumulates
for the mid-loop compaction trigger). ~1-in-3 orders are BLOCKED; a blocked check is a LARGE
`is_error` transcript (~500 tokens of shipment log) with a **release ref buried inside** that the
final `file_report` needs. The ref lives ONLY in that failure content — and the transcript is too
large to echo wholesale — so summarizing the failure away genuinely loses it (flavor-2 §1.2:
the failure carries forward-info, not just "don't-repeat"). Reuses `make_compaction_tools`.

Two IVs map the §1.2 boundary:
  - `anticipated`: True → prompt announces the ref requirement upfront (agent extracts refs into its
    own tokens → they survive compaction); False → revealed only by the terminal check (agent had no
    reason to extract → refs survive only if the failure result is preserved).
  - result SIZE is now LARGE by construction (the regime that actually needs compaction — a 40-token
    result the model can trivially carry forward was the earlier design flaw).

Primary DV = **ref-recall**: fraction of true refs the agent submits to `file_report` (runner-side,
mechanical, no judge). See docs/phases/phase-1.2-plan.md § Thread B.
"""

from __future__ import annotations

import random

from stance.tooluse.domain import World, gen_id
from stance.tooluse.tasks.base import TaskInstance, Write

_REASONS = ("address unverified", "payment review", "customs hold", "weight mismatch",
            "fraud screen", "restricted item")

# Filler shipment-log lines — realistic clutter so a BLOCKED transcript is large enough that the
# model can't echo it wholesale, and the buried ref isn't obviously salient at read time.
_LOG_LINES = (
    "Carrier scan recorded at the regional sortation hub; parcel weight re-measured in tolerance.",
    "Customs pre-clearance document queued for manual review by the destination broker.",
    "Automated address validation returned a soft match; flagged for secondary confirmation.",
    "Handling unit consolidated onto a mixed pallet; conveyor routing updated for the dock.",
    "Linehaul departure delayed pending trailer capacity; rebooked on the next scheduled lane.",
    "Hazmat screening cleared; segregation label reapplied per the destination country ruleset.",
    "Proof-of-delivery signature template attached to the manifest for the final-mile partner.",
    "Dimensional re-scan triggered a rate reclass; billing adjustment noted for reconciliation.",
    "Exception queue entry opened by the hub operator; awaiting upstream document resubmission.",
    "Cold-chain sensor telemetry nominal; last checkpoint within the contracted temperature band.",
    "Recipient contact attempt logged by the local branch; callback window scheduled.",
    "Insurance declared-value flag set; higher-tier handling applied through the transfer point.",
)


def _verbose_body(rng: random.Random, oid: str, reason: str, ref: str, n_lines: int = 22) -> str:
    """A ~500-token shipment-log transcript for a BLOCKED order with the release ref buried
    mid-transcript (not flagged as salient) so it survives only if the failure result is kept."""
    lines = [f"BLOCKED: shipment audit log for order {oid} (hold reason: {reason})."]
    body = [rng.choice(_LOG_LINES) for _ in range(n_lines)]
    ref_line = f"Release authorization on file — quote ref {ref} to clear this hold at closeout."
    body.insert(rng.randint(n_lines // 3, 2 * n_lines // 3), ref_line)  # buried in the middle
    lines.extend(body)
    return " ".join(lines)


def build_compaction_task(
    *, seed: int, n_orders: int = 9, n_blocked: int = 3, anticipated: bool = True
) -> tuple[World, TaskInstance]:
    """Stage a chain of `n_orders` orders; block `n_blocked` of them (never the first — a clean
    start), each returning a large transcript with a distinct release `ref` buried inside."""
    rng = random.Random(seed)
    taken: set[str] = set()
    chain: list[str] = []
    for _ in range(n_orders):
        oid = gen_id(rng, "O", taken)
        taken.add(oid)
        chain.append(oid)

    blocked_ids = sorted(rng.sample(chain[1:], n_blocked), key=chain.index)
    blocked: dict[str, tuple[str, str]] = {}  # oid -> (ref, large is_error body)
    true_refs: list[str] = []
    for oid in blocked_ids:
        ref = gen_id(rng, "R", taken)
        taken.add(ref)
        reason = rng.choice(_REASONS)
        blocked[oid] = (ref, _verbose_body(rng, oid, reason, ref))
        true_refs.append(ref)

    if anticipated:  # ref requirement announced upfront → agent pre-extracts
        prompt = (
            f"Audit this customer's order shipments, starting with {chain[0]}. Call check_shipment "
            "on each order; every result names the next order to check. Some orders are BLOCKED "
            "and their log has a release ref — collect every ref you see. When you reach the last "
            "order, call file_report with ALL the refs you collected."
        )
    else:  # requirement revealed only by the final check → agent had no reason to record refs
        prompt = (
            f"Audit this customer's order shipments, starting with {chain[0]}. Call check_shipment "
            "on each order and follow the chain — every result names the next order to check — "
            "until you reach the end."
        )
    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write("file_report", {}, cardinality=1)],  # filed once; recall in runner
        ivs={"tier": "compaction", "n_orders": n_orders, "n_blocked": n_blocked,
             "anticipated": anticipated},
        seed=seed,
        notes={"chain": chain, "blocked": blocked, "true_refs": true_refs},
    )
    return World(), task  # tools close over chain/blocked (task.notes), not the world
