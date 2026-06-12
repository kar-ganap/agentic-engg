"""Customer-support domain substrate for Phase 1.1 (Module 2, tool use).

Deterministic, offline (NO API). Provides the materials the tools read and the
task builders stage:

- `gen_id`: collision-filtered, same-format ids (uniqueness is load-bearing for
  needle/competitor disambiguation — plan req #2; reuses the Phase 1.0 `_gen_code`
  discipline of never colliding with a reserved/taken set).
- frozen entity types (`User`, `Account`, `Order`, `Ticket`).
- seeded generators for each.
- `gen_transcript`: a large, messy support-conversation string embedding a chosen
  number of competitor ids — the fill + diffuse-competitor source for the #4 chain.
- `World`: a simple data container the tools look up against.

The per-task DATA STAGING (which call returns the needle, competitor density per
cell) is the task builders' job (see plan § Generator); this module is just the
substrate. See docs/phases/phase-1.1-plan.md § "Loop & generator design".
"""

from __future__ import annotations

import random
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field

_DIGITS = "0123456789"


def _est_tokens(text: str) -> int:
    """Cheap char/4 token estimate (API-free), matching the rot harness."""
    return len(text) // 4


def gen_id(rng: random.Random, prefix: str, taken: Collection[str] = ()) -> str:
    """A `{prefix}-DDDD` id not present in `taken` (collision-filtered).

    Single-char prefixes by convention (`U`/`A`/`O`/`T`), so ids are 6 chars.
    """
    while True:
        code = f"{prefix}-{''.join(rng.choice(_DIGITS) for _ in range(4))}"
        if code not in taken:
            return code


# --- entities -------------------------------------------------------------
@dataclass(frozen=True)
class User:
    id: str
    name: str


@dataclass(frozen=True)
class Account:
    id: str
    holder: str  # the holder's display name


@dataclass(frozen=True)
class Order:
    id: str
    account_id: str
    days_ago: int

    @property
    def eligible(self) -> bool:
        """Return-window eligibility — the derived attribute #4 tasks check."""
        return self.days_ago <= 30


@dataclass(frozen=True)
class Ticket:
    id: str
    account_id: str
    subject: str
    transcript: str
    embedded_ids: tuple[str, ...] = ()  # competitor ids the task builder staged in `transcript`


# --- generators -----------------------------------------------------------
_FIRST = [
    "Jane", "John", "Mei", "Omar", "Priya", "Carlos", "Aisha", "Liam",
    "Sofia", "Noah", "Yuki", "Fatima", "Diego", "Hana", "Sam", "Lena",
]
_LAST = [
    "Doe", "Smith", "Park", "Khan", "Lopez", "Chen", "Ali", "Novak",
    "Rossi", "Haddad", "Singh", "Müller", "Okafor", "Tanaka", "Reyes",
]
_SUBJECTS = [
    "Damaged item on arrival", "Refund status", "Wrong item shipped",
    "Billing discrepancy", "Late delivery", "Account access issue",
]


def gen_user(rng: random.Random, taken: Collection[str] = ()) -> User:
    return User(id=gen_id(rng, "U", taken), name=f"{rng.choice(_FIRST)} {rng.choice(_LAST)}")


def gen_account(rng: random.Random, taken: Collection[str], holder: str) -> Account:
    return Account(id=gen_id(rng, "A", taken), holder=holder)


def gen_order(
    rng: random.Random, taken: Collection[str], account_id: str, days_ago: int | None = None
) -> Order:
    """`days_ago` defaults to a random 1–90; pass it to control return-eligibility
    (≤30 = eligible) — tasks that presume a refund must stage an *eligible* order."""
    return Order(
        id=gen_id(rng, "O", taken),
        account_id=account_id,
        days_ago=days_ago if days_ago is not None else rng.randint(1, 90),
    )


def gen_ticket(
    rng: random.Random,
    taken: Collection[str],
    account_id: str,
    transcript: str,
    embedded_ids: Sequence[str] = (),
) -> Ticket:
    return Ticket(
        id=gen_id(rng, "T", taken),
        account_id=account_id,
        subject=rng.choice(_SUBJECTS),
        transcript=transcript,
        embedded_ids=tuple(embedded_ids),
    )


