"""The retrieval environment for the *retrieve* arms (ReAct, plan-execute): a Task's evidence set
behind `list_evidence()` / `read_evidence(id)` tools. The *stuff* arms (baseline, reflection) don't
use it — they get the evidence rendered inline.

The §1.8 competition is visible in the list (targets + confusable distractors, indistinguishable by
teaser); a retrieve arm can *sidestep* the rot by reading selectively — so `n_reads` < set size on
large/confusable cells is the sidestep metric the prereg's primary leg predicts.
"""

from __future__ import annotations

from typing import Any

from stance.reasoning.pool import Task


def _teaser(text: str, n_words: int = 12) -> str:
    words = text.split()
    return " ".join(words[:n_words]) + ("…" if len(words) > n_words else "")


class EvidenceEnv:
    def __init__(self, task: Task) -> None:
        self._items = {e.ref: e for e in task.evidence}
        self._order = [e.ref for e in task.evidence]  # already shuffled by the sampler
        self.reads: list[str] = []  # ordered log of read refs (the sidestep metric)

    @property
    def n_reads(self) -> int:
        return len(self.reads)

    def list_evidence(self) -> str:
        return "\n".join(f"{ref}: {_teaser(self._items[ref].text)}" for ref in self._order)

    def read_evidence(self, ref: str) -> str:
        item = self._items.get(ref)
        if item is None:
            return f"NOT_FOUND: no evidence with id {ref!r}; use an id from list_evidence."
        self.reads.append(ref)
        return item.text

    def tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "list_evidence",
                "description": "List every available evidence item as 'id: teaser'. Call first.",
                "input_schema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "read_evidence",
                "description": "Read the full text of one evidence item by its id.",
                "input_schema": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                },
            },
        ]

    def dispatch(self, name: str, args: dict[str, Any]) -> str:
        if name == "list_evidence":
            return self.list_evidence()
        if name == "read_evidence":
            ref = args.get("id", "")
            return self.read_evidence(ref if isinstance(ref, str) else "")
        return f"UNKNOWN_TOOL: {name!r}; use list_evidence or read_evidence."
