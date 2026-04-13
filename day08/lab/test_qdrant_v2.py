import qdrant_client
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")

print(f"URL: {QDRANT_URL}")
try:
    client = qdrant_client.QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print(f"Client: {client}")
    print(f"Type: {type(client)}")
    print(f"Dir has search: {'search' in dir(client)}")
    if 'search' not in dir(client):
        print("Searching for similar methods...")
        for attr in dir(client):
            if 'search' in attr.lower() or 'query' in attr.lower():
                print(f"  Found: {attr}")
except Exception as e:
    print(f"Initialization failed: {e}")
