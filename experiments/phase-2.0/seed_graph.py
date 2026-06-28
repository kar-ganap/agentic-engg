"""Seed the evidence graph (Phase 2.0, step 4) — hand-authored positions into data/graph/.

WORKED EXAMPLE: §1.8 (signal-density rot) is transcribed from docs/synthesis.md as the
template. It shows BOTH halves meeting:
  (1) a position authored in — stance / confidence / retraction / evidence via Support-with-
      warrant / a DecisiveProbe / an edge; and
  (2) the EXPERIMENT -> GRAPH write-path that closes the loop (`record_experiment_result`):
      an experiment result becomes Evidence(experimental) + Support(warrant) + a new
      latest-wins Position version at the moved confidence.

The remaining seeds (§1.1+#3, §3.8) are TODO stubs — authoring them IS the position-
formation work (learning-first), so it's intentionally left to you, by the §1.8 pattern.

Run (no API, no cost; resets data/graph/ then re-seeds reproducibly):
    uv run python experiments/phase-2.0/seed_graph.py
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from stance.graph.models import Claim, DecisiveProbe, Evidence, Leg, Position, Retraction, Support
from stance.graph.store import GraphStore

GRAPH_DIR = Path("data/graph")


def _reset(root: Path) -> None:
    """Append-only store → clear the files first so re-seeding doesn't duplicate edges."""
    if root.exists():
        for f in root.glob("*.jsonl"):
            f.unlink()


def record_experiment_result(
    store: GraphStore, *, position: Position, evidence: Evidence, warrant: str,
    new_confidence: int, updated: str,
) -> Position:
    """THE EXPERIMENT -> GRAPH WRITE-PATH (the loop closing).

    An experiment result becomes Evidence(type=experimental) + a Support carrying the
    warrant (the mechanism), then the Position gets a new latest-wins version at the moved
    confidence. Today this is called by hand from a results-*.md write-up; later it is what
    'wire the loop into the spine' (Thread B) + the re-evaluation surface (Phase 2.1) automate.
    """
    store.add(evidence)
    store.add(Support(position_id=position.id, evidence_id=evidence.id,
                      warrant=warrant, polarity="supports"))
    moved = replace(position, confidence=new_confidence, updated=updated)
    store.add(moved)
    return moved


