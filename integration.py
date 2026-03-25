"""
Integration: Three-Tier Context + Existing Hermes Infrastructure
Connects the context system with vault, memory, ChromaDB, and session transcripts.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from hermes_paths import cron_output_path, memory_file_path, sessions_path, vault_path, rag_path

# ============================================
# Vault Context Provider
# ============================================

class VaultContextProvider:
    """Provides context from Obsidian vault"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)

    def get_l1_context(self, task: str) -> str:
        """Get L1 context: active protocols, relevant notes"""
        sections = []

        # Active protocols (always in L1)
        protocols = self._scan_protocols()
        if protocols:
            sections.append("=== ACTIVE PROTOCOLS ===")
            for p in protocols[:5]:
                sections.append(f"- {p}")

        # Task-relevant notes
        relevant = self._find_relevant_notes(task, limit=3)
        if relevant:
            sections.append(f"\n=== RELEVANT NOTES: {task[:50]} ===")
            for note in relevant:
                sections.append(f"--- {note['title']} ---")
                sections.append(note['preview'][:400])

        return "\n".join(sections)

    def get_l2_context(self, query: str) -> str:
        """Get L2 context: deep vault search"""
        results = self._search_vault(query, limit=5)
        if not results:
            return f"[L2] No vault results for: {query}"

        sections = [f"=== VAULT SEARCH: {query[:60]} ==="]
        for i, r in enumerate(results, 1):
            sections.append(f"\n[{i}] {r['file']}:{r['line']}")
            sections.append(r['content'][:300])
        return "\n".join(sections)

    def _scan_protocols(self) -> List[str]:
        """Scan for active protocol files"""
        protocols = []
        for md in self.vault_path.rglob("*.md"):
            if "protocol" in md.stem.lower():
                protocols.append(md.stem)
        return protocols[:10]

    def _find_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """Find notes relevant to query"""
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

    def _search_vault(self, query: str, limit: int = 5) -> List[Dict]:
        """Deep search through vault files"""
        results = []
        keywords = query.lower().split()

        for md in self.vault_path.rglob("*.md"):
            try:
                lines = md.read_text(errors='ignore').splitlines()
                for i, line in enumerate(lines):
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
# Memory Context Provider
# ============================================

class MemoryContextProvider:
    """Provides context from Hermes memory system"""

    def __init__(self):
        self.memory_path = memory_file_path().parent

    def get_l0_memory(self) -> str:
        """Get core memory entries for L0"""
        memory_file = self.memory_path / "memory.json"
        if not memory_file.exists():
            return ""

        try:
            data = json.loads(memory_file.read_text())
            entries = data.get('entries', [])
            if not entries:
                return ""

            lines = ["=== CORE MEMORY ==="]
            for entry in entries:
                content = entry.get('content', '')
                if content:
                    lines.append(f"- {content[:200]}")
            return "\n".join(lines)
        except:
            return ""

    def get_recent_memory(self, days: int = 7) -> str:
        """Get recent memory entries"""
        memory_file = self.memory_path / "memory.json"
        if not memory_file.exists():
            return ""

        try:
            data = json.loads(memory_file.read_text())
            entries = data.get('entries', [])
            cutoff = datetime.now() - timedelta(days=days)

            recent = []
            for entry in entries:
                timestamp = entry.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if dt >= cutoff:
                            recent.append(entry.get('content', ''))
                    except:
                        pass

            if not recent:
                return ""

            lines = ["=== RECENT MEMORY ==="]
            for r in recent[:5]:
                lines.append(f"- {r[:200]}")
            return "\n".join(lines)
        except:
            return ""

# ============================================
# RAG Context Provider
# ============================================

class RAGContextProvider:
    """Provides context from ChromaDB RAG"""

    def __init__(self, rag_path: str):
        self.rag_path = rag_path

    def query(self, question: str, n_results: int = 5) -> str:
        """Query ChromaDB for relevant context"""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=self.rag_path)
            collection = client.get_collection("hermes_vault")
            results = collection.query(
                query_texts=[question],
                n_results=n_results
            )

            docs = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]

            if not docs:
                return f"[RAG] No results for: {question}"

            sections = [f"=== RAG RESULTS: {question[:60]} ==="]
            for i, (doc, meta) in enumerate(zip(docs, metadatas), 1):
                title = meta.get('title', 'Unknown') if meta else 'Unknown'
                sections.append(f"\n[{i}] {title}")
                sections.append(doc[:400])

            return "\n".join(sections)

        except Exception as e:
            return f"[RAG] Error: {e}"

# ============================================
# Session Context Provider
# ============================================

