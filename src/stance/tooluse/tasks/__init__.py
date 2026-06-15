"""Per-tier task builders over the shared customer-support substrate (Phase 1.1).

Each builder turns a cell + seed into a `(World, TaskInstance)` — staging the World
so the dependency-forced calls return the controlled stimulus, and emitting the
write-boundary predicates from the ground truth it created (consistent by
construction). The loop/scorer stay tier-agnostic. See docs/phases/phase-1.1-plan.md
§ "Generator / task-config".
"""
