import json
from pathlib import Path

from hermes_context import HermesContext


def test_save_and_load_cached_context(tmp_path, monkeypatch):
    hermes_home = tmp_path / ".hermes"
    vault = tmp_path / "vault"
    rag = tmp_path / "rag"
    vault.mkdir()
    rag.mkdir()

    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("HERMES_VAULT_PATH", str(vault))
    monkeypatch.setenv("HERMES_RAG_PATH", str(rag))

    cache_dir = hermes_home / "context-cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "context-invalid.json").write_text("not json")

    ctx = HermesContext()
    saved = ctx.save_session_context("test task", "cached body")

    assert saved.exists()
    payload = json.loads(saved.read_text())
    assert payload["task"] == "test task"
    assert ctx.load_cached_context(max_age_hours=24) == "cached body"


def test_get_context_includes_l0_and_l1(tmp_path, monkeypatch):
    hermes_home = tmp_path / ".hermes"
    vault = tmp_path / "vault"
    rag = tmp_path / "rag"
    (vault / "notes").mkdir(parents=True)
    rag.mkdir()
    hermes_home.mkdir()
    (vault / "notes" / "protocol-note.md").write_text("protocol and task context\n")

    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("HERMES_VAULT_PATH", str(vault))
    monkeypatch.setenv("HERMES_RAG_PATH", str(rag))

    ctx = HermesContext()
    output = ctx.get_context("task context", include_deep=False)

    assert "=== IDENTITY ===" in output
    assert "=== ACTIVE PROTOCOLS ===" in output
