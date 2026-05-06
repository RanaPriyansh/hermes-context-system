import json
from pathlib import Path

from context_manager import ContextManager


def build_sample_layout(tmp_path: Path):
    vault = tmp_path / "vault"
    rag = tmp_path / "rag"
    hermes_home = tmp_path / ".hermes"

    (vault / "protocols").mkdir(parents=True)
    (vault / "notes").mkdir(parents=True)
    (rag).mkdir(parents=True)
    (hermes_home / "memory").mkdir(parents=True)
    (hermes_home / "skills" / "research-skill").mkdir(parents=True)
    (hermes_home / "sessions").mkdir(parents=True)
    (hermes_home / "cron" / "output").mkdir(parents=True)

    (vault / "protocols" / "focus-protocol.md").write_text("Protocol for focus mode\n")
    (vault / "notes" / "agent-identity.md").write_text(
        "Agent identity research note\nHermes agent identity matters.\n"
    )
    (hermes_home / "memory" / "memory.json").write_text(
        json.dumps({"entries": [{"content": "remember the user prefers free software"}]})
    )
    (hermes_home / "skills" / "research-skill" / "SKILL.md").write_text("research skill")
    (hermes_home / "sessions" / "20260101.json").write_text("{}")
    (hermes_home / "cron" / "output" / "daily.md").write_text("cron output")

    return vault, rag, hermes_home


def test_load_tier_l0_uses_memory_and_protocols(tmp_path, monkeypatch):
    vault, rag, hermes_home = build_sample_layout(tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    manager = ContextManager(str(vault), str(rag))
    output = manager.load_tier("L0")

    assert "=== HERMES IDENTITY ===" in output
    assert "focus-protocol" in output
    assert "remember the user prefers free software" in output
    assert isinstance(manager._estimate_tokens("one two three"), int)


def test_load_tier_l0_handles_malformed_memory_json(tmp_path, monkeypatch):
    vault, rag, hermes_home = build_sample_layout(tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    # Corrupt memory payload should not crash L0 loading.
    (hermes_home / "memory" / "memory.json").write_text("{not valid json")

    manager = ContextManager(str(vault), str(rag))
    output = manager.load_tier("L0")

    assert "=== HERMES IDENTITY ===" in output
    assert "=== CORE MEMORY ===" in output


def test_query_escalates_to_l2_for_complex_questions(tmp_path, monkeypatch):
    vault, rag, hermes_home = build_sample_layout(tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    manager = ContextManager(str(vault), str(rag))
    result = manager.query("research agent identity", tier="L1")

    assert "=== ACTIVE SKILLS ===" in result
    assert "=== DEEP KNOWLEDGE: research agent identity ===" in result
    assert "RAG Result 1" in result
