"""
Vault Integration — Connects Three-Tier Context with Obsidian Vault

This is the "filesystem mount" for L1 context.
When you need active context, this module scans the vault
for protocols, recent notes, and task-relevant content.
"""

from pathlib import Path
from datetime import datetime

from hermes_paths import vault_path as default_vault_path

def scan_active_protocols(vault_path: str = None) -> list:
    """Scan vault for active protocol files"""
    if vault_path is None:
        vault_path = str(default_vault_path())

    vault = Path(vault_path)
    protocols = []

    for md in vault.rglob("*.md"):
        if "protocol" in md.stem.lower():
            protocols.append({
                'name': md.stem,
                'path': str(md),
                'modified': datetime.fromtimestamp(md.stat().st_mtime).isoformat(),
            })

    # Sort by modification time (most recent first)
    protocols.sort(key=lambda x: x['modified'], reverse=True)
    return protocols[:10]

def find_relevant_notes(query: str, vault_path: str = None, limit: int = 5) -> list:
    """Find vault notes relevant to a query"""
    if vault_path is None:
        vault_path = str(default_vault_path())

    vault = Path(vault_path)
    results = []
    keywords = query.lower().split()

    for md in vault.rglob("*.md"):
        try:
            content = md.read_text(errors='ignore')
            score = sum(1 for kw in keywords if kw in content.lower())
            if score > 0:
                results.append({
                    'title': md.stem,
                    'path': str(md),
                    'score': score,
                    'preview': content[:300],
                })
        except:
            continue

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 vault_integration.py protocols")
        print("  python3 vault_integration.py search <query>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "protocols":
        protocols = scan_active_protocols()
        print("=== ACTIVE PROTOCOLS ===")
        for p in protocols:
            print(f"- {p['name']} (modified: {p['modified']})")

    elif cmd == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "agent identity"
        results = find_relevant_notes(query)
        print(f"=== VAULT SEARCH: {query} ===")
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] {r['title']} (score: {r['score']})")
            print(r['preview'][:200])

    else:
        print(f"Unknown command: {cmd}")
