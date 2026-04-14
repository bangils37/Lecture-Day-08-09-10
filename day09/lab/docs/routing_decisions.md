# Routing Decisions Log — Lab Day 09

**Nhóm:** Antigravity Force  
**Ngày:** 14/04/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).

---

## Routing Decision #1

**Task đầu vào:**
> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `default route`  
**MCP tools được gọi:** None  
**Workers called sequence:** `retrieval_worker` -> `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): SLA xử lý ticket P1 bao gồm: phản hồi trong 15 phút và giải quyết trong 4 giờ [1].
- confidence: 0.3
- Correct routing? Yes

**Nhận xét:** Supervisor nhận diện chính xác đây là câu hỏi về thông tin SLA chuẩn, không yêu cầu logic phức tạp hay kiểm tra quyền, nên route thẳng tới retrieval.

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword`  
**MCP tools được gọi:** None (Policy logic internal)  
**Workers called sequence:** `policy_tool_worker` -> `retrieval_worker` -> `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Tôi không tìm thấy thông tin cụ thể trong tài liệu nội bộ.
- confidence: 0.3
- Correct routing? Yes

**Nhận xét:** Vì query chứa từ khóa "hoàn tiền" (refund), Supervisor đã route sang Policy Tool Worker để kiểm tra các ngoại lệ (như Flash Sale). Mặc dù kết quả là Abstain do tài liệu thiếu thông tin ngày, nhưng quy trình routing là chính xác.

---

## Routing Decision #3

**Task đầu vào:**
> Ai phải phê duyệt để cấp quyền Level 3?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword`  
**MCP tools được gọi:** `check_access_permission`  
**Workers called sequence:** `policy_tool_worker` -> `retrieval_worker` -> `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Để cấp quyền Level 3, cần có sự phê duyệt của IT Security và Line Manager [1].
- confidence: 0.3
- Correct routing? Yes

**Nhận xét:** Đây là case tiêu biểu cho việc sử dụng MCP. Supervisor route sang Policy Tool do có từ khóa "cấp quyền". Policy Tool sau đó gọi MCP tool `check_access_permission` để xác định danh sách người phê duyệt từ hệ thống quản lý quyền.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 37 | 55% |
| policy_tool_worker | 30 | 44% |
| human_review | 0 | 0% |

### Routing Accuracy

- Câu route đúng: 15 / 15
- Câu route sai: 0
- Câu trigger HITL: 4 (cho các mã lỗi ERR)

### Lesson Learned về Routing

1. **Keyword Power**: Keyword matching đơn giản nhưng cực kỳ hiệu quả cho giai đoạn khởi đầu (cold start) của hệ thống RAG trước khi có đủ dữ liệu để train LLM classifier.
2. **Hybrid Advantage**: Việc route sang Policy Tool giúp tách biệt logic nghiệp vụ (business rules) khỏi logic tìm kiếm thông tin thuần túy, làm cho Synthesis worker hoạt động grounding tốt hơn.

---
*Lưu tại: `docs/routing_decisions.md`*
