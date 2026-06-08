"""One-time generator for the realism-check competitor pool (Phase 1.0, §3.6).

Calls the LLM ONCE to produce natural-prose archive competitor lines (choice B:
the model owns names + codes), applies a COLLISION FILTER, and writes a PINNED
JSON artifact. The committed JSON is canonical: the run reads it and samples
deterministically (seeded), so the experiment regenerates even though an LLM was
used once. Re-running regenerates (non-deterministic) — commit deliberately.

Collision filter (preserves answer uniqueness):
  - drop any line containing the answer code QX-7793-LK;
  - drop any line that pairs "Meridian" with "catalog" (would create a SECOND
    Meridian catalog number → ambiguity). Meridian + non-catalog attributes
    (box/shelf/page/donor) are allowed — those are legitimate same-item distractors.

    uv run python experiments/phase-1.0/gen_competitor_pool.py          # dry-run
    uv run python experiments/phase-1.0/gen_competitor_pool.py --go      # generate
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from stance.secrets import anthropic_api_key

REPO = Path(__file__).resolve().parents[2]
POOL_DIR = REPO / "data" / "competitor_pools"
ANSWER_KEY = "QX-7793-LK"
MODEL = "claude-haiku-4-5-20251001"
N_REQUEST = 120

# v2 (2026-06-05): role-CONSTRAINED to hold relatedness ~ templated. v1 was too
# loose — the LLM produced only ~15% catalog-number-asserting lines (rest were
# code-as-ID / other attributes), so it inadvertently LOWERED relatedness and the
# collapse vanished (a realism×relatedness confound). v2 fixes the roles so only
# *phrasing* varies → a clean construct-validity (templating-artifact) test.
PROMPT = (
    f"Generate filler lines for an archive-catalog retrieval test. Produce {N_REQUEST} "
    "short sentences. Vary the WORDING and sentence structure HEAVILY, but every line "
    "must be in EXACTLY one of these two roles:\n"
    "- [about 75% of lines] State the CATALOG NUMBER of a specific named manuscript "
    "OTHER than 'Meridian'. The line must make clear the code IS that manuscript's "
    "catalog number (e.g. \"The Halcyon manuscript's catalog number is AB-1234-CD\", "
    "\"Halcyon is cataloged as AB-1234-CD\", \"Catalog no. AB-1234-CD — the Halcyon "
    "manuscript\"). Invent diverse manuscript names; use varied codes shaped AB-1234-CD. "
    "Do NOT present the code as the manuscript's name/title/ID — it is specifically the "
    "CATALOG NUMBER.\n"
    "- [about 25% of lines] State a NON-catalog attribute (storage box number, "
    "shelf/aisle, page count, or donor) of the 'Meridian' manuscript.\n\n"
    "HARD CONSTRAINTS:\n"
    "1. NEVER state a catalog number for the 'Meridian' manuscript.\n"
    f"2. NEVER use the exact code {ANSWER_KEY}.\n"
    "Output ONE sentence per line. No numbering, no headers, no commentary."
)


def _collision(line: str) -> bool:
    """True if the line would break answer uniqueness (drop it)."""
    low = line.lower()
    if ANSWER_KEY.lower() in low:
        return True
    return "meridian" in low and "catalog" in low  # 2nd Meridian catalog# / ambiguity


def _text(resp: Any) -> str:
    parts: list[str] = []
    for b in resp.content:
        if getattr(b, "type", None) == "text":
            parts.append(getattr(b, "text", "") or "")
    return "".join(parts)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default="v2", help="pool version → realism_<version>.json")
    p.add_argument("--go", action="store_true", help="call the LLM and write the pool")
    args = p.parse_args()
    out = POOL_DIR / f"realism_{args.version}.json"
    if not args.go:
        print(f"dry-run — pass --go to call {MODEL} and write {out}\n\nPROMPT:\n{PROMPT}")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=anthropic_api_key())
    resp = client.messages.create(
        model=MODEL, max_tokens=4000, messages=[{"role": "user", "content": PROMPT}]
    )
    raw = [ln.strip(" -\t•") for ln in _text(resp).splitlines() if ln.strip()]
    kept = [ln for ln in raw if not _collision(ln)]
    dropped = len(raw) - len(kept)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "provenance": {
                    "version": args.version,
                    "model": MODEL,
                    "date": date.today().isoformat(),
                    "n_requested": N_REQUEST,
                    "n_raw": len(raw),
                    "n_dropped_collision": dropped,
                    "n_kept": len(kept),
                    "answer_key_excluded": ANSWER_KEY,
                    "prompt": PROMPT,  # self-documenting: how this pool was generated
                    "note": "PINNED artifact; the run samples this deterministically (seeded).",
                },
                "competitors": kept,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"raw={len(raw)} dropped(collision)={dropped} kept={len(kept)} -> {out}")
    for ln in kept[:8]:
        print("  ", ln)


if __name__ == "__main__":
    main()
