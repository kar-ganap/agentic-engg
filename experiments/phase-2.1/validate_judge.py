"""Judge-validation (Phase 2.1, B2; §1.9 unblocker). BLIND human-vs-judge agreement on the reasoning
grader (`reasoning.grader`). Generate a worksheet of blind packets (the exact context the judge saw,
minus its scores); you score 0-4 per criterion; then `--score` computes quadratic-weighted Cohen's κ
+ exact/adjacent agreement, per criterion and aggregate. If agreement clears your PRE-REGISTERED
threshold, §1.9 (`reasoning-pattern`) candidate → active (its grader caveat discharged).

    uv run python experiments/phase-2.1/validate_judge.py --n 15    # generate the blind worksheet
    uv run python experiments/phase-2.1/validate_judge.py --score   # after you fill in the SCORES

Blindness is on the honor system: fill `judge-validation-worksheet.md`, do NOT open the key file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from stance.graph.store import GraphStore
from stance.reasoning.grader import CRITERIA, RUBRIC
from stance.reasoning.sampler import build_task

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase-2.0"))
import pool_capability_failuremode as _cap  # noqa: E402
import pool_signal_density as _sig  # noqa: E402
import pool_tool_stability as _tool  # noqa: E402

POOLS = {m.POOL.id: m.POOL for m in (_sig, _tool, _cap)}
CORPUS = Path("experiments/phase-2.0/results")
HERE = Path("experiments/phase-2.1")
WORKSHEET = HERE / "judge-validation-worksheet.md"
KEY = HERE / "judge-validation-key-DONT-OPEN.json"
GRAPH_DIR = Path("data/graph")

# short worksheet labels -> full criterion keys (in CRITERIA order)
SHORT = ["stance", "calibration", "retraction", "evidence", "humility"]
S2C = dict(zip(SHORT, CRITERIA, strict=True))

HEADER = (
    "# Judge-validation worksheet (B2) — score each position BLIND\n\n"
    "For each item, fill the `SCORES` line: replace each `?` with an integer 0-4. Use the same\n"
    "rubric the judge used (below). Do NOT open the key file. Save, then run `--score`.\n\n"
    f"## Rubric (0-4 each)\n{RUBRIC}\n\n---\n"
)


def _records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for f in sorted(CORPUS.glob("reasoning-*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                if d.get("grade_parsed_ok"):
                    rows.append(d)
    return rows


def _stratified(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    """Spread the sample across the grade_total range (not all high-scorers)."""
    rows = sorted(rows, key=lambda r: (r["grade_total"], r["pool"], r["arm"], r["seed"]))
    if n >= len(rows):
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def _render(iid: str, task: Any, r: dict[str, Any]) -> str:
    ev = "\n".join(f"  - [{e.kind}] {e.ref}: {e.text}" for e in task.evidence)
    used = ", ".join(r["evidence_used"]) or "(none)"
    return (
        f"## item {iid}\n"
        f"DEBATE: {task.debate}\n\n"
        f"CORRECT POSITION (grading key): {task.correct_position}\n\n"
        f"EVIDENCE (target = decisive; distractor = related but not decisive):\n{ev}\n\n"
        "POSITION UNDER REVIEW:\n"
        f"  STANCE: {r['stance']}\n"
        f"  CONFIDENCE: {r['confidence']}\n"
        f"  RETRACTION: {r['retraction']}\n"
        f"  EVIDENCE_USED: {used}\n\n"
        "SCORES (0-4): stance=? calibration=? retraction=? evidence=? humility=?\n\n---\n"
    )


def generate(n: int) -> None:
    g = GraphStore(GRAPH_DIR).load()
    sample = _stratified(_records(), n)
    key: dict[str, Any] = {}
    packets = [HEADER]
    for i, r in enumerate(sample, 1):
        task = build_task(POOLS[r["pool"]], g, n_distractors=r["n_distractors"],
                          confusability=r["confusability"], seed=r["seed"])
        iid = f"{i:02d}"
        packets.append(_render(iid, task, r))
        key[iid] = {"judge": {c: r[f"grade_{c}"] for c in CRITERIA},
                    "pool": r["pool"], "arm": r["arm"], "seed": r["seed"],
                    "grade_total": r["grade_total"]}
    WORKSHEET.write_text("\n".join(packets), encoding="utf-8")
    KEY.write_text(json.dumps(key, indent=2), encoding="utf-8")
    totals = sorted(v["grade_total"] for v in key.values())
    print(f"wrote {WORKSHEET.name} ({n} items) + {KEY.name} (judge scores — don't open)")
    print(f"judge grade_total spread across the sample: {totals}")


def _parse_scores(text: str) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    cur: str | None = None
    for line in text.splitlines():
        m = re.match(r"^## item (\w+)", line)
        if m:
            cur = m.group(1)
        elif cur and line.startswith("SCORES"):
            vals = dict(re.findall(r"(\w+)=(\d)", line))
            if all(k in vals for k in SHORT):
                out[cur] = {S2C[k]: int(vals[k]) for k in SHORT}
            cur = None
    return out


def _qwkappa(a: list[int], b: list[int]) -> float:
    """Quadratic-weighted Cohen's κ over categories 0-4."""
    n = len(a)
    if n == 0:
        return float("nan")
    obs = [[0] * 5 for _ in range(5)]
    for x, y in zip(a, b, strict=True):
        obs[x][y] += 1
    row = [sum(obs[i]) for i in range(5)]
    col = [sum(obs[i][j] for i in range(5)) for j in range(5)]
    num = den = 0.0
    for i in range(5):
        for j in range(5):
            w = (i - j) ** 2 / 16.0
            num += w * obs[i][j]
            den += w * row[i] * col[j] / n
    return 1.0 - num / den if den else 1.0


