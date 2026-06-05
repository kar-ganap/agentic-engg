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
OUT = REPO / "data" / "competitor_pools" / "realism_v1.json"
ANSWER_KEY = "QX-7793-LK"
MODEL = "claude-haiku-4-5-20251001"
N_REQUEST = 120

PROMPT = (
    "Generate filler lines for an archive-catalog retrieval test. Produce "
    f"{N_REQUEST} short, natural, VARIED sentences, each stating ONE bibliographic "
    "fact about a manuscript in an archive. Mix these kinds:\n"
    "- catalog numbers for manuscripts OTHER than 'Meridian' (invent diverse "
    "manuscript names; use varied codes shaped like AB-1234-CD)\n"
    "- non-catalog attributes (storage box number, shelf/aisle, page count, donor) "
    "for various manuscripts, which MAY include 'Meridian' for these non-catalog "
    "attributes ONLY\n\n"
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
    p.add_argument("--go", action="store_true", help="call the LLM and write the pool")
    args = p.parse_args()
    if not args.go:
        print(f"dry-run — pass --go to call {MODEL} and write {OUT}\n\nPROMPT:\n{PROMPT}")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=anthropic_api_key())
    resp = client.messages.create(
        model=MODEL, max_tokens=4000, messages=[{"role": "user", "content": PROMPT}]
    )
    raw = [ln.strip(" -\t•") for ln in _text(resp).splitlines() if ln.strip()]
    kept = [ln for ln in raw if not _collision(ln)]
    dropped = len(raw) - len(kept)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "provenance": {
                    "model": MODEL,
                    "date": date.today().isoformat(),
                    "n_requested": N_REQUEST,
                    "n_raw": len(raw),
                    "n_dropped_collision": dropped,
                    "n_kept": len(kept),
                    "answer_key_excluded": ANSWER_KEY,
                    "note": "PINNED artifact; the run samples this deterministically (seeded).",
                },
                "competitors": kept,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"raw={len(raw)} dropped(collision)={dropped} kept={len(kept)} -> {OUT}")
    for ln in kept[:8]:
        print("  ", ln)


if __name__ == "__main__":
    main()
