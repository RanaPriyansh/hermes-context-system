"""
Smart Context Preloader — Implements OpenViking's Three-Tier Loading

L0: Core identity (always in system prompt — never changes)
L1: Active context (session-scoped — loaded once, cached)
L2: Deep knowledge (on-demand — RAG-retrieved, never bulk-loaded)

Key insight: Load what you NEED, not what you HAVE.
This is the "filesystem paradigm" — context is a tree, you cd into branches.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# ============================================
# L0: Core Identity (Always Loaded)
# ============================================

class L0Identity:
    """
    The immutable core. Loaded once per session.
    Think of this as /etc/passwd — system-level, never changes mid-session.
    """

    def __init__(self):
        self.identity = {
            "name": "Hermes Agent",
            "mode": "THIELON",
            "personality": "contrarian-first, first-principles, monopoly-thinking",
            "user": "Baked Bread",
            "user_prefs": "broke dropout, free/open source first, no paid APIs",
            "platforms": ["local", "telegram"],
            "home_channel": "telegram:7364191237",
        }

        self.core_directives = [
            "Always question consensus. What do very few people agree with you on?",
            "Break problems to physics-level fundamentals.",
            "Every project should aim for unique value nobody can copy.",
            "Ship fast, iterate faster.",
            "Find hidden truths everywhere.",
        ]

    def render(self) -> str:
        """Render L0 as a compact string (~500 tokens)"""
        lines = []
        lines.append("=== IDENTITY ===")
        lines.append(f"Name: {self.identity['name']}")
        lines.append(f"Mode: {self.identity['mode']} — {self.identity['personality']}")
        lines.append(f"User: {self.identity['user']} ({self.identity['user_prefs']})")
        lines.append(f"Platforms: {', '.join(self.identity['platforms'])}")
        lines.append("")
        lines.append("=== DIRECTIVES ===")
        for d in self.core_directives:
            lines.append(f"- {d}")
        return "\n".join(lines)


# ============================================
# L1: Active Context (Session-Scoped)
# ============================================

class L1ActiveContext:
    """
    What's happening RIGHT NOW. Changes every session.
    Think of this as $HOME — your working directory.
    Loaded once, stays in memory for the session.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.active_protocols = []
        self.active_skills = []
        self.active_tasks = []
        self.recent_memory = []
        self.token_budget = 8000  # L1 gets 8K tokens max

    def load_for_task(self, task: str) -> str:
        """Load L1 context relevant to a specific task"""
        sections = []

        # 1. Active protocols
        protocols = self._scan_protocols()
        sections.append("=== ACTIVE PROTOCOLS ===")
        for p in protocols[:5]:
            sections.append(f"- {p}")

        # 2. Task-relevant vault notes (top 3)
        notes = self._find_relevant_notes(task, limit=3)
        sections.append(f"\n=== RELEVANT NOTES (task: {task[:50]}) ===")
        for note in notes:
            sections.append(f"--- {note['title']} ---")
            sections.append(note['preview'][:400])

        # 3. Recent memory entries
        memory = self._load_recent_memory()
        sections.append("\n=== RECENT MEMORY ===")
        for entry in memory[:5]:
            sections.append(f"- {entry}")

        # 4. Active cron outputs
        cron = self._load_cron_outputs()
        if cron:
            sections.append("\n=== LATEST CRON OUTPUTS ===")
            for c in cron[:3]:
                sections.append(f"- {c}")

        return "\n".join(sections)

    def _scan_protocols(self) -> List[str]:
        """Scan vault for active protocols"""
        protocols = []
        for md in self.vault_path.rglob("*.md"):
            content = md.read_text(errors='ignore')
            if "protocol" in md.stem.lower() or "protocol" in content[:200].lower():
                protocols.append(md.stem)
        return protocols[:10]

    def _find_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """Find vault notes relevant to query"""
        results = []
        keywords = query.lower().split()
        for md in self.vault_path.rglob("*.md"):
            try:
                content = md.read_text(errors='ignore')
                score = sum(1 for kw in keywords if kw in content.lower())
                if score > 0:
                    results.append({
                        'title': md.stem,
                        'path': str(md),
                        'preview': content[:500],
                        'score': score,
                    })
            except:
                continue
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    def _load_recent_memory(self) -> List[str]:
        """Load recent memory entries"""
        memory_file = Path.home() / ".hermes" / "memory" / "memory.json"
        if memory_file.exists():
            try:
                data = json.loads(memory_file.read_text())
                entries = data.get('entries', [])
                return [e.get('content', '') for e in entries if e.get('content')]
            except:
                pass
        return []

    def _load_cron_outputs(self) -> List[str]:
        """Load recent cron outputs"""
        cron_path = Path.home() / ".hermes" / "cron" / "output"
        if cron_path.exists():
            outputs = sorted(cron_path.glob("*.md"), reverse=True)
            return [o.stem for o in outputs[:5]]
        return []


