"""Deterministic needle-match accuracy for the context-rot study (Phase 1.0).

Normalized substring containment of an unguessable answer key. Deterministic,
no LLM judge, no API cost — the deterministic-verifier slice (Module 6 /
§0.8 preference). The full eval harness (rubric / judge / trajectory) lands in
Phase 2.1; this is only the slice the context-rot curve needs.

The accuracy *criterion* (normalized containment, unguessable needle so base
rate ≈ 0) is a load-bearing design decision; the matching mechanics here
implement it.
"""

from __future__ import annotations

from collections.abc import Sequence


def normalize(text: str) -> str:
    """Lowercase and keep only alphanumeric characters.

    Collapses formatting differences (case, punctuation, spacing) so that
    'QX-7793-LK', 'qx7793lk', and 'qx 7793 lk' all compare equal.
    """
    return "".join(c for c in text.lower() if c.isalnum())


def is_hit(response: str, answer_key: str) -> bool:
    """True iff the normalized answer key is contained in the normalized response.

    Raises:
        ValueError: answer_key normalizes to empty — an empty needle is a design
            error that would spuriously match every response.
    """
    key = normalize(answer_key)
    if not key:
        raise ValueError("answer_key normalizes to empty; needle must be non-trivial")
    return key in normalize(response)


def accuracy(responses: Sequence[str], answer_key: str) -> float:
    """Fraction of responses that contain the answer key.

    Raises:
        ValueError: responses is empty — accuracy is undefined over zero trials.
    """
    if not responses:
        raise ValueError("responses is empty; accuracy is undefined over zero trials")
    hits = sum(is_hit(r, answer_key) for r in responses)
    return hits / len(responses)
