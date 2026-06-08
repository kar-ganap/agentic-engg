"""Load a public-domain text corpus into filler sentences for clean_essay.

The clean_essay structure needs varied, neutral filler. We use Pride & Prejudice
(public domain; neutrality-verified — contains none of our needle terms, esp.
"meridian"). The raw text is committed under `data/corpus/`; the split logic
lives here (tested) so the filler is reproducible.
"""

from __future__ import annotations

import re
from pathlib import Path

DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[3] / "data" / "corpus" / "pride_and_prejudice.txt"
)


def split_sentences(text: str, min_chars: int = 30) -> list[str]:
    """Split prose into sentences.

    Normalizes whitespace (collapsing mid-sentence line breaks), splits on
    sentence-ending punctuation, and drops fragments shorter than `min_chars`
    (chapter headings, stray tokens) so filler units are clean sentences.
    """
    normalized = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [s.strip() for s in parts if len(s.strip()) >= min_chars]


def load_sentences(path: Path | None = None, min_chars: int = 30) -> list[str]:
    """Load the corpus file and return it split into filler sentences."""
    p = path or DEFAULT_CORPUS
    return split_sentences(p.read_text(encoding="utf-8"), min_chars=min_chars)
