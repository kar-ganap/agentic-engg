"""Project secret loading — STRICTLY from .env, never from the shell.

Rationale (lessons §0.10): shell/.zshrc-exported secrets must not leak into this
project. `python-dotenv`'s `load_dotenv()` does NOT override existing env vars,
so a shell `ANTHROPIC_API_KEY` silently takes precedence over `.env` — that is
exactly how a work key got used for personal experiments here (2026-06-03).

We therefore read `.env` *directly* via `dotenv_values` (which never touches
`os.environ`) and pass the key explicitly to the client. The shell environment
is never consulted, and a missing key fails loudly rather than silently falling
back to whatever is exported in the shell.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def get_secret(name: str) -> str:
    """Return a secret defined in `.env`. Raises if absent — never reads the shell."""
    value = dotenv_values(_ENV_PATH).get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not defined in {_ENV_PATH}. Secrets must live in .env "
            f"(never inherited from the shell/.zshrc, never a work/shared key). "
            f"See CLAUDE.md security rules."
        )
    return value


def has_anthropic_key() -> bool:
    """True iff ANTHROPIC_API_KEY is defined in `.env` (shell is not consulted)."""
    return bool(dotenv_values(_ENV_PATH).get("ANTHROPIC_API_KEY"))


def anthropic_api_key() -> str:
    return get_secret("ANTHROPIC_API_KEY")
