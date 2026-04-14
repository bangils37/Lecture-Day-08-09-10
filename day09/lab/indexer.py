import os
import glob
import json
from datetime import datetime
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

load_dotenv()

# Config
COLLECTION_NAME = "day09_docs"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

def index_docs():
    # Initialize embedding model
    print(f"DEBUG: Starting index_docs")
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME, trust_remote_code=True)
        print(f"DEBUG: Model loaded successfully")
    except Exception as e:
        print(f"DEBUG: Error loading model: {e}")
        return
    
    # Initialize Qdrant client (Local Mode to avoid network issues)
    print(f"Connecting to local Qdrant at ./qdrant_db...")
    try:
        client = QdrantClient(path="./qdrant_db")
        print(f"DEBUG: Connected to local Qdrant")
    except Exception as e:
        print(f"DEBUG: Error connecting to Qdrant: {e}")
        return
    
    # Create collection if it doesn't exist
    vector_size = model.get_sentence_embedding_dimension()
    print(f"Vector size: {vector_size}")
    
    try:
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        return

    if not exists:
        print(f"Creating collection: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
    else:
        print(f"Collection {COLLECTION_NAME} already exists.")
    
    # Load and index documents
    docs_path = "data/docs/*.txt"
    files = glob.glob(docs_path)
    
    if not files:
        print("No documents found in data/docs/", flush=True)
        return

    points = []
    idx = 1
    for file_path in files:
        file_name = os.path.basename(file_path)
        print(f"Processing: {file_name}", flush=True)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Chunking by paragraph
        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
        
        for chunk in chunks:
            embedding = model.encode(chunk).tolist()
            points.append(models.PointStruct(
                id=idx,
                vector=embedding,
                payload={
                    "text": chunk,
                    "source": file_name,
                    "timestamp": datetime.now().isoformat()
                }
            ))
            idx += 1
            
    # Upload points
    if points:
        print(f"Uploading {len(points)} points to Qdrant...", flush=True)
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print("Indexing complete.", flush=True)
    else:
        print("No points to upload.")

if __name__ == "__main__":
    index_docs()
