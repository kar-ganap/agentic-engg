"""Thread-B sampler tests (Phase 2.0): Pool + Graph -> materialized Task."""

from __future__ import annotations

import pytest

from stance.graph.models import Evidence
from stance.graph.store import Graph
from stance.reasoning.pool import Distractor, Pool
from stance.reasoning.sampler import _expand, build_task


def _graph() -> Graph:
    g = Graph()
    g.evidence["ev-t1"] = Evidence("ev-t1", "experimental", "exp/1", "target claim 1", "direct")
    g.evidence["ev-t2"] = Evidence("ev-t2", "literature", "p/2", "target claim 2", "corroborating")
    return g


def _pool() -> Pool:
    return Pool(
        id="test",
        debate="does X drive Y?",
        correct_position="yes, X drives Y",
        target_ids=("ev-t1", "ev-t2"),
        distractors=(
            Distractor("h1", "ax1", "high", "synthetic", "hi-1"),
            Distractor("h2", "ax2", "high", "synthetic", "hi-2"),
            Distractor("h3", "ax3", "high", "synthetic", "hi-3"),
            Distractor("m1", "axb", "mid", "synthetic", "mid-1"),
        ),
    )


def test_targets_always_included() -> None:
    t = build_task(_pool(), _graph(), n_distractors=2, confusability="high", seed=1)
    targets = [e for e in t.evidence if e.kind == "target"]
    assert {e.ref for e in targets} == {"ev-t1", "ev-t2"}
    assert {e.text for e in targets} == {"target claim 1", "target claim 2"}  # resolved from graph
    assert len(t.evidence) == 4  # 2 targets + 2 distractors


def test_distractors_from_requested_tier_only() -> None:
    t = build_task(_pool(), _graph(), n_distractors=3, confusability="high", seed=1)
    d = [e for e in t.evidence if e.kind == "distractor"]
    assert len(d) == 3
    assert all(e.ref.startswith("h") for e in d)  # never the mid-tier m1


def test_mid_tier_selectable() -> None:
    t = build_task(_pool(), _graph(), n_distractors=1, confusability="mid", seed=1)
    d = [e for e in t.evidence if e.kind == "distractor"]
    assert [e.ref for e in d] == ["m1"]


def test_zero_distractors_is_targets_only() -> None:
    t = build_task(_pool(), _graph(), n_distractors=0, confusability="high", seed=1)
    assert all(e.kind == "target" for e in t.evidence)
    assert len(t.evidence) == 2


def test_deterministic_by_seed() -> None:
    a = build_task(_pool(), _graph(), n_distractors=2, confusability="high", seed=7)
    b = build_task(_pool(), _graph(), n_distractors=2, confusability="high", seed=7)
    assert a == b  # same seed -> byte-identical task (selection AND shuffle order)


def test_oversize_raises_pointing_at_multiplier() -> None:
    with pytest.raises(ValueError, match="multiplier"):  # only 3 high singletons -> 3 variants
        build_task(_pool(), _graph(), n_distractors=5, confusability="high", seed=1)


# ---- the multiplier: slotted templates -> similar-but-distinct variants ----
def test_expand_singleton_is_identity() -> None:
    single = Distractor("s", "ax", "high", "synthetic", "plain text")
    assert _expand(single) == [single]


def test_expand_slotted_template_to_variants() -> None:
    tmpl = Distractor(
        "t", "ax", "high", "synthetic", "in {size} inputs, the {region} recovers worse",
        slots={"size": ("50k", "200k"), "region": ("middle", "tail")},
    )
    vs = _expand(tmpl)
    assert len(vs) == 4  # 2 x 2 combinations
    assert {v.id for v in vs} == {"t#0", "t#1", "t#2", "t#3"}  # unique ids
    texts = {v.text for v in vs}
    assert "in 50k inputs, the middle recovers worse" in texts
    assert "in 200k inputs, the tail recovers worse" in texts
    assert all(v.axis == "ax" and v.confusability == "high" for v in vs)  # inherits axis/tier


def test_build_task_reaches_large_n_via_multiplier() -> None:
    # ONE authored template, 6 combos -> can sample 5 distractors (impossible pre-multiplier)
    pool = Pool(
        "p", "d?", "yes", ("ev-t1",),
        (Distractor("t", "ax", "high", "synthetic", "{a}/{b}",
                    slots={"a": ("1", "2", "3"), "b": ("x", "y")}),),
    )
    t = build_task(pool, _graph(), n_distractors=5, confusability="high", seed=1)
    d = [e for e in t.evidence if e.kind == "distractor"]
    assert len(d) == 5
    assert len({e.ref for e in d}) == 5  # 5 distinct variants of the one template


def test_missing_target_raises() -> None:
    bad = Pool("p", "d?", "yes", ("ev-nope",), ())
    with pytest.raises(KeyError, match="ev-nope"):
        build_task(bad, _graph(), n_distractors=0, confusability="high", seed=1)
