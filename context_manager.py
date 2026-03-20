"""
Hermes Three-Tier Context Manager
Inspired by OpenViking's filesystem paradigm for agent context.

L0: Core Identity (always loaded)
L1: Active Context (session-scoped)
L2: Deep Knowledge (on-demand)
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ============================================
# Context Tiers
# ============================================

@dataclass
class ContextItem:
    """Single piece of context with metadata"""
    path: str
    content: str
    tier: str  # L0, L1, L2
    relevance_score: float
    token_estimate: int
    last_accessed: str
    access_count: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            'path': self.path,
            'tier': self.tier,
            'relevance_score': self.relevance_score,
            'token_estimate': self.token_estimate,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'tags': self.tags,
        }

class ContextManager:
    """Three-tier context manager for Hermes"""

    def __init__(self, vault_path: str, rag_path: str):
        self.vault_path = Path(vault_path)
        self.rag_path = Path(rag_path)
        self.context_index = {}
        self.session_context = []

        # Tier configurations
        self.tier_config = {
            'L0': {
                'max_tokens': 3000,
                'always_load': True,
                'sources': ['memory', 'identity', 'protocols'],
            },
            'L1': {
                'max_tokens': 10000,
                'always_load': False,
                'sources': ['vault', 'skills', 'active_tasks', 'recent_sessions'],
            },
            'L2': {
                'max_tokens': 50000,
                'always_load': False,
                'sources': ['chromadb', 'full_vault', 'external', 'historical'],
            },
        }

    def load_tier(self, tier: str, task: str = None) -> str:
        """Load context for a specific tier"""
        if tier == 'L0':
            return self._load_l0()
        elif tier == 'L1':
            return self._load_l1(task)
        elif tier == 'L2':
            return self._load_l2(task)
        else:
            raise ValueError(f"Unknown tier: {tier}")

    def _load_l0(self) -> str:
        """L0: Core identity — always loaded"""
        sections = []

        # Agent identity
        sections.append("=== HERMES IDENTITY ===")
        sections.append("Name: Hermes Agent")
        sections.append("Mode: THIELON (contrarian-first, monopoly thinking)")
        sections.append("Platforms: Telegram, local")
        sections.append("User: Baked Bread (broke dropout, prefers free/open source)")

        # Active protocols
        sections.append("\n=== ACTIVE PROTOCOLS ===")
        protocols = self._scan_active_protocols()
        for p in protocols:
            sections.append(f"- {p}")

        # Core memory
        sections.append("\n=== CORE MEMORY ===")
        memory = self._load_memory()
        for entry in memory:
            sections.append(f"- {entry}")

        return "\n".join(sections)

    def _load_l1(self, task: str = None) -> str:
        """L1: Active context — session-scoped"""
        sections = []

        # Current task context
        if task:
            sections.append(f"=== CURRENT TASK: {task} ===")
            relevant_notes = self._find_relevant_notes(task, limit=5)
            for note in relevant_notes:
                sections.append(f"\n--- {note['title']} ---")
                sections.append(note['preview'])

        # Active skills
        sections.append("\n=== ACTIVE SKILLS ===")
        skills = self._load_active_skills()
        for skill in skills:
            sections.append(f"- {skill}")

        # Recent session context
        sections.append("\n=== RECENT CONTEXT ===")
        recent = self._load_recent_sessions(limit=3)
        for session in recent:
            sections.append(f"- {session}")

        # Active cron outputs
        sections.append("\n=== ACTIVE CRON OUTPUTS ===")
        cron_outputs = self._load_cron_outputs()
        for output in cron_outputs:
            sections.append(f"- {output}")

        return "\n".join(sections)

    def _load_l2(self, task: str = None) -> str:
        """L2: Deep knowledge — on-demand retrieval"""
        if not task:
            return "[L2] No task specified — use RAG query for specific retrieval"

        # ChromaDB RAG query
        results = self._rag_query(task, n_results=10)

        sections = []
        sections.append(f"=== DEEP KNOWLEDGE: {task} ===")

        for i, result in enumerate(results, 1):
            sections.append(f"\n--- Result {i}: {result.get('title', 'Unknown')} ---")
            sections.append(f"Relevance: {result.get('distance', 'N/A')}")
            sections.append(result.get('content', '')[:500])

        return "\n".join(sections)

    def query(self, question: str, tier: str = 'L1') -> str:
        """Query context with smart tier selection"""
        # Start with L1
        context = self.load_tier(tier, task=question)

        # If insufficient, escalate to L2
        if tier == 'L1' and self._needs_deeper_context(question):
            context += "\n\n" + self.load_tier('L2', task=question)

        return context

    def save_context_snapshot(self, session_id: str, context: str):
        """Save context snapshot for future L2 retrieval"""
        snapshot_path = self.vault_path / "context-snapshots" / f"{session_id}.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        snapshot = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'token_estimate': self._estimate_tokens(context),
            'content_hash': hashlib.md5(context.encode()).hexdigest(),
            'content': context,
        }

        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)

    # ============================================
    # Helper Methods
    # ============================================

    def _scan_active_protocols(self) -> List[str]:
        """Scan for active protocols"""
        protocols = []
        protocols_path = self.vault_path / "protocols"
        if protocols_path.exists():
            for f in protocols_path.glob("*.md"):
                protocols.append(f.stem)
        return protocols or [
            "THIELON MODE (contrarian-first)",
            "LUCKEY PATRIOTIC PROTOCOL (7-day defense rotation)",
            "ANTI-MIMESIS PROTOCOL (Girard theory)",
            "QUAD HELIX ENGINE (Elon+Thiel+Andreessen+Luckey)",
            "SECRETS HUNTING v3.0 (multiplicative scoring)",
        ]

    def _load_memory(self) -> List[str]:
        """Load core memory entries"""
        memory_file = Path.home() / ".hermes" / "memory" / "memory.json"
        if memory_file.exists():
            with open(memory_file) as f:
                data = json.load(f)
                return [entry.get('content', '') for entry in data.get('entries', [])]
        return []

    def _find_relevant_notes(self, query: str, limit: int = 5) -> List[Dict]:
        """Find relevant vault notes for a query"""
        results = []
        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text()
                if any(word.lower() in content.lower() for word in query.split()):
                    results.append({
                        'title': md_file.stem,
                        'path': str(md_file),
                        'preview': content[:300],
                    })
                    if len(results) >= limit:
                        break
            except:
                continue
        return results

    def _load_active_skills(self) -> List[str]:
        """Load active skills"""
        skills_path = Path.home() / ".hermes" / "skills"
        if skills_path.exists():
            return [f.parent.name for f in skills_path.rglob("SKILL.md")][:10]
        return []

    def _load_recent_sessions(self, limit: int = 3) -> List[str]:
        """Load recent session summaries"""
        sessions_path = Path.home() / ".hermes" / "sessions"
        if sessions_path.exists():
            sessions = sorted(sessions_path.glob("*.json"), reverse=True)
            return [s.stem for s in sessions[:limit]]
        return []

    def _load_cron_outputs(self) -> List[str]:
        """Load recent cron outputs"""
        cron_path = Path.home() / ".hermes" / "cron" / "output"
        if cron_path.exists():
            outputs = sorted(cron_path.glob("*.md"), reverse=True)
            return [o.stem for o in outputs[:5]]
        return []

    def _rag_query(self, query: str, n_results: int = 10) -> List[Dict]:
        """Query ChromaDB for relevant context"""
        # This would use the actual ChromaDB client
        # For now, return simulated results
        return [
            {
                'title': f'RAG Result {i}',
                'content': f'Content related to: {query}',
                'distance': 0.1 * i,
            }
            for i in range(n_results)
        ]

    def _needs_deeper_context(self, question: str) -> bool:
        """Determine if L2 context is needed"""
        # Simple heuristic: if question is complex or references specific topics
        complex_indicators = [
            'how does', 'explain', 'compare', 'analyze',
            'what is the relationship', 'why does', 'research',
        ]
        return any(indicator in question.lower() for indicator in complex_indicators)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text.split()) * 1.3  # ~1.3 tokens per word

# ============================================
# CLI Interface
# ============================================

def main():
    import sys

    vault_path = os.path.expanduser("~/obsidian-hermes-vault")
    rag_path = os.path.expanduser("~/hermes-rag-db")

    manager = ContextManager(vault_path, rag_path)

    if len(sys.argv) < 2:
        print("Usage: python3 context_manager.py <command> [args]")
        print("Commands:")
        print("  load --tier L0|L1|L2 [--task <task>]")
        print("  query <question> [--tier L1]")
        print("  save --session <id>")
        return

    command = sys.argv[1]

    if command == "load":
        tier = "L1"
        task = None
        if "--tier" in sys.argv:
            tier = sys.argv[sys.argv.index("--tier") + 1]
        if "--task" in sys.argv:
            task = sys.argv[sys.argv.index("--task") + 1]

        context = manager.load_tier(tier, task)
        print(context)

    elif command == "query":
        question = " ".join(sys.argv[2:])
        tier = "L1"
        if "--tier" in sys.argv:
            idx = sys.argv.index("--tier")
            tier = sys.argv[idx + 1]
            question = " ".join(sys.argv[2:idx])

        context = manager.query(question, tier)
        print(context)

    elif command == "save":
        if "--session" in sys.argv:
            session_id = sys.argv[sys.argv.index("--session") + 1]
            context = manager.load_tier("L1")
            manager.save_context_snapshot(session_id, context)
            print(f"Context snapshot saved for session: {session_id}")

if __name__ == "__main__":
    main()