def seed_18(store: GraphStore) -> None:
    """§1.8 — signal density, not token count, governs context-rot onset (transcribed)."""
    store.add(Claim(
        id="cl-diffuse-collapse", kind="finding",
        text="Under diffuse (pervasive) competition, confident retrieval collapses well "
             "before length limits.",
        evidence_ids=("ev-ruler", "ev-nolima", "ev-length-ext"),
    ))
    store.add(Evidence(
        id="ev-ruler", type="literature", source="Hsieh et al., RULER, arXiv:2404.06654",
        summary="Multi-key NIAH: perfect vanilla NIAH, large drops with length; failure to "
                "ignore distractors.",
        strength="corroborating", claim_ids=("cl-diffuse-collapse",),
    ))
    store.add(Evidence(
        id="ev-nolima", type="literature",
        source="Modarressi et al., NoLiMa, arXiv:2502.05167 (ICML 2025)",
        summary="Minimal needle-question lexical overlap -> 10/12 models below 50% by 32k; "
                "semantic-routing difficulty, not raw length.",
        strength="corroborating", claim_ids=("cl-diffuse-collapse",),
    ))

    # Initial register (transcription draft — verify dates/values vs synthesis §1.8).
    pos = Position(
        id="1.8", title="Signal density, not token count, governs context-rot onset",
        stance="Onset/severity of context rot is governed by the context's signal-to-noise "
               "ratio, not raw token count: at fixed length, adding semantically-similar "
               "competitors sharply degrades retrieval; at fixed signal density, length "
               "matters far less.",
        confidence=78, status="candidate", registered="2026-06-04", updated="2026-06-04",
        preconditions=("retrieval/reasoning over long context (>= ~knee length)",),
        retraction=(
            Retraction("down", 30, "a model shows a neutral (no-competition) knee BELOW its "
                       "diffuse knee — pure length rots before competition", ("clause-a",)),
            Retraction("down", 20, "diffuse competition fails to collapse confident retrieval "
                       "in a different model family (cross-family generality)", ("clause-b",)),
        ),
        edges=(("tension_with", "2.1"),), synthesis_ref="1.8",
    )
    store.add(pos)
    store.add(Support("1.8", "ev-ruler", polarity="supports",
                      warrant="distractor count drives the drop independent of finding the "
                              "needle => competition, not length, is the driver"))
    store.add(Support("1.8", "ev-nolima", polarity="supports",
                      warrant="removing lexical overlap localizes failure to semantic routing "
                              "under length => S/N, not raw tokens"))

    # The loop closing: the Phase 1.0-ext length-extension experiment moves §1.8 78 -> 80.
    record_experiment_result(
        store, position=pos, new_confidence=80, updated="2026-06-13",
        evidence=Evidence(
            id="ev-length-ext", type="experimental",
            source="experiments/phase-1.0/results-length-extension.md",
            summary="v4-pro neutral null holds flat to ~94k, only mild decay by 758k (0.67) — "
                    "pure-length effect appears ~7x above the diffuse knee.",
            strength="direct", claim_ids=("cl-diffuse-collapse",),
        ),
        warrant="pure length rots far LATER than competition on a capable cross-family model "
                "=> reinforces the competition-first ordering (pillar B)",
    )

    # The decisive uncollected datum (clause b) — what would most move §1.8 next.
    store.add(DecisiveProbe(
        id="probe-diffuse-crossfamily", expected="up", why_uncollected="methodology-gap",
        description="Cross-family diffuse-collapse replication with a STRUCTURE-INVARIANT "
                    "needle (mid-similarity; control holds on both prose and tool-stream) — "
                    "discharges §1.8 clause (b).",
        would_move=("1.8",), status="deferred",
        note="~+5 toward 85 if it replicates; the 1.0-ext attempt hit structure x similarity "
             "entanglement (results-cross-family.md).",
    ))


def seed_11(store: GraphStore) -> None:
    """§1.1 — tool definitions should be stable across a run (transcribed). Exercises LEGS.

    mechanism-data (§1.1's measurement spec) is NOT transcribed — it's the deferred evaluator
    layer (v1); it stays in synthesis.md prose for now.
    """
    store.add(Claim(
        id="cl-tool-cache-root", kind="finding",
        text="The tool block sits at the front of the cached prefix; mutating it invalidates "
             "the whole suffix (measured ~7x a stable prefix).",
        evidence_ids=("ev-exb", "ev-manus"),
    ))
    store.add(Claim(
        id="cl-stale-toolref-confuses", kind="proposition",
        text="Stale tool_use references in history confuse the model when the current tools "
             "list disagrees (the coherence leg — literature-only, untested here).",
        evidence_ids=("ev-manus",),
    ))
    store.add(Evidence(
        id="ev-manus", type="literature",
        source="Manus, Context Engineering: Lessons from Building Manus (July 2025)",
        summary="Both the KV-cache argument (stable prefix) and the model-confusion argument "
                "(stale tool_use refs) for not mutating tools mid-run.",
        strength="corroborating", claim_ids=("cl-tool-cache-root", "cl-stale-toolref-confuses"),
    ))
    store.add(Evidence(
        id="ev-exb", type="experimental",
        source="experiments/phase-1.0/results-exercise-B.md",
        summary="KV-cache anti-patterns: tools are the cache root; mutating the tool block costs "
                "~7x a stable prefix.",
        strength="direct", claim_ids=("cl-tool-cache-root",),
    ))
    store.add(Position(
        id="1.1", title="Tool definitions should be stable across a run (no mid-loop mutation)",
        stance="For KV-cached, multi-turn agents, the tools=[] parameter should be set once at "
               "run start and not mutated mid-loop; handle state-dependent availability in the "
               "latest user message (and via tool_choice), not by mutating tools/system.",
        confidence=80, status="candidate", registered="2026-06-01", updated="2026-06-05",
        legs=(
            Leg("cache-economics", 90, "measured: tools are the cache root; mutating = ~7x a "
                "stable prefix (Exercise B)"),
            Leg("model-coherence", 65, "literature-only (Manus), untested here — headline 80 is "
                "capped by this weaker leg; retraction needs BOTH legs null"),
        ),
        preconditions=(
            "KV-cache inference AND >=3 multi-turn iterations with a shared prefix",
            "run long enough that the cached-token discount exceeds stable-prefix discipline "
            "(~10+ turns at meaningful volume)",
            "loop preserves full history (heavy compaction of stale tool_use refs weakens the "
            "coherence leg)",
            "Anthropic-served Sonnet/Opus/Haiku family (other providers may differ)",
        ),
        retraction=(
            Retraction("down", 30, "controlled Anthropic measurement: lexically-changing tools "
                       "mid-run shows NO cache-hit degradation AND no coherence degradation; OR "
                       "Anthropic ships first-class state-conditioned tool masking",
                       ("cache", "coherence")),
            Retraction("down", 10, "coherence problem shown much smaller than the cache problem "
                       "-> care about mutation for cache reasons only", ("scope",)),
            Retraction("up", 10, "severe coherence breakdown under mutation (hallucinated tool "
                       "names / repeated failed calls to removed tools)", ("coherence",)),
        ),
        synthesis_ref="1.1",
    ))
    store.add(Support("1.1", "ev-exb", polarity="supports",
                      warrant="mutating the tool block busts the cached prefix => ~7x cost; this "
                              "is the cache-economics leg (~90)"))
    store.add(Support("1.1", "ev-manus", polarity="supports",
                      warrant="stale tool_use refs vs the current tools list confuse the model; "
                              "the model-coherence leg (~65, untested)"))


