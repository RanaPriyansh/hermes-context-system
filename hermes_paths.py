from pathlib import Path
import os


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()


def vault_path() -> Path:
    return Path(
        os.environ.get("HERMES_VAULT_PATH", Path.home() / "obsidian-hermes-vault")
    ).expanduser()


def rag_path() -> Path:
    return Path(
        os.environ.get("HERMES_RAG_PATH", Path.home() / "hermes-rag-db")
    ).expanduser()


def context_cache_path() -> Path:
    return hermes_home() / "context-cache"


def memory_file_path() -> Path:
    return hermes_home() / "memory" / "memory.json"


def skills_path() -> Path:
    return hermes_home() / "skills"


def sessions_path() -> Path:
    return hermes_home() / "sessions"


def cron_output_path() -> Path:
    return hermes_home() / "cron" / "output"
