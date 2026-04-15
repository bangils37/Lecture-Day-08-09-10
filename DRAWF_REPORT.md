# Báo cáo nháp
Dùng để các thành viên trong nhóm  trò chuyện, thống nhất và notes. Chức năng tương tự Work-logging.

## Thống nhất TechStack

* LLM: gemini-3.1-flash-lite-preview
* Embedding: SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
* Vector DB: Qdrant
* Reranker: (Không dùng)
* Framework: LangChain - LangGraph, FastAPI, Uvicorn
* Monitoring: LangSmith

## Phân vai

| Vai | Trách nhiệm | Sprint chính | Phân công |
|-----|-------------|----------------|
| **Ingestion Owner** | raw paths, logging, manifest | 1 | Bùi Trọng Anh
| **Cleaning / Quality Owner** | `cleaning_rules.py`, `expectations.py`, quarantine | 1–3 | Nguyễn Bằng Anh
| **Embed Owner** | Chroma collection, idempotency, eval | 2–3 | Đỗ Thị Thùy Trang
| **Monitoring / Docs Owner** | freshness, runbook, 3 docs, group report | 4 | Bùi Trọng Anh

