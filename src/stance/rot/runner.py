"""Context-rot evaluator (Phase 1.0) — the re-pointable sweep engine (§0.7).

For a given condition (structure x competition x similarity x model), builds a
haystack for every (length x depth x seed) cell, calls the model, scores with the
deterministic needle-match, and appends one JSONL record per run. `complete_fn`
and `count_fn` are dependency-injected (like loop.py) → unit-testable offline;
the real Anthropic client is wired only in experiments/phase-1.0/. The EXACT
count_tokens value is recorded as the x-value (the builder's estimate only hits
the target).
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from stance.eval.accuracy import is_hit
from stance.rot.haystack import build_haystack

# Forces a concise, scoreable answer — without it, verbose/cautious models bury or
# withhold the needle and a binary substring scorer mis-reads formatting as
# retrieval failure (lessons §0.11; caught by the Sonnet spot-check).
ANSWER_SYSTEM = (
    "You are answering a factual lookup. Reply with ONLY the exact catalog "
    "number requested, and nothing else. If it is not present, reply UNKNOWN."
)


def _answer_text(response: Any) -> str:
    """Concatenate text from a response's content blocks (object or dict form)."""
    parts: list[str] = []
    for block in response.content:
        btype = getattr(block, "type", None)
        if btype is None and isinstance(block, dict):
            btype = block.get("type")
        if btype == "text":
            text = getattr(block, "text", None)
            if text is None and isinstance(block, dict):
                text = block.get("text")
            parts.append(text or "")
    return "".join(parts)


def run_cell(
    *,
    structure: str,
    competition: str,
    similarity: str,
    model: str,
    lengths: Sequence[int],
    depths: Sequence[float],
    seeds: Sequence[int],
    complete_fn: Callable[..., Any],
    count_fn: Callable[..., int],
    out_path: Path,
    filler_sentences: Sequence[str] | None = None,
    n_distractors: int = 4,
    diffuse_density: float = 0.3,
    competitor_pool: Sequence[str] | None = None,
    max_tokens: int = 256,
    max_input_tokens: int = 190_000,
    system: str | None = ANSWER_SYSTEM,
) -> int:
    """Run one condition's full (length x depth x seed) sweep; append JSONL.

    Returns the number of runs executed (written). Runs whose built haystack
    exceeds `max_input_tokens` (margin under the 200k context limit) are SKIPPED
    rather than sent — a safety net against estimate drift; skips are surfaced
    via a printed warning (never silent).

    `system` defaults to ANSWER_SYSTEM, which forces a concise answer so the
    deterministic scorer measures retrieval, not verbosity/truncation (lessons
    §0.11). `max_tokens` is well above the answer length for the same reason.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    skipped = 0
    with out_path.open("a", encoding="utf-8") as f:
        for length in lengths:
            for depth in depths:
                for seed in seeds:
                    h = build_haystack(
                        structure=structure,
                        competition=competition,
                        similarity=similarity,
                        target_tokens=length,
                        depth=depth,
                        seed=seed,
                        filler_sentences=filler_sentences,
                        n_distractors=n_distractors,
                        diffuse_density=diffuse_density,
                        competitor_pool=competitor_pool,
                    )
                    # NO tools param: tool_use history is accepted without it, and
                    # omitting tools means the model CANNOT "search" — it must answer
                    # from context. (Passing tools caused the model to tool-call
                    # instead of answering; tool_choice=none caused empty responses.
                    # Both were artifacts — lessons §0.11.)
                    kwargs: dict[str, Any] = {"model": model, "messages": h.messages}
                    if system:
                        kwargs["system"] = system
                    exact_tokens = count_fn(**kwargs)
                    if exact_tokens > max_input_tokens:
                        skipped += 1
                        continue
                    response = complete_fn(max_tokens=max_tokens, **kwargs)
                    answer = _answer_text(response)
                    hit = is_hit(answer, h.answer_key)
                    record = {
                        "structure": structure,
                        "competition": competition,
                        "similarity": similarity,
                        "model": model,
                        "target_tokens": length,
                        "exact_tokens": exact_tokens,
                        "depth": depth,
                        "seed": seed,
                        "hit": hit,
                        # Full answer (not truncated): a verbose model can state the
                        # needle early then hedge late — a cap would hide the hedge
                        # and let offline `committed` over-count (§0.11). Disk is ours.
                        "answer": answer,
                        # Self-describing record (Substrate Discipline #5): the params
                        # §0.11 proved are outcome-determining are stamped here, so a
                        # record's regime is never ambiguous (an earlier Sonnet file
                        # omitted these and became un-rescoreable).
                        "max_tokens": max_tokens,
                        "system": system,
                        "diffuse_density": diffuse_density,
                        "n_distractors": n_distractors,
                        # 0 = templated competitors; >0 = sampled from a pinned pool
                        # (realism check). Provenance of the pool is in the filename tag.
                        "competitor_pool_size": len(competitor_pool) if competitor_pool else 0,
                        "needle_position": h.metadata["needle_position"],
                        "n_competitors": h.metadata["n_competitors"],
                    }
                    f.write(json.dumps(record, sort_keys=True) + "\n")
                    f.flush()
                    n += 1
    if skipped:
        print(
            f"  WARNING: skipped {skipped} run(s) over {max_input_tokens} input tokens "
            f"({structure}/{competition}/{similarity})"
        )
    return n


def load_records(path: Path) -> list[dict[str, Any]]:
    """Read an append-only JSONL results file."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def accuracy_by_length(records: list[dict[str, Any]]) -> list[tuple[int, float]]:
    """Collapse to (mean exact_tokens, mean accuracy) per target length, sorted."""
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        buckets[r["target_tokens"]].append(r)
    out: list[tuple[int, float]] = []
    for length in sorted(buckets):
        rs = buckets[length]
        mean_tokens = sum(r["exact_tokens"] for r in rs) / len(rs)
        mean_acc = sum(1.0 if r["hit"] else 0.0 for r in rs) / len(rs)
        out.append((int(mean_tokens), mean_acc))
    return out


def passband_knee(
    curve: list[tuple[int, float]], drop: float = 0.1
) -> tuple[float, int | None]:
    """Return (ceiling, knee_tokens).

    `ceiling` = accuracy at the shortest length; `knee` = first token count where
    accuracy falls more than `drop` below the ceiling (None if it never does → a
    full passband across the swept range).
    """
    if not curve:
        return (0.0, None)
    ceiling = curve[0][1]
    for tokens, acc in curve:
        if acc < ceiling - drop:
            return (ceiling, tokens)
    return (ceiling, None)
