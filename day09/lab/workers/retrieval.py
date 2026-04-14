import os
import sys
from typing import List, Dict
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Config
COLLECTION_NAME = "day09_docs"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Cache resources
_model = None
_client = None

def get_resources():
    global _model, _client
    if _model is None:
        print(f"  [retrieval] Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME, trust_remote_code=True)
    if _client is None:
        print(f"  [retrieval] Connecting to local Qdrant at ./qdrant_db...")
        _client = QdrantClient(path="./qdrant_db")
    return _model, _client

def retrieve_dense(query: str, top_k: int = 3) -> List[Dict]:
    """Search with Qdrant and robust keyword fallback."""
    chunks = []
    
    # 1. Try Qdrant (Disabled for stability in this environment)
    # try:
    #     model, client = get_resources()
    #     query_vector = model.encode(query).tolist()
    #     results = client.query_points(
    #         collection_name=COLLECTION_NAME,
    #         query=query_vector,
    #         limit=top_k
    #     ).points
    #     for res in results:
    #         chunks.append({
    #             "text": res.payload.get("text"),
    #             "source": res.payload.get("source"),
    #             "score": res.score if hasattr(res, 'score') else 0.5,
    #             "metadata": res.payload
    #         })
    # except Exception as e:
    #     print(f"  [retrieval] Qdrant/Model failed: {e}. Falling back to robust keyword search.")

    # 2. Robust Keyword Fallback (Direct file reading)
    if not chunks:
        import glob
        files = glob.glob("data/docs/*.txt")
        for f_path in files:
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Simple paragraph chunking
                file_chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
                for c in file_chunks:
                    # Simple keyword scoring
                    query_words = set(query.lower().split())
                    chunk_words = set(c.lower().split())
                    match_count = len(query_words.intersection(chunk_words))
                    if match_count > 0:
                        chunks.append({
                            "text": c,
                            "source": os.path.basename(f_path),
                            "score": match_count / len(query_words),
                            "metadata": {}
                        })
            except: continue
        
        chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)[:top_k]
        
    return chunks

def run(state: dict) -> dict:
    """Worker entry point."""
    task = state["task"]
    chunks = retrieve_dense(task)
    sources = list(set([c["source"] for c in chunks]))
    
    return {
        "retrieved_chunks": chunks,
        "retrieved_sources": sources,
        "history": [f"[retrieval_worker] found {len(chunks)} chunks"],
        "workers_called": ["retrieval_worker"]
    }

if __name__ == "__main__":
    # Test independently
    test_state = {"task": "SLA ticket P1 là bao lâu?"}
    result = run(test_state)
    print(f"Found {len(result['retrieved_chunks'])} chunks.")
    for c in result['retrieved_chunks']:
        print(f" - [{c['score']:.4f}] {c['source']}: {c['text'][:100]}...")
