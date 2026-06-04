"""Corpus loader tests (Phase 1.0) — sentence splitting for clean_essay filler."""

from __future__ import annotations

from stance.rot.corpus import load_sentences, split_sentences


def test_split_sentences_basic() -> None:
    text = "Hello there, friend. This is a longer test sentence! Is it working well?"
    sents = split_sentences(text, min_chars=5)
    assert "Hello there, friend." in sents
    assert any(s.endswith("!") for s in sents)
    assert any(s.endswith("?") for s in sents)


def test_split_collapses_newlines() -> None:
    text = "This sentence spans\nacross two lines of text. And here is another one."
    sents = split_sentences(text, min_chars=5)
    assert all("\n" not in s for s in sents)
    assert any("spans across two lines" in s for s in sents)


def test_split_filters_short_fragments() -> None:
    text = "OK. This sentence is definitely long enough to be retained as filler."
    sents = split_sentences(text, min_chars=20)
    assert "OK." not in sents  # too short → dropped
    assert any("long enough" in s for s in sents)


def test_load_corpus_real() -> None:
    sents = load_sentences()  # the committed Pride & Prejudice corpus
    assert len(sents) > 1000  # thousands of sentences
    assert all(len(s) >= 30 for s in sents)
    assert all("\n" not in s for s in sents)
