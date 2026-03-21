# Hermes Three-Tier Context System

[![GitHub](https://img.shields.io/badge/GitHub-000000?logo=github)](https://github.com/thielon-apps/hermes-context-system)
[![License](https://img.shields.io/github/license/thielon-apps/hermes-context-system)](https://github.com/thielon-apps/hermes-context-system/blob/main/LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/thielon-apps/hermes-context-system)](https://github.com/thielon-apps/hermes-context-system/commits/main)

Inspired by OpenViking's (ByteDance) context database for agents.

## The Core Insight

Agents burn tokens on irrelevant context. The fix: load context in tiers based on relevance.

## Three-Tier Architecture

### L0: Core Identity (Always Loaded)
- Agent identity, personality, core directives
- User preferences and profile
- Active protocols and frameworks
- **Size**: ~2K tokens
- **Loading**: Every session, no exceptions

### L1: Active Context (Session-Scoped)
- Current project files and task state
- Recent conversation context
- Relevant vault notes (RAG-retrieved)
- Active cron job outputs
- **Size**: ~8K tokens
- **Loading**: Smart retrieval based on current task

### L2: Deep Knowledge (On-Demand)
- Full vault notes (35+ indexed in ChromaDB)
- Historical session transcripts
- External research (web, arXiv, etc.)
- Skill definitions and procedures
- **Size**: Unlimited (queried, not loaded)
- **Loading**: Only when explicitly needed or RAG-retrieved

## Token Savings

| Approach | Tokens per Session | Notes |
|----------|-------------------|-------|
| Naive (load everything) | ~50K | Everything in context |
| Three-tier | ~10K | 80% reduction |
| Three-tier + RAG | ~12K | Better quality, still 76% savings |

## Implementation

```bash
# Core system
python3 context_manager.py load --tier L0
python3 context_manager.py load --tier L1 --task "agent identity research"
python3 context_manager.py query --tier L2 --query "EigenTrust reputation"
```

## Integration Points

1. **ChromaDB RAG** (`~/hermes-rag-db/`) — L2 retrieval
2. **Obsidian Vault** (`~/obsidian-hermes-vault/`) — L1/L2 source
3. **Memory System** (~/.hermes/memory/) — L0 core
4. **Session Transcripts** — L2 historical context
5. **Skills System** (~/.hermes/skills/) — L1 active skills
