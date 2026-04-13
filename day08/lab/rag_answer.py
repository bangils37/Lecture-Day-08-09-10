"""Sprint 2 baseline RAG: Qdrant retrieval + LangChain Gemini generation."""

import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from index import QDRANT_COLLECTION, QDRANT_DB_DIR, _get_qdrant_client, get_embedding

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

TOP_K_SEARCH = int(os.getenv("TOP_K_SEARCH", "8"))
TOP_K_SELECT = int(os.getenv("TOP_K_SELECT", "3"))
MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.25"))

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite-preview")

ABSTAIN_MESSAGE = "Khong du du lieu de tra loi tu tai lieu hien co."


# =============================================================================
# RETRIEVAL (SPRINT 2)
# =============================================================================


def retrieve_qdrant(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    """Retrieve chunks from Qdrant using the same embedding model as indexing."""
    client = _get_qdrant_client(QDRANT_DB_DIR)
    query_vector = get_embedding(query)

    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )
    results = getattr(response, "points", response)

    hits: List[Dict[str, Any]] = []
    for item in results:
        payload = item.payload or {}
        text = payload.get("text", "")
        if not text:
            continue

        metadata = {k: v for k, v in payload.items() if k != "text"}
        hits.append(
            {
                "text": text,
                "metadata": metadata,
                "score": float(getattr(item, "score", 0.0)),
            }
        )
    return hits


# Alias giu lai de tuong thich ten ham cu.
def retrieve_dense(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    return retrieve_qdrant(query, top_k=top_k)


# =============================================================================
# PROMPT + LLM (SPRINT 2)
# =============================================================================


def build_context_block(chunks: List[Dict[str, Any]]) -> str:
    """Pack retrieved chunks into a numbered context block for citation."""
    context_parts: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        score = chunk.get("score", 0.0)
        text = chunk.get("text", "")

        header = f"[{i}] {source}"
        if section:
            header += f" | {section}"
        header += f" | score={score:.3f}"

        context_parts.append(f"{header}\n{text}")

    return "\n\n".join(context_parts)


def _build_chain() -> Any:
    """Build LangChain chain: Prompt -> Gemini -> String output parser."""
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Thieu GOOGLE_API_KEY. Hay cap nhat file .env truoc khi chay Sprint 2.")

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=0,
        google_api_key=api_key,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Ban la tro ly noi bo. Chi duoc tra loi bang thong tin trong context. "
                "Neu context khong du thi tra loi dung cau: Khong du du lieu de tra loi tu tai lieu hien co. "
                "Khi tra loi duoc, phai kem citation dang [1], [2] theo doan context.",
            ),
            (
                "human",
                "Cau hoi:\n{query}\n\n"
                "Context:\n{context}\n\n"
                "Tra loi ngan gon, ro rang, dung ngon ngu cua cau hoi.",
            ),
        ]
    )

    return prompt | llm | StrOutputParser()


# =============================================================================
# RAG PIPELINE (SPRINT 2)
# =============================================================================


def rag_answer(
    query: str,
    top_k_search: int = TOP_K_SEARCH,
    top_k_select: int = TOP_K_SELECT,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Baseline RAG pipeline for Sprint 2."""
    candidates = retrieve_qdrant(query, top_k=top_k_search)

    if verbose:
        print(f"[RAG] Retrieved: {len(candidates)} chunks")

    if not candidates:
        return {
            "query": query,
            "answer": ABSTAIN_MESSAGE,
            "sources": [],
            "chunks_used": [],
            "config": {
                "top_k_search": top_k_search,
                "top_k_select": top_k_select,
                "min_relevance_score": MIN_RELEVANCE_SCORE,
                "llm_model": LLM_MODEL,
            },
        }

    selected = candidates[:top_k_select]
    best_score = max(chunk.get("score", 0.0) for chunk in selected)

    if best_score < MIN_RELEVANCE_SCORE:
        return {
            "query": query,
            "answer": ABSTAIN_MESSAGE,
            "sources": [],
            "chunks_used": selected,
            "config": {
                "top_k_search": top_k_search,
                "top_k_select": top_k_select,
                "min_relevance_score": MIN_RELEVANCE_SCORE,
                "llm_model": LLM_MODEL,
            },
        }

    context_block = build_context_block(selected)
    chain = _build_chain()
    answer = chain.invoke({"query": query, "context": context_block}).strip()

    sources = sorted(
        {
            chunk.get("metadata", {}).get("source", "unknown")
            for chunk in selected
            if chunk.get("metadata", {}).get("source")
        }
    )

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "chunks_used": selected,
        "config": {
            "top_k_search": top_k_search,
            "top_k_select": top_k_select,
            "min_relevance_score": MIN_RELEVANCE_SCORE,
            "llm_model": LLM_MODEL,
        },
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 2: Baseline RAG (Qdrant + LangChain + Gemini)")
    print("=" * 60)

    test_queries = [
        "SLA xu ly ticket P1 la bao lau?",
        "Khach hang co the yeu cau hoan tien trong bao nhieu ngay?",
        "Ai phai phe duyet de cap quyen Level 3?",
        "Lich thi dau bong da World Cup 2030 la gi?",
    ]

    for query in test_queries:
        print("\n" + "-" * 60)
        print(f"Query: {query}")
        try:
            result = rag_answer(query, verbose=True)
            print(f"Answer: {result['answer']}")
            print(f"Sources: {result['sources']}")
        except Exception as exc:
            print(f"Loi: {exc}")