def seed_3(store: GraphStore) -> None:
    """#3 — carry-vs-swap tool-set break-even (transcribed). A SEPARATE Position that QUALIFIES
    §1.1's cache leg. Graph id "carry-swap" (a slug, to avoid clashing with §3.x synthesis
    numbering; synthesis_ref points back to §1.1, where it lives in prose)."""
    store.add(Claim(
        id="cl-carry-swap-crossover", kind="finding",
        text="A carry-vs-swap tool-set break-even exists, KV-cache-governed: carry-cost is linear "
             "in superset size, swap-cost flat; below N* carry is cheaper, above it swap wins "
             "despite busting the cache.",
        evidence_ids=("ev-smoke-cache", "ev-breakeven", "ev-dontbreakcache"),
    ))
    store.add(Evidence(
        id="ev-smoke-cache", type="experimental", source="experiments/phase-1.1/smoke_cache.py",
        summary="DeepSeek prefix-caches tool defs; mutating the tool block busts the suffix "
                "(cache_read 15,488 -> 0 -> 15,488).",
        strength="direct", claim_ids=("cl-carry-swap-crossover",),
    ))
    store.add(Evidence(
        id="ev-breakeven", type="experimental",
        source="experiments/phase-1.1/results-3.md (predict_cache_breakeven + cache_breakeven)",
        summary="predict->verify: pre-registered N* ~5,111 tool-tokens; empirical 6,461 (~26%; "
                "carry slope matched <0.1%, residual = actual S/C/k vs nominal).",
        strength="direct", claim_ids=("cl-carry-swap-crossover",),
    ))
    store.add(Evidence(
        id="ev-dontbreakcache", type="literature",
        source="Don't Break the Cache, arXiv:2601.06007 (Jan 2026)",
        summary="Cross-provider: excluding dynamic tool results beats naive full-context caching; "
                "confirms carry-linear / don't-bust but does NOT derive the swap crossover.",
        strength="corroborating", claim_ids=("cl-carry-swap-crossover",),
    ))
    store.add(Position(
        id="carry-swap",
        title="Carry-vs-swap tool-set break-even (#3) — qualifies §1.1's cache leg",
        stance="Given a large tool universe, there is a KV-cache-governed break-even in superset "
               "size: carry a fixed superset below N* (cache-stable), swap a minimal per-task set "
               "above it. Existence + cost-model are cross-provider; the LOCATION is "
               "provider/TTL/session-shape-dependent.",
        confidence=78, status="candidate", registered="2026-06-14", updated="2026-06-14",
        preconditions=(
            "prefix-cache inference where hit-rate < miss-rate",
            "tool universe large relative to any single task's needs (else carry trivially wins)",
        ),
        retraction=(
            Retraction("down", 30, "no carry/swap crossover within a realistic superset range on "
                       "any prefix-cached provider, OR carry stays cheaper at all superset sizes "
                       "(carry-cost not linear in tool-block size)", ("mechanism",)),
        ),
        edges=(("qualifies", "1.1"),), synthesis_ref="1.1",
    ))
    store.add(Support("carry-swap", "ev-smoke-cache", polarity="supports",
                      warrant="tool defs live in the cached prefix and mutation busts the suffix "
                              "=> the swap arm pays a full re-miss per task-switch (the cost "
                              "model's foundation)"))
    store.add(Support("carry-swap", "ev-breakeven", polarity="supports",
                      warrant="carry linear in superset size, swap flat => they cross; the "
                              "predicted N* was verified empirically => the break-even EXISTS"))
    store.add(Support("carry-swap", "ev-dontbreakcache", polarity="supports",
                      warrant="independent cross-provider confirmation of carry-linear/don't-bust; "
                              "it does NOT derive the swap crossover => that's our delta"))
    store.add(DecisiveProbe(
        id="probe-claude-cache-anchor", expected="up", why_uncollected="cost",
        description="Claude (Anthropic) cache anchor: re-run the carry-vs-swap break-even under "
                    "the ~10x hit-discount / 5-min TTL to confirm the crossover LOCATION moves as "
                    "the cost model predicts (cross-provider location-generality).",
        would_move=("carry-swap",), status="deferred",
        note="~+5-8 toward mid-80s if location moves as modelled; would lower if it doesn't. The "
             "78 headline already prices this deferral (existence cross-provider, location not).",
    ))


