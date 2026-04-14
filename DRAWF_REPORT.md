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

| Vai trò | Trách nhiệm chính | Sprint lead | Phân công |
|---------|------------------|------------|-----------|
| **Supervisor Owner** | graph.py, routing logic, state management | 1 | Bùi Trọng Anh |
| **Worker Owner** | retrieval.py, policy_tool.py, synthesis.py, contracts | 2 | Nguyễn Bằng Anh |
| **MCP Owner** | mcp_server.py, MCP integration trong policy_tool | 3 | Đỗ Thị Thùy Trang |
| **Trace & Docs Owner** | eval_trace.py, 3 doc templates, group_report | 4 | Bùi Trọng Anh |
