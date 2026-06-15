"""#4-v2 — self-generated *semantic role-binding* interference (refund tier).

The agent computes a DISTINCT refund per item via `apply_adjustment` (the in-flight,
self-generated value — no tool exposes the base price, the bypass guard), then must route the
RIGHT amount to a referent named by a **paraphrase cue**. The cue is semantically-near but
**lexically-far** from its target (no shared word stems), so the cue→item step needs meaning,
not string-matching — the cousins/gifts shape. Distinct amounts make a mis-bind unambiguous.

The competitor `kind` is a **lexical × semantic 2×2** (deconfound — does the collapse track
*meaning* or *surface form*?):
  low / mid / high  — semantically far / mid / near to the target, all lex-far from the cue.
  lure              — semantically FAR from the target but LEX-near to the cue (shares a cue
                      stem). A model that lexical-matches the cue gets captured; a semantic one
                      resists. Where mis-binds land (semantic neighbor vs lure) is the mechanism
                      signature.
  mixed             — half semantic neighbors + half lures.

See .claude/plans/ (refund #4-v2) and docs/phases/phase-1.1-plan.md.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from stance.tooluse.domain import (
    Order,
    World,
    gen_account,
    gen_amount,
    gen_id,
    gen_transcript,
    gen_user,
)
from stance.tooluse.tasks.base import DependencyEdge, TaskInstance, Write

# --- stem-overlap checker (the cue-leak guard + the lure-construction validator) ----------
# A light stemmer + prefix-containment. NOT a real stemmer — a *review flag*: it catches the
# common inflectional leaks (trail/trails, run/running, race/racing) so a cue can't accidentally
# share surface form with its target, and so lures can be verified to share a cue stem.
_STOP = {
    "the", "a", "an", "and", "or", "for", "of", "to", "on", "in", "with", "at", "by", "from",
    "as", "pair", "set", "that", "this", "these", "those", "she", "he", "it", "you", "your",
    "they", "one", "two", "kit", "pack", "unit", "model", "item", "her", "his",
}


def _stem(word: str) -> str:
    for suf in ("ings", "ing", "ers", "er", "ed", "es", "s"):
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            word = word[: -len(suf)]
            break
    if len(word) >= 4 and word[-1] == word[-2] and word[-1] not in "aeiou":
        word = word[:-1]  # running -> runn -> run
    return word


def stems(text: str) -> set[str]:
    """Content-word stems of `text` (drops stopwords + <4-char words)."""
    return {_stem(w) for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP and len(w) >= 4}


def shared_stems(a: str, b: str) -> set[str]:
    """Stems shared between `a` and `b` (exact or ≥3-char prefix containment). Nonempty ⇒ a
    lexical overlap a cue must NOT have with its target (and a lure MUST have with its cue)."""
    sa, sb = stems(a), stems(b)
    hits: set[str] = set()
    for x in sa:
        for y in sb:
            if x == y or (len(x) >= 3 and len(y) >= 3 and (x.startswith(y) or y.startswith(x))):
                hits.add(x if len(x) <= len(y) else y)
    return hits


# =====================================================================================
# USER-OWNED (learning-first) — the load-bearing needle/competitor design. FIRST DRAFT,
# stem-validated by tests/test_tooluse_tasks.py::test_scenarios_are_stem_valid. Refine the
# cues/pools (and validate the semantic bins with embeddings); extend for larger N.
#   cue:    semantically-near, LEXICALLY-FAR from `target` (no shared stem).
#   high/mid/low: semantically near/mid/far to `target`, all LEX-FAR from the cue.
#   lure:   semantically FAR from `target`, LEX-NEAR to the cue (shares a cue stem) — the
#           lexical decoy; must NOT share a `target` stem (else it's a target match, not a lure).
# =====================================================================================
@dataclass(frozen=True)
class Scenario:
    target: str
    cue: str
    high: tuple[str, ...]
    mid: tuple[str, ...]
    low: tuple[str, ...]
    lure: tuple[str, ...]


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        target="trail-running shoes",
        cue="the pair for slick backcountry switchbacks",
        high=(
            "road-running shoes", "racing flats", "track spikes",
            "cross-training sneakers", "cushioned daily trainers", "stability running shoes",
        ),
        mid=(
            "hiking boots", "leather sandals", "dress loafers",
            "rubber rain boots", "insulated snow boots", "canvas slip-ons",
        ),
        low=(
            "kitchen blender", "desk lamp", "travel umbrella",
            "wireless headphones", "yoga mat", "steel water bottle",
        ),
        lure=(
            "backcountry camping stove", "switchback railway model", "slick vinyl record",
            "backcountry fishing rod", "switchback puzzle book", "slick hair pomade",
        ),
    ),
    Scenario(
        target="espresso machine",
        cue="the gadget for pulling morning shots",
        high=(
            "drip coffee maker", "french press", "pour-over kettle",
            "cold-brew tower", "stovetop moka pot", "capsule coffee maker",
        ),
        mid=(
            "countertop blender", "toaster oven", "stand mixer",
            "food processor", "electric kettle", "rice cooker",
        ),
        low=(
            "desk lamp", "travel umbrella", "leather wallet",
            "wireless headphones", "yoga mat", "paperback novel",
        ),
        lure=(
            "morning newspaper", "pull-up exercise bar", "shot-put ball",
            "morning alarm clock", "gadget repair toolkit", "morning glory seeds",
        ),
    ),
    Scenario(
        target="mountain bike",
        cue="the ride for rocky downhill descents",
        high=(
            "road bicycle", "gravel bike", "BMX bike",
            "electric commuter bike", "folding bike", "cyclocross bike",
        ),
        mid=(
            "skateboard", "sea kayak", "snowboard",
            "treadmill", "tennis racket", "climbing harness",
        ),
        low=(
            "kitchen blender", "desk lamp", "paperback novel",
            "travel umbrella", "wireless headphones", "yoga mat",
        ),
        lure=(
            "rocky road ice cream", "downhill ski wax", "descent mystery novel",
            "rocky shoreline painting", "downhill marathon medal", "rocky garden gnome",
        ),
    ),
)

_KINDS = ("low", "mid", "high", "lure", "mixed")


def gen_items(
    rng: random.Random, *, kind: str, n_items: int
) -> tuple[list[str], str, int, set[str]]:
    """USER-OWNED. Pick a scenario; return `(descriptions, cue, target_index, lure_descs)` —
    the target + `n_items-1` competitors of `kind` (mixed = half high + half lure)."""
    if kind not in _KINDS:
        raise ValueError(f"unknown kind: {kind!r}")
    scenario = rng.choice(SCENARIOS)
    n_comp = n_items - 1
    lure_descs: set[str] = set()
    if kind == "mixed":
        n_lex = n_comp // 2
        sem = rng.sample(scenario.high, n_comp - n_lex)
        lex = rng.sample(scenario.lure, n_lex)
        lure_descs = set(lex)
        comps = sem + lex
    else:
        pool = {"low": scenario.low, "mid": scenario.mid,
                "high": scenario.high, "lure": scenario.lure}[kind]
        comps = rng.sample(pool, n_comp)
        if kind == "lure":
            lure_descs = set(comps)
    items = [scenario.target, *comps]
    rng.shuffle(items)
    return items, scenario.cue, items.index(scenario.target), lure_descs


# =====================================================================================
# Harness scaffold (Claude) — stages the world + task around the USER-OWNED generator.
# =====================================================================================
def build_refund_task(
    *, seed: int, kind: str, n_items: int, fill_tokens: int
) -> tuple[World, TaskInstance]:
    rng = random.Random(seed)
    taken: set[str] = set()
    user = gen_user(rng, taken)
    taken.add(user.id)
    acct = gen_account(rng, taken, holder=user.name)
    taken.add(acct.id)

    descriptions, cue, target_index, lure_descs = gen_items(rng, kind=kind, n_items=n_items)

    items: list[tuple[Order, str]] = []  # (order, amount)
    order_lines: list[str] = []
    amounts_taken: set[str] = set()
    for desc in descriptions:
        base, disc, amount = gen_amount(rng, amounts_taken)
        amounts_taken.add(amount)
        oid = gen_id(rng, "O", taken)
        taken.add(oid)
        order = Order(
            id=oid, account_id=acct.id, days_ago=rng.randint(1, 30),
            base_price=base, discount=disc, description=desc,
        )
        items.append((order, amount))
        order_lines.append(f"- Order {oid}: {desc} (customer negotiated {int(disc * 100)}% off)")

    world = World(
        users={user.id: user}, accounts={acct.id: acct}, orders={o.id: o for o, _ in items}
    )
    target_order, target_amount = items[target_index]
    competitor_pool = [a for i, (_, a) in enumerate(items) if i != target_index]

    fill, _ = gen_transcript(rng, n_competitors=0, target_tokens=fill_tokens)
    prompt = (
        "You are handling a customer's returns. The customer negotiated a refund on each item "
        "below. Compute each refund with apply_adjustment (the base price is internal — only the "
        "tool knows it), then issue the ONE refund requested at the end.\n\n"
        + "\n".join(order_lines)
        + (f"\n\n{fill}" if fill else "")
        + f"\n\nNow issue the refund for {cue}."
    )

    bindings = {o.description: a for o, a in items}
    task = TaskInstance(
        prompt=prompt,
        expected_writes=[Write(action="issue_refund", args={"amount": target_amount})],
        ivs={"tier": "refund", "kind": kind, "n_items": n_items, "fill_tokens": fill_tokens},
        seed=seed,
        dependency_edge=DependencyEdge(
            consumer="issue_refund", needle_id=target_amount,
            needle_arg="amount", producer="apply_adjustment",
        ),
        competitor_pool=competitor_pool,
        notes={
            "target_order": target_order.id,
            "target_description": target_order.description,
            "cue": cue,
            "bindings": bindings,  # description ↔ amount, for post-hoc error analysis
            # amounts bound to LEXICAL lures → a mis-bind here = lexical capture (not semantic)
            "lure_amounts": [a for o, a in items if o.description in lure_descs],
        },
    )
    return world, task
