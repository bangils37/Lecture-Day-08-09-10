"""
setup_db.py — Initialize ChromaDB with Day 09 documents
Chạy 1 lần trước Sprint 2 để build vector index.

Usage:
    python setup_db.py
"""

import os
from pathlib import Path


def setup_chroma_db(docs_dir: str = "./data/docs", db_path: str = "./chroma_db"):
    """
    Initialize ChromaDB with documents from docs_dir.
    
    Args:
        docs_dir: Directory containing .txt files to index
        db_path: Path where ChromaDB persist folder will be created
    """
    import chromadb
    from sentence_transformers import SentenceTransformer

    print("=" * 60)
    print("ChromaDB Setup — Day 09 Lab")
    print("=" * 60)

    # Initialize client
    client = chromadb.PersistentClient(path=db_path)
    
    # Create collection
    collection = client.get_or_create_collection(
        "day09_docs",
        metadata={"hnsw:space": "cosine"}
    )
    print(f"✓ Collection 'day09_docs' created/loaded")

    # Load embedding model
    print("⏳ Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✓ Model loaded")

    # Read and index documents
    docs_path = Path(docs_dir)
    doc_files = sorted([f for f in docs_path.glob("*.txt")])
    
    if not doc_files:
        print(f"⚠️  No .txt files found in {docs_dir}")
        return

    print(f"📁 Found {len(doc_files)} documents:")
    
    for doc_file in doc_files:
        with open(doc_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        doc_name = doc_file.name
        
        # Split into chunks (simple: every ~500 chars)
        chunk_size = 500
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        # Embed and add to collection
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                embedding = model.encode(chunk)
                collection.add(
                    ids=[f"{doc_name}_{i}"],
                    documents=[chunk],
                    embeddings=[embedding.tolist()],
                    metadatas=[{"source": doc_name, "chunk_id": i}]
                )
        
        print(f"  ✓ {doc_name}: {len(chunks)} chunks indexed")
    
    print(f"\n✅ ChromaDB setup complete!")
    print(f"   → Collection: day09_docs")
    print(f"   → Path: {db_path}")
    print(f"   → Ready for Sprint 2 workers")


if __name__ == "__main__":
    setup_chroma_db()
