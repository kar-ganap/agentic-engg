"""Position-staleness scheduler (Phase 2.1, throughline Property 3 — re-evaluation cadence).

Ranks positions by review-worthiness so the tool can surface the position that needs revisiting
*before* a decision is made against it. The staleness FUNCTION is a load-bearing design decision
(user-designed 2026-07-28): a **status-dependent review interval**, amplified **multiplicatively**
by unincorporated signal — new evidence-flux since the last update, open decisive-probes, and
confidence volatility. **Retraction-proximity is surfaced as a HUMAN-facing flag** (the position's
pre-registered triggers), NOT folded into the numeric score — the judgment stays human.

Pure over `stance.graph`; `today` is passed in (no hidden clock) so it is testable/reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from stance.graph.models import Position
from stance.graph.store import Graph

# --- the staleness function (user-designed shape; the weights below are the tunable knobs) ---
REVIEW_INTERVAL_DAYS: dict[str, int] = {"hypothesis": 30, "candidate": 90, "active": 180}
# 'demoted' (or any status not listed) never resurfaces — overdue := 0.
W_FLUX = 0.5   # per new (unincorporated) evidence/support recorded since the position's last update
W_PROBE = 0.5  # per open decisive-probe (uncollected data that would move the position)
W_VOL = 0.3    # recent confidence swing (range of the last 3 records / 100)


@dataclass(frozen=True)
class StalenessScore:
    """A position's review-worthiness + a transparent breakdown of why (and the human checklist)."""

    position_id: str
    title: str
    status: str
    confidence: int
    staleness: float
    # breakdown (transparency — every score is auditable):
    age_days: int
    overdue: float
    flux: int
    open_probes: int
    volatility: float
    retraction_flags: tuple[str, ...]  # the pre-registered triggers, for the human to judge


def _age_days(p: Position, today: date) -> int:
    return (today - date.fromisoformat(p.updated)).days


def _flux(p: Position, g: Graph) -> int:
    """New evidence/support bearing on p, recorded AFTER p's last update (undated = baseline)."""
    cutoff = date.fromisoformat(p.updated)
    n = 0
    for s in g.supports_for(p.id):
        d = s.date or (g.evidence[s.evidence_id].date if s.evidence_id in g.evidence else "")
        if d and date.fromisoformat(d) > cutoff:
            n += 1
    return n


def _open_probes(p: Position, g: Graph) -> int:
    return len(g.probes_for(p.id))


def _volatility(p: Position, g: Graph) -> float:
    confs = [h.confidence for h in g.position_history(p.id)][-3:]
    return (max(confs) - min(confs)) / 100 if len(confs) >= 2 else 0.0


def staleness(p: Position, g: Graph, today: date) -> StalenessScore:
    """staleness = overdue(status-interval) × (1 + w_flux·flux + w_probe·probes + w_vol·vol)."""
    age = _age_days(p, today)
    interval = REVIEW_INTERVAL_DAYS.get(p.status)
    overdue = age / interval if interval is not None else 0.0  # demoted → never resurface
    flux, probes, vol = _flux(p, g), _open_probes(p, g), _volatility(p, g)
    score = overdue * (1 + W_FLUX * flux + W_PROBE * probes + W_VOL * vol)
    return StalenessScore(
        position_id=p.id, title=p.title, status=p.status, confidence=p.confidence,
        staleness=score, age_days=age, overdue=overdue, flux=flux, open_probes=probes,
        volatility=vol, retraction_flags=tuple(r.condition for r in p.retraction),
    )


def rank(g: Graph, today: date) -> list[StalenessScore]:
    """All current positions, most review-worthy first."""
    return sorted((staleness(p, g, today) for p in g.positions.values()),
                  key=lambda s: s.staleness, reverse=True)
