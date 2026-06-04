"""Context-rot haystack builder tests (Phase 1.0) — clean_essay structure.

Locks the construct-validity contract: needle present + unguessable; high vs.
low needle-question lexical similarity; neutral/localized/diffuse competition;
needle at depth; deterministic given seed; build-to-target length.
"""

from __future__ import annotations

import random
from typing import Any

import pytest

from stance.rot.haystack import (
    ANSWER_KEY,
    Haystack,
    _gen_competitor,
    _gen_neutral_op,
    build_haystack,
)

FILLER = [
    "The harbor was quiet that morning.",
    "She folded the map and tucked it away.",
    "Rain had washed the streets clean overnight.",
    "A gull circled the empty pier.",
    "The bakery opened its shutters at six.",
    "He counted the change twice before leaving.",
    "The train arrived four minutes late.",
    "Lanterns swayed in the harbor breeze.",
]


def _text(h: Haystack) -> str:
    parts: list[str] = []
    for m in h.messages:
        content = m["content"]
        if isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)


def _essay(**kw: Any) -> Haystack:
    defaults: dict[str, Any] = dict(
        structure="clean_essay",
        competition="neutral",
        similarity="high",
        target_tokens=2000,
        depth=0.5,
        seed=1,
        filler_sentences=FILLER,
    )
    defaults.update(kw)
    return build_haystack(**defaults)


def test_needle_present_and_answer_key() -> None:
    h = _essay()
    assert h.answer_key == ANSWER_KEY == "QX-7793-LK"
    assert "QX-7793-LK" in _text(h)


def test_high_similarity_question_reuses_needle_wording() -> None:
    h = _essay(similarity="high")
    assert "catalog number for the meridian manuscript" in h.question.lower()


def test_low_similarity_question_is_synonymized_but_specific() -> None:
    h = _essay(similarity="low")
    q = h.question.lower()
    assert "catalog number" not in q  # synonymized away
    assert "meridian" in q  # routing anchor retained


def test_neutral_has_no_competitors() -> None:
    assert _essay(competition="neutral").metadata["n_competitors"] == 0


def test_localized_injects_n_distractors() -> None:
    h = _essay(competition="localized", n_distractors=3)
    assert h.metadata["n_competitors"] == 3
    text = _text(h).lower()
    assert any(v in text for v in ("sentinel", "cobalt", "halcyon", "storage box"))


def test_diffuse_density_makes_many_competitors() -> None:
    h = _essay(competition="diffuse", diffuse_density=0.5, target_tokens=4000)
    assert h.metadata["n_competitors"] >= 3
    # competitors are catalog-domain; "manuscript" appears at least once per competitor
    assert _text(h).lower().count("manuscript") > h.metadata["n_competitors"]


def test_depth_controls_needle_position() -> None:
    early = _essay(depth=0.1).metadata["needle_position"]
    late = _essay(depth=0.9).metadata["needle_position"]
    assert early < late


def test_estimate_near_target() -> None:
    est = _essay(target_tokens=3000).metadata["est_tokens"]
    assert 3000 <= est <= 4500  # build up to target, modest overshoot


def test_deterministic_given_seed() -> None:
    assert _essay(seed=7).messages == _essay(seed=7).messages
    assert _essay(seed=7).messages != _essay(seed=8).messages


def test_essay_requires_filler() -> None:
    with pytest.raises(ValueError):
        build_haystack(
            structure="clean_essay",
            competition="neutral",
            similarity="high",
            target_tokens=1000,
            depth=0.5,
            seed=1,
            filler_sentences=None,
        )


# ---------------------------------------------------------------------------
# tool_call_stream structure (agentic; backlog item 3)
# ---------------------------------------------------------------------------


def _stream(**kw: Any) -> Haystack:
    defaults: dict[str, Any] = dict(
        structure="tool_call_stream",
        competition="neutral",
        similarity="high",
        target_tokens=1500,
        depth=0.5,
        seed=1,
    )
    defaults.update(kw)
    return build_haystack(**defaults)


def test_tool_stream_valid_pairing() -> None:
    msgs = _stream().messages
    assert msgs[0]["role"] == "user"  # initial task
    assert msgs[-1]["role"] == "user"  # final question
    # Interior alternates assistant(tool_use) / user(tool_result) with matching ids.
    i = 1
    while i < len(msgs) - 1:
        a, u = msgs[i], msgs[i + 1]
        assert a["role"] == "assistant" and a["content"][0]["type"] == "tool_use"
        assert u["role"] == "user" and u["content"][0]["type"] == "tool_result"
        assert u["content"][0]["tool_use_id"] == a["content"][0]["id"]
        i += 2


def test_tool_stream_needle_in_a_tool_result() -> None:
    h = _stream()
    found = any(
        isinstance(m["content"], list)
        and m["content"][0].get("type") == "tool_result"
        and "QX-7793-LK" in str(m["content"][0]["content"])
        for m in h.messages
    )
    assert found


def test_tool_stream_competition_counts() -> None:
    assert _stream(competition="neutral").metadata["n_competitors"] == 0
    assert _stream(competition="localized", n_distractors=2).metadata["n_competitors"] == 2
    diffuse = _stream(competition="diffuse", diffuse_density=0.5, target_tokens=3000)
    assert diffuse.metadata["n_competitors"] >= 2


def test_tool_stream_deterministic_and_estimate() -> None:
    assert _stream(seed=3).messages == _stream(seed=3).messages
    assert _stream(seed=3).messages != _stream(seed=4).messages
    est = _stream(target_tokens=2000).metadata["est_tokens"]
    assert 2000 <= est <= 3000


def test_competitor_variety_and_uniqueness() -> None:
    rng = random.Random(123)
    comps = [_gen_competitor(rng) for _ in range(200)]
    assert len(set(comps)) > 5  # varied phrasings (avoids §1.7 template-rut)
    assert any("Meridian" in c for c in comps)  # same-manuscript distractors present
    assert any("Meridian" not in c for c in comps)  # other-manuscript present
    # Uniqueness invariant: no competitor is a "catalog number ... Meridian"
    # (that would clash with the needle and break answer uniqueness).
    for c in comps:
        lc = c.lower()
        assert not ("catalog number" in lc and "meridian" in lc)


def test_neutral_op_variety() -> None:
    rng = random.Random(123)
    names = {_gen_neutral_op(rng)[0] for _ in range(100)}
    assert len(names) >= 5  # varied tool types, not a single repeated template


def test_research_doc_stream_not_yet_implemented() -> None:
    with pytest.raises(NotImplementedError):
        build_haystack(
            structure="research_doc_stream",
            competition="neutral",
            similarity="high",
            target_tokens=1000,
            depth=0.5,
            seed=1,
        )