def seed_38(store: GraphStore) -> None:
    """§3.8 — capability shifts the failure mode (confabulate -> refuse) (transcribed).
    The only status="hypothesis"; exercises CONTRADICTING evidence + a qualifies->1.8 edge."""
    store.add(Claim(
        id="cl-capability-shifts-mode", kind="finding",
        text="Under diffuse competition, as capability rises the failure mode shifts from "
             "confident confabulation toward honest refusal and the knee moves EARLIER "
             "(consistent with conflict-detection OR refusal-affordance-following — undecided).",
        evidence_ids=("ev-exA-capability", "ev-deepseek-abstain"),
    ))
    store.add(Claim(
        id="cl-parametric-opposite-scaling", kind="finding",
        text="In the PARAMETRIC knowledge-gap regime, larger / instruction-tuned models "
             "hallucinate MORE and abstain LESS — the opposite scaling.",
        evidence_ids=("ev-loops-to-oops",),
    ))
    store.add(Evidence(
        id="ev-exA-capability", type="experimental", source="experiments/phase-1.0/results.md",
        summary="Exercise A: Sonnet diffuse-committed hits 0 by ~5k vs Haiku ~20k (knee ~4x "
                "earlier in the stronger model); Sonnet refuses (UNKNOWN), Haiku confabulates.",
        strength="direct", claim_ids=("cl-capability-shifts-mode",),
    ))
    store.add(Evidence(
        id="ev-deepseek-abstain", type="experimental",
        source="experiments/phase-1.0/results-cross-family.md",
        summary="DeepSeek v4-flash: a 3rd failure mode (abstention; empty-rate 24% diffuse vs 2% "
                "neutral) — but capability x training confounded, so suggestive only.",
        strength="corroborating", claim_ids=("cl-capability-shifts-mode",),
    ))
    store.add(Evidence(
        id="ev-loops-to-oops", type="literature",
        source="From Loops to Oops (arXiv:2407.06071) + OpenAI, Why Language Models Hallucinate",
        summary="Larger / instruction-tuned models hallucinate MORE and abstain LESS — the "
                "OPPOSITE scaling — but in the parametric knowledge-gap regime, not in-context.",
        strength="contradicting", claim_ids=("cl-parametric-opposite-scaling",),
    ))
    store.add(Position(
        id="3.8",
        title="Capability shifts the diffuse-competition failure mode (confabulate -> refuse)",
        stance="As capability rises under diffuse competition, the failure mode shifts from "
               "confident confabulation toward honest refusal and the diffuse knee moves EARLIER, "
               "not later (a stronger model = a better conflict-detector, not a more robust "
               "retriever). Conflict-detection OR refusal-affordance-following — undecided.",
        confidence=45, status="hypothesis", registered="2026-06-04", updated="2026-06-04",
        preconditions=(
            "diffuse (pervasive, length-scaling) competition",
            "a unique true answer exists (so refusal is a genuine binding failure, not caution)",
            "models in the same family/era (cross-family confounds capability with training)",
        ),
        retraction=(
            Retraction("down", 30, "a stronger model shows a LATER diffuse knee AND a lower "
                       "refusal rate (capability -> genuine robustness, not earlier honesty) — "
                       "inverts the claim", ("invert",)),
            Retraction("down", 15, "the refuse-vs-confabulate split is an artifact of the explicit "
                       "UNKNOWN affordance, not capability (vary the refusal affordance)",
                       ("affordance", "scope")),
            Retraction("up", 10, "a 3rd model on the ladder continues the monotone "
                       "more-capable->earlier-refusal trend AND the split survives removing the "
                       "UNKNOWN affordance", ("ladder",)),
        ),
        edges=(("qualifies", "1.8"),), synthesis_ref="3.8",
    ))
    store.add(Support("3.8", "ev-exA-capability", polarity="supports",
                      warrant="knee ~4x earlier + the confabulate(Haiku)->refuse(Sonnet) split "
                              "across a capability step => capability shifts the failure mode"))
    store.add(Support("3.8", "ev-deepseek-abstain", polarity="supports",
                      warrant="a 3rd mode (abstention) on a cross-family model — suggestive, but "
                              "confounded (capability x training), so does NOT advance the claim"))
    store.add(Support("3.8", "ev-loops-to-oops", polarity="contradicts",
                      warrant="opposite scaling in the PARAMETRIC regime => §3.8 is a candidate "
                              "REGIME-DEPENDENT reversal (in-context, not parametric) => higher "
                              "burden of proof; the affordance-control is mandatory"))
    store.add(DecisiveProbe(
        id="probe-refusal-affordance", expected="toggle", why_uncollected="cost",
        description="Refusal-affordance control: re-run the capability comparison with the "
                    "explicit 'reply UNKNOWN' affordance removed, on a >=3-model ladder x >=5 "
                    "seeds — does the confabulate->refuse split survive, or was it the affordance?",
        would_move=("3.8",), status="planned",
        note="the contradicting parametric-regime literature makes the UNKNOWN affordance the "
             "prime suspect; this control is MANDATORY before §3.8 rises above ~55.",
    ))


def main() -> None:
    _reset(GRAPH_DIR)
    store = GraphStore(GRAPH_DIR)
    seed_18(store)
    seed_11(store)
    seed_3(store)
    seed_38(store)

    # Summary: every seeded position, round-tripped back out of the store.
    g = store.load()
    print(f"{'id':<11} {'conf':>4} {'status':<10} {'#ev':>3} {'#probe':>6}  edges")
    for pid in sorted(g.positions):
        p = g.positions[pid]
        print(f"{pid:<11} {p.confidence:>4} {p.status:<10} "
              f"{len(g.evidence_for(pid)):>3} {len(g.probes_for(pid)):>6}  {g.edges_of(pid)}")
    print(f"\nclaims={len(g.claims)}  evidence={len(g.evidence)}  "
          f"supports={len(g.supports)}  probes={len(g.probes)}")


if __name__ == "__main__":
    main()
