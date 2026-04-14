"""
workers/retrieval.py — Retrieval Worker
Sprint 2: Implement retrieval từ ChromaDB, trả về chunks + sources.

Input (từ AgentState):
    - task: câu hỏi cần retrieve
    - (optional) retrieved_chunks nếu đã có từ trước

Output (vào AgentState):
    - retrieved_chunks: list of {"text", "source", "score", "metadata"}
    - retrieved_sources: list of source filenames
    - worker_io_log: log input/output của worker này

Gọi độc lập để test:
    python workers/retrieval.py
"""

import os
import re
from pathlib import Path

# ─────────────────────────────────────────────
# Worker Contract (xem contracts/worker_contracts.yaml)
# Input:  {"task": str, "top_k": int = 3}
# Output: {"retrieved_chunks": list, "retrieved_sources": list, "error": dict | None}
# ─────────────────────────────────────────────

WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3


def _get_collection():
    """Kết nối ChromaDB collection nếu có."""
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    return client.get_collection("day09_docs")


def _normalize_tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def _score_overlap(query_tokens: set, doc_text: str) -> float:
    if not query_tokens:
        return 0.0
    doc_tokens = _normalize_tokens(doc_text)
    overlap = len(query_tokens.intersection(doc_tokens))
    return round(min(1.0, overlap / max(1, len(query_tokens))), 4)


def _fallback_keyword_search(query: str, top_k: int = DEFAULT_TOP_K) -> list:
    """Fallback retrieval khi Chroma chưa sẵn sàng: tìm theo overlap token trong data/docs."""
    docs_dir = Path("./data/docs")
    if not docs_dir.exists():
        return []

    query_tokens = _normalize_tokens(query)
    ranked = []

    for path in docs_dir.glob("*.txt"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        score = _score_overlap(query_tokens, text)
        if score <= 0:
            continue

        ranked.append(
            {
                "text": text[:1200],
                "source": path.name,
                "score": score,
                "metadata": {"source": path.name, "method": "keyword_fallback"},
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_k]


def retrieve_dense(query: str, top_k: int = DEFAULT_TOP_K) -> list:
    """
    Dense retrieval: embed query → query ChromaDB → trả về top_k chunks.

    Returns:
        list of {"text": str, "source": str, "score": float, "metadata": dict}
    """
    try:
        collection = _get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        chunks = []
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for doc, dist, meta in zip(documents, distances, metadatas):
            metadata = meta or {}
            score = 1.0 - float(dist)
            score = max(0.0, min(1.0, score))
            chunks.append({
                "text": doc,
                "source": metadata.get("source", "unknown"),
                "score": round(score, 4),
                "metadata": metadata,
            })

        if chunks:
            return chunks

        return _fallback_keyword_search(query, top_k)

    except Exception:
        return _fallback_keyword_search(query, top_k)


def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState với retrieved_chunks và retrieved_sources
    """
    task = state.get("task", "")
    top_k = int(state.get("top_k", state.get("retrieval_top_k", DEFAULT_TOP_K)))

    state.setdefault("workers_called", [])
    state.setdefault("history", [])

    state["workers_called"].append(WORKER_NAME)

    # Log worker IO (theo contract)
    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": None,
        "error": None,
    }

    try:
        chunks = retrieve_dense(task, top_k=top_k)

        sources = sorted({c.get("source", "unknown") for c in chunks})

        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources

        worker_io["output"] = {
            "chunks_count": len(chunks),
            "sources": sources,
        }
        state["history"].append(
            f"[{WORKER_NAME}] retrieved {len(chunks)} chunks from {sources}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "RETRIEVAL_FAILED", "reason": str(e)}
        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    # Ghi worker IO vào state để trace
    state.setdefault("worker_io_logs", []).append(worker_io)

    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Retrieval Worker — Standalone Test")
    print("=" * 50)

    test_queries = [
        "SLA ticket P1 là bao lâu?",
        "Điều kiện được hoàn tiền là gì?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        result = run({"task": query})
        chunks = result.get("retrieved_chunks", [])
        print(f"  Retrieved: {len(chunks)} chunks")
        for c in chunks[:2]:
            print(f"    [{c['score']:.3f}] {c['source']}: {c['text'][:80]}...")
        print(f"  Sources: {result.get('retrieved_sources', [])}")

    print("\n✅ retrieval_worker test done.")
