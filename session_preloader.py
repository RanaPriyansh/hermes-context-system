"""
Session Preloader — Auto-builds context before each session.

Run this before starting a new session to pre-build the L1 context.
This is the "filesystem mount" — it prepares the working directory
before you cd into it.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def preload_session():
    """Pre-build context for the next session"""
    vault_path = Path.home() / "obsidian-hermes-vault"

    # 1. Scan for active protocols
    protocols = []
    for md in vault_path.rglob("*.md"):
        if "protocol" in md.stem.lower():
            protocols.append(md.stem)

    # 2. Load recent memory
    memory_entries = []
    memory_file = Path.home() / ".hermes" / "memory" / "memory.json"
    if memory_file.exists():
        try:
            data = json.loads(memory_file.read_text())
            memory_entries = [e.get('content', '') for e in data.get('entries', []) if e.get('content')]
        except:
            pass

    # 3. Load recent cron outputs
    cron_outputs = []
    cron_path = Path.home() / ".hermes" / "cron" / "output"
    if cron_path.exists():
        outputs = sorted(cron_path.glob("*.md"), reverse=True)
        cron_outputs = [o.stem for o in outputs[:5]]

    # 4. Build session context
    session_context = {
        "timestamp": datetime.now().isoformat(),
        "l0_identity": {
            "name": "Hermes Agent",
            "mode": "THIELON",
            "user": "Baked Bread",
        },
        "l1_active": {
            "protocols": protocols[:10],
            "memory_entries": memory_entries[:5],
            "cron_outputs": cron_outputs,
        },
        "token_budget": {
            "l0": 500,
            "l1": 8000,
            "l2": "on-demand",
        },
    }

    # 5. Save session context
    session_path = Path.home() / ".hermes" / "context-cache"
    session_path.mkdir(parents=True, exist_ok=True)

    cache_file = session_path / f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(cache_file, 'w') as f:
        json.dump(session_context, f, indent=2)

    print(f"Session context preloaded: {cache_file}")
    print(f"  Protocols: {len(protocols)}")
    print(f"  Memory entries: {len(memory_entries)}")
    print(f"  Cron outputs: {len(cron_outputs)}")

    # 6. Clean old cache files (keep last 10)
    cache_files = sorted(session_path.glob("session-*.json"), reverse=True)
    for old_file in cache_files[10:]:
        old_file.unlink()

    return session_context

if __name__ == "__main__":
    preload_session()