class SessionContextProvider:
    """Provides context from session transcripts"""

    def __init__(self):
        self.sessions_path = sessions_path()

    def get_recent_sessions(self, limit: int = 3) -> str:
        """Get recent session summaries"""
        if not self.sessions_path.exists():
            return ""

        sessions = sorted(self.sessions_path.glob("*.json"), reverse=True)
        if not sessions:
            return ""

        lines = ["=== RECENT SESSIONS ==="]
        for session in sessions[:limit]:
            try:
                data = json.loads(session.read_text())
                summary = data.get('summary', session.stem)
                lines.append(f"- {session.stem}: {summary[:100]}")
            except:
                lines.append(f"- {session.stem}")

        return "\n".join(lines)

# ============================================
# Cron Context Provider
# ============================================

class CronContextProvider:
    """Provides context from cron outputs"""

    def __init__(self):
        self.cron_path = cron_output_path()

    def get_recent_outputs(self, limit: int = 5) -> str:
        """Get recent cron outputs"""
        if not self.cron_path.exists():
            return ""

        outputs = sorted(self.cron_path.glob("*.md"), reverse=True)
        if not outputs:
            return ""

        lines = ["=== RECENT CRON OUTPUTS ==="]
        for output in outputs[:limit]:
            lines.append(f"- {output.stem}")

        return "\n".join(lines)

# ============================================
# Integrated Context System
# ============================================

class IntegratedContextSystem:
    """
    Full three-tier context system with all providers integrated.
    This is the main interface for Hermes to use.
    """

    def __init__(self):
        self.vault = VaultContextProvider(str(vault_path()))
        self.memory = MemoryContextProvider()
        self.rag = RAGContextProvider(str(rag_path()))
        self.sessions = SessionContextProvider()
        self.cron = CronContextProvider()

    def get_l0(self) -> str:
        """L0: Core identity — always loaded"""
        sections = []
        sections.append("=== IDENTITY ===")
        sections.append("Name: Hermes Agent")
        sections.append("Mode: THIELON (contrarian-first, monopoly thinking)")
        sections.append("User: Baked Bread (broke dropout, free/open source)")
        sections.append("")
        sections.append("=== DIRECTIVES ===")
        sections.append("- Question consensus. What do few people agree on?")
        sections.append("- Break problems to first principles.")
        sections.append("- Aim for unique value nobody can copy.")
        sections.append("- Ship fast, iterate faster.")
        sections.append("- Find hidden truths everywhere.")

        # Core memory
        core_mem = self.memory.get_l0_memory()
        if core_mem:
            sections.append("")
            sections.append(core_mem)

        return "\n".join(sections)

    def get_l1(self, task: str = "general") -> str:
        """L1: Active context — session-scoped"""
        sections = []

        # Vault context (protocols + relevant notes)
        vault_ctx = self.vault.get_l1_context(task)
        if vault_ctx:
            sections.append(vault_ctx)

        # Recent memory
        recent_mem = self.memory.get_recent_memory()
        if recent_mem:
            sections.append("")
            sections.append(recent_mem)

        # Recent sessions
        sessions_ctx = self.sessions.get_recent_sessions()
        if sessions_ctx:
            sections.append("")
            sections.append(sessions_ctx)

        # Cron outputs
        cron_ctx = self.cron.get_recent_outputs()
        if cron_ctx:
            sections.append("")
            sections.append(cron_ctx)

        return "\n".join(sections)

    def get_l2(self, query: str) -> str:
        """L2: Deep knowledge — on-demand"""
        sections = []

        # RAG first (semantic search)
        rag_ctx = self.rag.query(query)
        sections.append(rag_ctx)

        # Vault deep search (keyword)
        vault_ctx = self.vault.get_l2_context(query)
        sections.append("")
        sections.append(vault_ctx)

        return "\n".join(sections)

    def get_full_context(self, task: str, include_deep: bool = False) -> str:
        """Get full context for a task"""
        sections = []
        sections.append(self.get_l0())
        sections.append("")
        sections.append(self.get_l1(task))

        if include_deep:
            sections.append("")
            sections.append(self.get_l2(task))

        return "\n".join(sections)

# ============================================
# CLI Interface
# ============================================

if __name__ == "__main__":
    import sys

    ctx = IntegratedContextSystem()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 integration.py l0              # Core identity")
        print("  python3 integration.py l1 [task]       # Active context")
        print("  python3 integration.py l2 <query>      # Deep knowledge")
        print("  python3 integration.py full [task]     # Full context")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "l0":
        print(ctx.get_l0())
    elif cmd == "l1":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "general"
        print(ctx.get_l1(task))
    elif cmd == "l2":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "agent identity"
        print(ctx.get_l2(query))
    elif cmd == "full":
        task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "general"
        print(ctx.get_full_context(task, include_deep=True))
    else:
        print(f"Unknown command: {cmd}")
