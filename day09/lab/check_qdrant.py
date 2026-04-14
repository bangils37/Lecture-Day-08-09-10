import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "day09_docs"

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

try:
    count = client.count(collection_name=COLLECTION_NAME).count
    print(f"Collection {COLLECTION_NAME} has {count} points.")
except Exception as e:
    print(f"Error checking collection: {e}")
