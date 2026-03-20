"""
Hermes Context System — Master Integration

Three-Tier Context Loading (inspired by OpenViking):
- L0: Core identity (always loaded)
- L1: Active context (session-scoped)
- L2: Deep knowledge (on-demand)

This is the "filesystem mount" for agent context.
Load what you NEED, not what you HAVE.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

# Import our modules
from smart_preloader import L0Identity, L1ActiveContext, L2DeepKnowledge
from vault_integration import scan_active_protocols, find_relevant_notes
from rag_integration import rag_query

class HermesContext:
    """Master context system for Hermes"""

    def __init__(self):
        self.vault_path = str(Path.home() / "obsidian-hermes-vault")
        self.rag_path = str(Path.home() / "hermes-rag-db")
        self.cache_path = Path.home() / ".hermes" / "context-cache"
        self.cache_path.mkdir(parents=True, exist_ok=True)

        # Initialize tiers
        self.l0 = L0Identity()
        self.l1 = L1ActiveContext(self.vault_path)
        self.l2 = L2DeepKnowledge(self.vault_path, self.rag_path)

    def get_context(self, task: str = "general", include_deep: bool = False) -> str:
        """Get full context for a task"""
        sections = []

        # L0: Always include identity
        sections.append(self.l0.render())

        # L1: Active context for the task
        sections.append(self.l1.load_for_task(task))

        # L2: Only if explicitly requested
        if include_deep:
            sections.append(self.l2.query(task))

        return "\n\n".join(sections)

    def save_session_context(self, task: str, context: str):
        """Save session context for future reference"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        cache_file = self.cache_path / f"context-{timestamp}.json"

        session_data = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "token_estimate": len(context.split()) * 1.3,
            "content": context,
        }

        with open(cache_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"Session context saved: {cache_file}")
        return cache_file

    def load_cached_context(self, max_age_hours: int = 24) -> str:
        """Load most recent cached context"""
        cache_files = sorted(self.cache_path.glob("context-*.json"), reverse=True)

        for cache_file in cache_files:
            try:
                data = json.loads(cache_file.read_text())
                timestamp = datetime.fromisoformat(data['timestamp'])
                age = (datetime.now() - timestamp).total_seconds() / 3600

                if age <= max_age_hours:
                    print(f"Loaded cached context from {timestamp}")
                    return data['content']
            except:
                continue

        return ""

def main():
    ctx = HermesContext()

    if len(sys.argv) < 2:
        print("Hermes Context System")
        print("=" * 50)
        print("Usage:")
        print("  python3 hermes_context.py l0                    # Core identity")
        print("  python3 hermes_context.py l1 [task]             # Active context")
        print("  python3 hermes_context.py l2 <query>            # Deep knowledge")
        print("  python3 hermes_context.py full [task]           # Full context")
        print("  python3 hermes_context.py cache [task]          # Save context")
        print("  python3 hermes_context.py load                  # Load cached")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "l0":
        print(ctx.l0.render())

    elif cmd == "l1":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "general"
        print(ctx.l1.load_for_task(task))

    elif cmd == "l2":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "agent identity"
        print(ctx.l2.query(query))

    elif cmd == "full":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "general"
        print(ctx.get_context(task, include_deep=True))

    elif cmd == "cache":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "general"
        context = ctx.get_context(task)
        ctx.save_session_context(task, context)

    elif cmd == "load":
        cached = ctx.load_cached_context()
        if cached:
            print(cached)
        else:
            print("No cached context found")

    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