# --- transcript (fill + diffuse competitors) ------------------------------
_COMPETITOR_TEMPLATES = [
    "Agent: I see a note on account {cid} about a similar issue.",
    "Customer: My colleague's account {cid} had the same problem last week.",
    "System: cross-reference — account {cid} flagged for follow-up.",
    "Agent: For comparison, account {cid} was resolved the same way.",
    "Note: merged context from account {cid} during the prior shift.",
]
_NEUTRAL_LINES = [
    "Customer: Thanks for your patience.",
    "Agent: Let me pull up your details.",
    "Agent: Is there anything else I can help with today?",
    "Customer: No, that's all for now.",
    "Agent: Your ticket has been updated and noted.",
    "Customer: Could you double-check the shipping address?",
    "Agent: I've escalated this to the fulfilment team.",
    "Customer: Appreciate the quick response.",
    "Agent: One moment while I confirm the policy.",
    "System: conversation auto-saved.",
]


def gen_transcript(
    rng: random.Random,
    *,
    n_competitors: int,
    target_tokens: int,
    pool: Sequence[str] | None = None,
    taken: Collection[str] = (),
) -> tuple[str, list[str]]:
    """A support-conversation string of ~`target_tokens`, embedding `n_competitors`
    unique competitor account-ids (the diffuse competitors).

    Returns `(text, competitor_ids)` — the ids are guaranteed to appear in `text`,
    so a later rendered-id check is exact. `pool` (if given) supplies competitor
    line templates with a `{cid}` placeholder — the realism hook (plan §0.13).
    `taken` lets the caller reserve ids (e.g. the needle + prior competitors) so the
    generated competitors never collide with them — uniqueness is load-bearing (#2).
    """
    templates = list(pool) if pool else _COMPETITOR_TEMPLATES
    comp_ids: list[str] = []
    seen: set[str] = set(taken)
    for _ in range(n_competitors):
        cid = gen_id(rng, "A", seen)
        seen.add(cid)
        comp_ids.append(cid)

    lines: list[str] = [rng.choice(templates).format(cid=cid) for cid in comp_ids]
    while _est_tokens("\n".join(lines)) < target_tokens:
        lines.append(rng.choice(_NEUTRAL_LINES))
    rng.shuffle(lines)
    return "\n".join(lines), comp_ids


# --- world ----------------------------------------------------------------
@dataclass
class World:
    """A container of generated entities + the lookups the tools wrap."""

    users: dict[str, User] = field(default_factory=dict)
    accounts: dict[str, Account] = field(default_factory=dict)
    orders: dict[str, Order] = field(default_factory=dict)
    tickets: dict[str, Ticket] = field(default_factory=dict)

    def get_account(self, account_id: str) -> Account | None:
        return self.accounts.get(account_id)

    def orders_for(self, account_id: str) -> list[Order]:
        return [o for o in self.orders.values() if o.account_id == account_id]

    def tickets_for(self, account_id: str) -> list[Ticket]:
        return [t for t in self.tickets.values() if t.account_id == account_id]

    def search_users(self, query: str) -> list[User]:
        q = query.lower()
        return [u for u in self.users.values() if q in u.name.lower()]


def build_world(
    rng: random.Random, *, n_accounts: int, orders_per_account: int
) -> World:
    """Build a small seeded world with globally-unique ids across all entities."""
    taken: set[str] = set()
    world = World()
    for _ in range(n_accounts):
        u = gen_user(rng, taken)
        taken.add(u.id)
        world.users[u.id] = u
        a = gen_account(rng, taken, holder=u.name)
        taken.add(a.id)
        world.accounts[a.id] = a
        for _ in range(orders_per_account):
            o = gen_order(rng, taken, account_id=a.id)
            taken.add(o.id)
            world.orders[o.id] = o
        text, _ = gen_transcript(rng, n_competitors=0, target_tokens=400)
        t = gen_ticket(rng, taken, account_id=a.id, transcript=text)
        taken.add(t.id)
        world.tickets[t.id] = t
    return world