# ============================================
# L2: Deep Knowledge (On-Demand)
# ============================================

class L2DeepKnowledge:
    """
    The infinite library. Never loaded in bulk.
    Think of this as a filesystem — you ls and cat specific files.
    Queried via RAG, never dumped into context.
    """

    def __init__(self, vault_path: str, rag_db_path: str):
        self.vault_path = Path(vault_path)
        self.rag_db_path = Path(rag_db_path)

    def query(self, question: str, n_results: int = 5) -> str:
        """Query deep knowledge — returns only relevant snippets"""
        # Try ChromaDB first
        rag_results = self._rag_search(question, n_results)
        if rag_results:
            sections = [f"=== DEEP KNOWLEDGE: {question[:60]} ==="]
            for i, r in enumerate(rag_results, 1):
                sections.append(f"\n[{i}] {r.get('title', 'Unknown')}")
                sections.append(r.get('content', '')[:400])
            return "\n".join(sections)

        # Fallback: grep vault
        grep_results = self._grep_vault(question, limit=n_results)
        if grep_results:
            sections = [f"=== VAULT SEARCH: {question[:60]} ==="]
            for i, r in enumerate(grep_results, 1):
                sections.append(f"\n[{i}] {r['file']}:{r['line']}")
                sections.append(r['content'][:300])
            return "\n".join(sections)

        return f"[L2] No results for: {question}"

    def _rag_search(self, query: str, n_results: int) -> List[Dict]:
        """Search ChromaDB for relevant context"""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(self.rag_db_path))
            collection = client.get_collection("hermes_vault")
            results = collection.query(query_texts=[query], n_results=n_results)
            docs = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            return [
                {
                    'title': meta.get('title', 'Unknown') if meta else 'Unknown',
                    'content': doc,
                }
                for doc, meta in zip(docs, metadatas)
            ]
        except Exception as e:
            return []

    def _grep_vault(self, query: str, limit: int = 5) -> List[Dict]:
        """Grep vault files for query terms"""
        results = []
        keywords = query.lower().split()
        for md in self.vault_path.rglob("*.md"):
            try:
                for i, line in enumerate(md.read_text(errors='ignore').splitlines()):
                    if any(kw in line.lower() for kw in keywords):
                        results.append({
                            'file': str(md.relative_to(self.vault_path)),
                            'line': i + 1,
                            'content': line.strip(),
                        })
                        if len(results) >= limit:
                            return results
            except:
                continue
        return results


# ============================================
# Main: Three-Tier Context Loader
# ============================================

class ContextSystem:
    """
    The full three-tier context system.
    Filesystem paradigm: L0 is /etc, L1 is $HOME, L2 is the entire filesystem.
    """

    def __init__(self):
        self.vault_path = str(Path.home() / "obsidian-hermes-vault")
        self.rag_path = str(Path.home() / "hermes-rag-db")

        self.l0 = L0Identity()
        self.l1 = L1ActiveContext(self.vault_path)
        self.l2 = L2DeepKnowledge(self.vault_path, self.rag_path)

    def get_context(self, task: str, include_deep: bool = False) -> str:
        """Get full context for a task"""
        sections = []

        # Always include L0
        sections.append(self.l0.render())

        # Include L1 for the task
        sections.append(self.l1.load_for_task(task))

        # Only include L2 if explicitly requested
        if include_deep:
            sections.append(self.l2.query(task))

        return "\n\n".join(sections)

    def deep_query(self, question: str) -> str:
        """Deep query — L2 only"""
        return self.l2.query(question)


# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    import sys

    ctx = ContextSystem()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 smart_preloader.py l0          # Show core identity")
        print("  python3 smart_preloader.py l1 <task>   # Load active context for task")
        print("  python3 smart_preloader.py l2 <query>  # Deep knowledge query")
        print("  python3 smart_preloader.py full <task> # Full context (L0+L1+L2)")
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
    else:
        print(f"Unknown command: {cmd}")
