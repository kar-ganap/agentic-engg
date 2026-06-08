"""Context-rot experiment harness (Phase 1.0).

Builds synthetic haystacks (haystack.py) and runs the accuracy-vs-length sweep
(runner.py, later) to test §1.8 / §5.2 / §3.6 on our own substrate. See
`docs/synthesis.md` §3.6 for the design + pre-registration.
"""

from stance.rot.haystack import ANSWER_KEY, Haystack, build_haystack

__all__ = ["ANSWER_KEY", "Haystack", "build_haystack"]
