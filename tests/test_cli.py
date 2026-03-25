import json
import os
import subprocess
import sys
from pathlib import Path

from session_preloader import main as session_preloader_main


ROOT = Path(__file__).resolve().parents[1]


def prepare_env(tmp_path: Path):
    vault = tmp_path / "vault"
    rag = tmp_path / "rag"
    hermes_home = tmp_path / ".hermes"

    (vault / "protocols").mkdir(parents=True)
    (rag).mkdir(parents=True)
    (hermes_home / "memory").mkdir(parents=True)

    (vault / "protocols" / "cli-protocol.md").write_text("CLI protocol\n")
    (hermes_home / "memory" / "memory.json").write_text(
        json.dumps({"entries": [{"content": "cli memory entry"}]})
    )

    env = os.environ.copy()
    env["HERMES_VAULT_PATH"] = str(vault)
    env["HERMES_RAG_PATH"] = str(rag)
    env["HERMES_HOME"] = str(hermes_home)
    return env


def test_cli_commands_smoke(tmp_path):
    env = prepare_env(tmp_path)

    hermes_result = subprocess.run(
        [sys.executable, "hermes_context.py", "l0"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    manager_result = subprocess.run(
        [sys.executable, "context_manager.py", "load", "--tier", "L0"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "=== IDENTITY ===" in hermes_result.stdout
    assert "=== HERMES IDENTITY ===" in manager_result.stdout
    assert "cli memory entry" in manager_result.stdout


def test_session_preloader_main_returns_cleanly(tmp_path, monkeypatch, capsys):
    env = prepare_env(tmp_path)
    for key in ("HERMES_VAULT_PATH", "HERMES_RAG_PATH", "HERMES_HOME"):
        monkeypatch.setenv(key, env[key])

    result = session_preloader_main()
    captured = capsys.readouterr()

    assert result is None
    assert "Session context preloaded:" in captured.out
    cache_dir = Path(env["HERMES_HOME"]) / "context-cache"
    assert list(cache_dir.glob("session-*.json"))
