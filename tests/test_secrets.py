"""Secret-loading tests (Phase 1.0) — secrets come from .env, NEVER the shell.

Guards the rule that a shell/.zshrc-exported key (e.g. a work key) can never be
used by the project: stance.secrets reads .env directly and never consults
os.environ. See CLAUDE.md security rules + lessons §0.10.
"""

from __future__ import annotations

import pytest

import stance.secrets as secrets


def test_reads_env_file_not_shell(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    envf = tmp_path / ".env"  # type: ignore[operator]
    envf.write_text("ANTHROPIC_API_KEY=from-dotenv-XYZ\n")
    monkeypatch.setattr(secrets, "_ENV_PATH", envf)
    # A shell-exported key must be IGNORED, not preferred.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-shell-MUST-NOT-BE-USED")
    assert secrets.get_secret("ANTHROPIC_API_KEY") == "from-dotenv-XYZ"


def test_raises_when_absent_from_env_even_if_in_shell(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    envf = tmp_path / ".env"  # type: ignore[operator]
    envf.write_text("OTHER=1\n")
    monkeypatch.setattr(secrets, "_ENV_PATH", envf)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "shell-key-must-not-rescue-us")
    with pytest.raises(RuntimeError):
        secrets.get_secret("ANTHROPIC_API_KEY")


def test_has_key_reflects_env_file(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    envf = tmp_path / ".env"  # type: ignore[operator]
    monkeypatch.setattr(secrets, "_ENV_PATH", envf)
    envf.write_text("OTHER=1\n")
    assert secrets.has_anthropic_key() is False
    envf.write_text("ANTHROPIC_API_KEY=k\n")
    assert secrets.has_anthropic_key() is True


def test_deepseek_key_reads_env_not_shell(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    envf = tmp_path / ".env"  # type: ignore[operator]
    envf.write_text("DEEPSEEK_API_KEY=ds-from-dotenv\n")
    monkeypatch.setattr(secrets, "_ENV_PATH", envf)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-from-shell-MUST-NOT-BE-USED")
    assert secrets.deepseek_api_key() == "ds-from-dotenv"


def test_has_deepseek_key_reflects_env_file(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    envf = tmp_path / ".env"  # type: ignore[operator]
    monkeypatch.setattr(secrets, "_ENV_PATH", envf)
    envf.write_text("ANTHROPIC_API_KEY=k\n")
    assert secrets.has_deepseek_key() is False
    envf.write_text("DEEPSEEK_API_KEY=ds\n")
    assert secrets.has_deepseek_key() is True
