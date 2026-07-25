"""The arm harness: telemetry (`Meter`), the `Client` protocol arms call, the `ArmResult` they
return, and BASELINE as a worked template. ReAct / plan-execute / reflection are the load-bearing
Module-3 loops — user-written (see the stubs).

All arms share the same output contract (position.POSITION_FORMAT -> FormedPosition), the same
evidence (a Task), the same Client. They differ ONLY in reasoning structure, so the DV
(quality x token-cost x latency) isolates structure, not prompt richness. Access model (per the
prereg): baseline & reflection STUFF (evidence in the prompt) -> eat the §1.8 rot as N grows;
ReAct & plan-execute RETRIEVE (via EvidenceEnv) -> can sidestep it.

src/ stays provider-agnostic: arms depend on the `Client` protocol; the concrete anthropic/DeepSeek
client is wired in the runner (experiments/), and fakes satisfy it in tests.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from stance.reasoning.pool import Task
from stance.reasoning.position import POSITION_FORMAT, FormedPosition, parse_formed_position

SYSTEM = (
    "You are a careful analyst forming an evidence-based position on a contested question. "
    "Give a calibrated confidence and a falsifiable retraction condition."
)  # neutral by design: no distractor pre-warning (else the §1.8 rot can't be induced — the #4 trap)


@dataclass
class Meter:
    """Accumulates token usage across an arm's LLM calls. One fresh client (hence Meter) per run."""

    n_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0

    def add(self, usage: Any) -> None:
        self.n_calls += 1
        self.input_tokens += getattr(usage, "input_tokens", 0) or 0
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0


class Response(Protocol):
    content: list[Any]
    stop_reason: str | None
    usage: Any


class Client(Protocol):
    """What an arm needs from the model; the concrete client lives in the runner."""

    meter: Meter

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = ...,
        max_tokens: int = ...,
    ) -> Response: ...


@dataclass(frozen=True)
class ArmResult:
    arm: str
    position: FormedPosition
    # cost side of the DV
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    n_calls: int
    n_reads: int  # EvidenceEnv reads (0 for stuff arms) — the sidestep metric
    n_turns: int
    latency_s: float
    # cell coordinates (copied off the Task)
    pool_id: str
    n_distractors: int
    confusability: str
    seed: int


Arm = Callable[[Task, Client], ArmResult]


def _text(content: list[Any]) -> str:
    return "".join(getattr(b, "text", "") for b in content if getattr(b, "type", None) == "text")


def render_stuffed(task: Task) -> str:
    """The STUFF prompt: debate + the full evidence set inline (baseline & reflection)."""
    lines = [f"DEBATE: {task.debate}", "", "EVIDENCE:"]
    lines += [f"- [{e.ref}] {e.text}" for e in task.evidence]
    lines += ["", POSITION_FORMAT]
    return "\n".join(lines)


def make_result(
    arm: str, task: Task, position: FormedPosition, client: Client, *,
    n_reads: int, n_turns: int, latency_s: float,
) -> ArmResult:
    """Assemble an ArmResult from the client's Meter + the loop's read/turn counts. The arms call
    this so the telemetry shape stays uniform across them."""
    m = client.meter
    return ArmResult(
        arm=arm, position=position, input_tokens=m.input_tokens, output_tokens=m.output_tokens,
        cache_read_tokens=m.cache_read_tokens, n_calls=m.n_calls, n_reads=n_reads, n_turns=n_turns,
        latency_s=latency_s, pool_id=task.pool_id, n_distractors=task.n_distractors,
        confusability=task.confusability, seed=task.seed,
    )


def baseline(task: Task, client: Client) -> ArmResult:
    """STUFF + single-pass: the whole evidence set in one prompt, one call, parse. The template the
    three real arms extend — they change the reasoning structure, never the contract."""
    started = time.time()
    resp = client.complete(
        system=SYSTEM,
        messages=[{"role": "user", "content": render_stuffed(task)}],
        max_tokens=1024,
    )
    position = parse_formed_position(_text(resp.content))
    return make_result(
        "baseline", task, position, client, n_reads=0, n_turns=1, latency_s=time.time() - started
    )


# --- The three load-bearing arms (user-written). Signatures + specs fixed; bodies TBD. ----------
def react(task: Task, client: Client) -> ArmResult:
    """RETRIEVE + adaptive. Build EvidenceEnv(task); give the model env.tool_specs(). Loop:
    reason -> (maybe) call list_evidence / read_evidence via client.complete(tools=...) ->
    env.dispatch -> feed the result back -> repeat; stop when the model answers in POSITION_FORMAT
    (no tool_use). Bet: reads selectively, so n_reads < set size on large cells. TODO(user)."""
    raise NotImplementedError("react: user-written (Module-3 loop)")


def plan_execute(task: Task, client: Client) -> ArmResult:
    """RETRIEVE + plan-first. Call 1: a short plan (which evidence to examine, what to check).
    Then execute (read via EvidenceEnv) -> emit POSITION_FORMAT. Bet: lookahead earns its keep only
    on large sets; ties or trails ReAct on small/known ones. TODO(user)."""
    raise NotImplementedError("plan_execute: user-written (Module-3 loop)")


def reflection(task: Task, client: Client) -> ArmResult:
    """STUFF + iterative. Draft (render_stuffed) -> self-critique against the rubric dimensions ->
    revise -> final POSITION_FORMAT. Bet: lift < its HumanEval reputation because our feedback is a
    fuzzy rubric, not crisp pass/fail (self-review-on-noise risk). TODO(user)."""
    raise NotImplementedError("reflection: user-written (Module-3 loop)")


# The registry the runner iterates; the user arms join here as they land.
ARMS: dict[str, Arm] = {"baseline": baseline}
