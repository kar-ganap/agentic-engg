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

# Uniform, content-free label for every item — the anti-triage design (§0.25 re-test). If the list
# showed a content teaser, a retrieve arm could skim-triage the decisive items without reading; the
# uniform label forces it to actually read, so commit-to-few is tested honestly, not via triage.
_ITEM_LABEL = "[evidence — read the item to view its content]"


class EvidenceEnv:
    def __init__(self, task: Task) -> None:
        self._items = {e.display_id: e for e in task.evidence}  # keyed by the anonymized id
        self._order = [e.display_id for e in task.evidence]  # already shuffled by the sampler
        self.reads: list[str] = []  # ordered log of read display_ids (the sidestep metric)

    @property
    def n_reads(self) -> int:
        return len(self.reads)

    def list_evidence(self) -> str:
        return "\n".join(f"{did}: {_ITEM_LABEL}" for did in self._order)  # uniform -> no tell

    def read_evidence(self, did: str) -> str:
        item = self._items.get(did)
        if item is None:
            return f"NOT_FOUND: no evidence with id {did!r}; use an id from list_evidence."
        self.reads.append(did)
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
