# Hermes Three-Tier Context System

Inspired by OpenViking's context database idea for agents.

The core idea is simple: agents should load context in tiers based on relevance instead of dumping everything into the prompt.

## Three-tier model

### L0: Core identity
- Agent identity and directives
- User profile and stable preferences
- Always loaded
- Small and predictable

### L1: Active context
- Current task context
- Relevant vault notes
- Recent memory, skills, sessions, cron output
- Loaded per session or task

### L2: Deep knowledge
- RAG-backed or vault-backed retrieval
- Historical and broader knowledge
- Queried on demand

## Repository status

This project is intentionally lightweight. It keeps the existing script-first layout, but now has:
- packaging metadata via `pyproject.toml`
- console script entry points
- environment-variable based path overrides for safer local testing
- a small pytest regression suite

## Default paths

By default the scripts look for Hermes data in:
- vault: `~/obsidian-hermes-vault`
- rag db: `~/hermes-rag-db`
- Hermes home: `~/.hermes`

For testing or custom setups, override them with:
- `HERMES_VAULT_PATH`
- `HERMES_RAG_PATH`
- `HERMES_HOME`

## Install

Editable install:

```bash
python3 -m pip install -e .
```

Install with test dependencies:

```bash
python3 -m pip install -e .[test]
```

## Run

Existing script usage is preserved:

```bash
python3 hermes_context.py l0
python3 hermes_context.py l1 "agent identity research"
python3 hermes_context.py l2 "EigenTrust reputation"
python3 hermes_context.py full "agent identity research"

python3 context_manager.py load --tier L0
python3 context_manager.py load --tier L1 --task "agent identity research"
python3 context_manager.py query "research agent identity" --tier L1
```

After installation, console entry points are also available:

```bash
hermes-context l0
hermes-context-manager load --tier L0
hermes-session-preloader
```

## Test

```bash
python3 -m pytest
python3 -m compileall context_manager.py hermes_context.py hermes_paths.py integration.py rag_integration.py session_preloader.py smart_preloader.py vault_integration.py tests
```

## What is covered by tests

The regression suite checks:
- L0 loading from memory and protocol files
- L1 to L2 escalation behavior for complex queries
- context cache save/load behavior
- CLI smoke tests for the main scripts

## Notes

- ChromaDB is optional at runtime. If it is unavailable, RAG calls fall back to error text or vault search behavior already present in the scripts.
- This repo still uses top-level modules rather than a package directory to keep the existing CLI layout unchanged.
