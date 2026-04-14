"""Quick test for retrieval worker"""
from workers.retrieval import run as retrieval_run

test_queries = [
    "SLA ticket P1 là bao lâu?",
    "Hoàn tiền? Flash Sale được không?",
    "Cấp quyền access Level 3 thế nào?"
]

for query in test_queries:
    print(f"\n▶ Query: {query}")
    state = {'task': query, 'history': []}
    result = retrieval_run(state)
    chunks = result.get('retrieved_chunks', [])
    print(f"  Chunks found: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[:2]):
        source = chunk.get('source', 'unknown')
        score = chunk.get('score', 0)
        text = chunk.get('text', '')[:80]
        print(f"  [{i}] {source} (score: {score}) - {text}...")