def _agree(a: list[int], b: list[int]) -> tuple[float, float]:
    n = len(a)
    exact = sum(x == y for x, y in zip(a, b, strict=True)) / n
    adj = sum(abs(x - y) <= 1 for x, y in zip(a, b, strict=True)) / n
    return exact, adj


def _rank(xs: list[int]) -> list[float]:
    """Average ranks (1-based); tied values share the mean of their rank positions."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j < len(xs) and xs[order[j]] == xs[order[i]]:
            j += 1
        avg = (i + j - 1) / 2 + 1  # mean of the 1-based ranks i+1..j
        for k in range(i, j):
            ranks[order[k]] = avg
        i = j
    return ranks


def _spearman(a: list[int], b: list[int]) -> float:
    ra, rb = _rank(a), _rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    va = sum((r - ma) ** 2 for r in ra) ** 0.5
    vb = sum((r - mb) ** 2 for r in rb) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


def score() -> None:
    if not WORKSHEET.exists() or not KEY.exists():
        sys.exit("generate the worksheet first (run without --score), then fill it in.")
    key = json.loads(KEY.read_text(encoding="utf-8"))
    human = _parse_scores(WORKSHEET.read_text(encoding="utf-8"))
    items = [i for i in human if i in key]
    if not items:
        sys.exit("no fully-scored items found — replace every ? in the SCORES lines with 0-4.")
    print(f"judge-validation — {len(items)} scored items\n")
    print(f"{'criterion':<20} {'κ(qw)':>7} {'exact':>7} {'adj':>7}")
    kappas = []
    for c in CRITERIA:
        h = [human[i][c] for i in items]
        j = [key[i]["judge"][c] for i in items]
        k = _qwkappa(h, j)
        ex, adj = _agree(h, j)
        kappas.append(k)
        print(f"{c:<20} {k:>7.2f} {ex:>7.2f} {adj:>7.2f}")
    # aggregate: §1.9's DV is grade_total → Spearman rank-correlation is the pre-registered metric
    ht = [sum(human[i][c] for c in CRITERIA) for i in items]
    jt = [key[i]["grade_total"] for i in items]
    mean_k, min_k = sum(kappas) / len(kappas), min(kappas)
    rho = _spearman(ht, jt)
    passed = rho >= 0.7 and min_k >= 0.4
    print(f"\nmean per-criterion κ(qw): {mean_k:.2f}   (min {min_k:.2f}, floor 0.40)")
    print(f"total-score Spearman ρ:   {rho:.2f}   (threshold 0.70)")
    verdict = "PASS → §1.9 candidate → active" if passed else "FAIL → §1.9 stays candidate"
    print(f"\nPRE-REGISTERED RULE  [ρ ≥ 0.70 AND every criterion κ ≥ 0.40]:  {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--score", action="store_true", help="agreement from the filled worksheet")
    args = ap.parse_args()
    score() if args.score else generate(args.n)


if __name__ == "__main__":
    main()
