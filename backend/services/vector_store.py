"""
Vector Store Service — ChromaDB with lightweight fallback.
If chromadb is not installed, falls back to an in-memory list-based store.
"""
from typing import List, Dict, Any

# ─── Try to import ChromaDB ───────────────────────────────────────────────────
try:
    import chromadb
    from chromadb.config import Settings

    _client = chromadb.PersistentClient(path="./chroma_store")
    _collection = _client.get_or_create_collection("scientific_docs")
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    _collection = None
    print("[VectorStore] ChromaDB not installed. Using in-memory fallback.")


# ─── In-memory fallback ───────────────────────────────────────────────────────
_memory_store: List[Dict[str, Any]] = []


def add_documents(docs: List[str], metadatas: List[dict] = None, ids: List[str] = None):
    """Add documents to the vector store."""
    if CHROMA_AVAILABLE:
        _collection.add(
            documents=docs,
            metadatas=metadatas or [{} for _ in docs],
            ids=ids or [str(i) for i in range(len(docs))],
        )
    else:
        for i, doc in enumerate(docs):
            _memory_store.append({
                "id": ids[i] if ids else str(i),
                "text": doc,
                "metadata": metadatas[i] if metadatas else {},
            })


def query_documents(query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """Query the vector store for relevant documents."""
    if CHROMA_AVAILABLE:
        results = _collection.query(query_texts=[query_text], n_results=n_results)
        return [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(
                results["documents"][0],
                results["metadatas"][0],
            )
        ]
    else:
        # Simple keyword fallback: return docs containing any query word
        words = query_text.lower().split()
        matches = [
            d for d in _memory_store
            if any(w in d["text"].lower() for w in words)
        ]
        return matches[:n_results] if matches else [
            {"text": "No matching documents found in knowledge base.", "metadata": {}}
        ]


def get_store_info() -> dict:
    return {
        "backend": "chromadb" if CHROMA_AVAILABLE else "in-memory",
        "document_count": len(_collection.get()["ids"]) if CHROMA_AVAILABLE else len(_memory_store),
    }
