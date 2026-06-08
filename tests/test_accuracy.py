"""Deterministic needle-match accuracy tests (Phase 1.0).

Contract for the context-rot accuracy checker: normalized substring
containment of an unguessable answer key. No LLM judge (the deterministic-
verifier slice; full eval harness is Phase 2.1).
"""

from __future__ import annotations

import pytest

from stance.eval.accuracy import accuracy, is_hit, normalize


def test_normalize_strips_case_and_punctuation() -> None:
    assert normalize("QX-7793-LK") == "qx7793lk"
    assert normalize("qx 7793 lk!") == "qx7793lk"
    assert normalize("  Hello, World.  ") == "helloworld"
    assert normalize("") == ""


def test_is_hit_true_for_formatting_variants() -> None:
    key = "QX-7793-LK"
    assert is_hit("The code is QX-7793-LK.", key)
    assert is_hit("the code is qx7793lk", key)
    assert is_hit("Answer: qx 7793 lk", key)


def test_is_hit_false_when_absent_or_off_by_one() -> None:
    key = "QX-7793-LK"
    assert not is_hit("I don't know the code.", key)
    assert not is_hit("The code is QX-7793-LM.", key)  # one char off
    assert not is_hit("", key)


def test_empty_answer_key_raises() -> None:
    # Guards the "" -in- anything == True degenerate case; an empty needle is a
    # design error that would spuriously match every response.
    with pytest.raises(ValueError):
        is_hit("anything", "")
    with pytest.raises(ValueError):
        is_hit("anything", "  !!  ")  # normalizes to empty


def test_accuracy_averages_hits() -> None:
    key = "QX-7793-LK"
    responses = ["QX-7793-LK", "nope", "qx7793lk", "wrong"]
    assert accuracy(responses, key) == 0.5


def test_accuracy_empty_responses_raises() -> None:
    with pytest.raises(ValueError):
        accuracy([], "QX-7793-LK")
