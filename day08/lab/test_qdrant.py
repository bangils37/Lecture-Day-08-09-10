from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")

print(f"URL: {QDRANT_URL}")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
print(f"Client type: {type(client)}")
print(f"Has search: {hasattr(client, 'search')}")
print(f"Dir: {dir(client)}")
