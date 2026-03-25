"""
RAG Integration — Connects Three-Tier Context with ChromaDB

This is the "filesystem mount" for L2 context.
When you need deep knowledge, this module queries ChromaDB
and returns only the relevant snippets.
"""

from pathlib import Path

from hermes_paths import rag_path as default_rag_path

def rag_query(query: str, n_results: int = 5) -> str:
    """Query ChromaDB for relevant context"""
    try:
        import chromadb
        rag_db_path = str(default_rag_path())
        client = chromadb.PersistentClient(path=rag_db_path)
        collection = client.get_collection("hermes_vault")
        results = collection.query(query_texts=[query], n_results=n_results)

        docs = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]

        if not docs:
            return f"[RAG] No results for: {query}"

        sections = [f"=== RAG RESULTS: {query[:60]} ==="]
        for i, (doc, meta) in enumerate(zip(docs, metadatas), 1):
            title = meta.get('title', 'Unknown') if meta else 'Unknown'
            sections.append(f"\n[{i}] {title}")
            sections.append(doc[:400])

        return "\n".join(sections)

    except Exception as e:
        return f"[RAG] Error: {e}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 rag_integration.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(rag_query(query))
