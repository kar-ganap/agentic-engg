"""Thread-B harness tests (Phase 2.0): output-contract parse, retrieval env, baseline arm."""

from __future__ import annotations

from typing import Any

from stance.reasoning.arms import _REACT_MAX_TURNS, Meter, baseline, react
from stance.reasoning.environment import EvidenceEnv
from stance.reasoning.pool import EvidenceItem, Task
from stance.reasoning.position import parse_formed_position


def _task() -> Task:
    return Task(
        pool_id="test",
        debate="does X drive Y?",
        evidence=(
            EvidenceItem("target one full text goes here", "target", "ev-t1"),
            EvidenceItem("a confusable distractor claim, full text", "distractor", "d-1"),
        ),
        correct_position="yes, X drives Y",
        n_distractors=1,
        confusability="high",
        seed=1,
    )


# ---- output-contract parser ----
def test_parse_wellformed() -> None:
    fp = parse_formed_position(
        "STANCE: competition drives it\n"
        "CONFIDENCE: 78\n"
        "RETRACTION: a neutral knee below a diffuse knee\n"
        "EVIDENCE_USED: ev-ruler, d-form-1"
    )
    assert fp.stance == "competition drives it"
    assert fp.confidence == 78
    assert fp.retraction == "a neutral knee below a diffuse knee"
    assert fp.evidence_used == ("ev-ruler", "d-form-1")


def test_parse_multiline_and_surrounding_prose() -> None:
    fp = parse_formed_position(
        "REASONING: some scratch work the model wrote first\n"
        "STANCE: competition drives it,\n"
        "not raw length\n"
        "CONFIDENCE: 80\n"
        "RETRACTION: none\n"
        "EVIDENCE_USED: ev-ruler"
    )
    assert fp.stance == "competition drives it, not raw length"  # multi-line joined
    assert fp.confidence == 80  # REASONING: (unknown label) did not derail parsing


def test_parse_confidence_out_of_range_or_missing() -> None:
    assert parse_formed_position("CONFIDENCE: 140").confidence == -1
    assert parse_formed_position("STANCE: x").confidence == -1  # missing


# ---- retrieval environment ----
def test_env_list_read_and_reads_metric() -> None:
    env = EvidenceEnv(_task())
    listing = env.list_evidence()
    assert "ev-t1:" in listing and "d-1:" in listing  # both ids, teasers
    assert env.read_evidence("ev-t1") == "target one full text goes here"  # full text
    assert env.n_reads == 1
    assert "NOT_FOUND" in env.read_evidence("nope")
    assert env.n_reads == 1  # a failed read does not count


def test_env_dispatch_and_specs() -> None:
    env = EvidenceEnv(_task())
    assert {t["name"] for t in env.tool_specs()} == {"list_evidence", "read_evidence"}
    assert "d-1:" in env.dispatch("list_evidence", {})
    assert env.dispatch("read_evidence", {"id": "d-1"}).startswith("a confusable")
    assert "UNKNOWN_TOOL" in env.dispatch("bogus", {})


# ---- baseline arm (via a fake client) ----
class _Usage:
    input_tokens = 120
    output_tokens = 40
    cache_read_input_tokens = 0


class _Block:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text: str) -> None:
        self.content = [_Block(text)]
        self.stop_reason = "end_turn"
        self.usage = _Usage()


class _FakeClient:
    def __init__(self, text: str) -> None:
        self._text = text
        self.meter = Meter()

    def complete(self, *, system: str, messages: list[dict[str, Any]],
                 tools: Any = None, max_tokens: int = 1024) -> _Resp:
        r = _Resp(self._text)
        self.meter.add(r.usage)
        return r


def test_baseline_arm() -> None:
    canned = (
        "STANCE: competition, not length\nCONFIDENCE: 80\n"
        "RETRACTION: neutral knee below diffuse\nEVIDENCE_USED: ev-t1"
    )
    r = baseline(_task(), _FakeClient(canned))
    assert r.arm == "baseline"
    assert r.position.confidence == 80
    assert r.position.evidence_used == ("ev-t1",)
    assert r.n_calls == 1 and r.n_reads == 0 and r.n_turns == 1  # stuff arm: no reads, single pass
    assert r.input_tokens == 120 and r.output_tokens == 40
    assert r.pool_id == "test" and r.n_distractors == 1 and r.confusability == "high"


# ---- react loop (via a scripted fake that returns tool_use turns then a final answer) ----
class _ToolUse:
    def __init__(self, block_id: str, name: str, args: dict[str, Any]) -> None:
        self.type = "tool_use"
        self.id = block_id
        self.name = name
        self.input = args


class _Scripted:
    def __init__(self, content: list[Any], stop_reason: str) -> None:
        self.content = content
        self.stop_reason = stop_reason
        self.usage = _Usage()


class _ScriptedClient:
    def __init__(self, responses: list[_Scripted]) -> None:
        self._responses = responses
        self._i = 0
        self.meter = Meter()

    def complete(self, *, system: str, messages: list[dict[str, Any]],
                 tools: Any = None, max_tokens: int = 1024) -> _Scripted:
        r = self._responses[self._i]
        self._i += 1
        self.meter.add(r.usage)
        return r


_FINAL = "STANCE: competition\nCONFIDENCE: 70\nRETRACTION: neutral knee\nEVIDENCE_USED: ev-t1"


def test_react_reasons_acts_then_answers() -> None:
    client = _ScriptedClient([
        _Scripted([_ToolUse("t1", "list_evidence", {})], "tool_use"),          # ACT: list
        _Scripted([_ToolUse("t2", "read_evidence", {"id": "ev-t1"})], "tool_use"),  # ACT: read
        _Scripted([_Block(_FINAL)], "end_turn"),                                # REASON: answer
    ])
    r = react(_task(), client)
    assert r.arm == "react"
    assert r.position.confidence == 70
    assert r.n_reads == 1            # read ev-t1 exactly once (the sidestep metric)
    assert r.n_turns == 3 and r.n_calls == 3


def test_react_forced_final_on_cap_exhaustion() -> None:
    # never answers -> exhausts the cap -> one forced final call (no tools) still yields a position
    loops = [_Scripted([_ToolUse("t", "list_evidence", {})], "tool_use")] * _REACT_MAX_TURNS
    client = _ScriptedClient(loops + [_Scripted([_Block("STANCE: forced\nCONFIDENCE: 40")], "end")])
    r = react(_task(), client)
    assert r.position.stance == "forced"
    assert r.n_turns == _REACT_MAX_TURNS + 1  # cap turns + the forced final
    assert r.n_calls == _REACT_MAX_TURNS + 1
