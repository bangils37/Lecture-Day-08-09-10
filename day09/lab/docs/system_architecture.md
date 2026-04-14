# System Architecture — Lab Day 09

## 1. Thành phần hệ thống (Component Diagram)

```mermaid
graph TD
    User([User Query]) --> Supervisor{Supervisor Agent}
    
    subgraph "Worker Agents"
        Supervisor -- "retrieval_needed" --> Retrieval[Retrieval Worker]
        Supervisor -- "policy_exception" --> Policy[Policy Tool Worker]
        Supervisor -- "risk_high" --> HITL[Human-in-the-Loop]
    end
    
    subgraph "External Resources"
        Retrieval --> Qdrant[(Qdrant Vector DB)]
        Retrieval --> LocalDocs[(Local Documents)]
        Policy --> MCP[MCP Server]
        MCP --> Tools{Tools: access, ticket}
    end
    
    Retrieval --> Synthesis[Synthesis Worker]
    Policy --> Synthesis
    HITL --> Retrieval
    
    Synthesis --> Output([Final Answer + Citations])
```

## 2. Shared State Management (AgentState)

Hệ thống sử dụng một `TypedDict` duy nhất để truyền dữ liệu qua các nodes trong LangGraph:

- `task`: Query gốc.
- `supervisor_route`: Quyết định điều hướng.
- `retrieved_chunks`: List các đoạn văn bản tìm được.
- `policy_result`: Phân tích chính sách từ worker.
- `mcp_tools_used`: Lịch sử các tool đã gọi qua MCP.
- `history`: Nhật ký các bước xử lý (Annotated với `operator.add`).

## 3. Worker Design

### Retrieval Worker
- **Logic**: Sử dụng Hybrid Search. Ưu tiên vector search với `all-MiniLM-L6-v2`. Nếu gặp lỗi môi trường (locking), tự động chuyển sang keyword-based search trên files vật lý.
- **Output**: Trả về 3-5 chunks có độ liên quan cao nhất kèm theo nguồn (source).

### Policy Tool Worker
- **Logic**: Node này chịu trách nhiệm cho các logic phức tạp. Nó gọi MCP tools như `check_access_permission` hoặc `get_ticket_info` dựa trên phân tích keywords trong query.
- **Output**: `policy_applies` (True/False) và danh sách các `exceptions_found`.

### Synthesis Worker
- **Logic**: Node cuối cùng chịu trách nhiệm tổng hợp. Sử dụng LLM (Gemini 2.0 Flash) với prompt khắt khe về việc trích dẫn nguồn.
- **Grounding**: Chỉ được phép trả lời dựa trên `retrieved_chunks` và `policy_result`.

## 4. MCP Integration

Hệ thống MCP đóng vai trò là "cánh tay nối dài" cho agent, cho phép truy cập vào các hệ thống bên ngoài mà không cần sửa đổi logic cốt lõi của Agent. Node `Policy Tool Worker` đóng vai trò là controller điều phối việc gọi MCP.

---
*Lưu tại: `docs/system_architecture.md`*
