# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Day09-Team  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Bùi Trọng Anh | Supervisor Owner, Trace & Docs Owner | tronganhsl93@gmail.com |
| Nguyễn Bằng Anh | Worker Owner | 26ai.anhnb@vinuni.edu.vn |
| Đỗ Thị Thùy Trang | MCP Owner | 26ai.trangdtt@vinuni.edu.vn |

**Ngày nộp:** 14-04-2026  
**Repo:** [Lecture-Day-08-09-10/day09/lab](https://github.com/bangils37/Lecture-Day-08-09-10.git)

---

## 1. Kiến trúc nhóm đã xây dựng

Nhóm triển khai mô hình Supervisor-Worker trên LangGraph với 4 node chính: `supervisor`, `retrieval_worker`, `policy_tool_worker`, `synthesis_worker`, và 1 node phụ `human_review` cho tình huống rủi ro cao. Luồng chạy thực tế: Input -> supervisor -> (retrieval hoặc policy_tool hoặc human_review) -> retrieval -> synthesis -> END.  

Shared state được chuẩn hóa trong `AgentState` (file `graph.py`) gồm các trường chính: `task`, `supervisor_route`, `route_reason`, `risk_high`, `needs_tool`, `retrieved_chunks`, `policy_result`, `mcp_tools_used`, `workers_called`, `final_answer`, `confidence`, `latency_ms`. Việc giữ state tập trung giúp trace rõ ràng và dễ replay từng run.

Routing logic cốt lõi dùng rule-based keyword + risk flag:
- Nhóm từ khóa policy/access (`refund`, `hoàn tiền`, `cấp quyền`, `level 3`) -> `policy_tool_worker`.
- Nhóm từ khóa rủi ro (`khẩn cấp`, `2am`, `err-`) -> bật `risk_high`.
- Nếu có `err-` + `risk_high` -> `human_review` trước khi quay lại retrieval.

MCP tools đã tích hợp trong `mcp_server.py`:
- `search_kb(query, top_k)`
- `get_ticket_info(ticket_id)`
- `check_access_permission(access_level, requester_role, is_emergency)`
- `create_ticket(priority, title, description)`

Evidence tool-call: trace `run_20260414_153618.json` ghi `mcp_tools_used` có `check_access_permission` với input level 3, emergency=true.

---

## 2. Quyết định kỹ thuật quan trọng nhất

**Quyết định:** chọn **rule-based routing có `route_reason` bắt buộc** thay vì để LLM classifier quyết định tuyến ngay từ Sprint 1.

**Bối cảnh vấn đề:** Trong Day 08, cùng một pipeline monolith khiến nhóm khó biết lỗi nằm ở retrieval, policy hay synthesis. Khi refactor sang Day 09, câu hỏi đầu tiên là “để supervisor tự suy luận bằng LLM hay đóng khung bằng luật định tuyến trước”.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| LLM classifier routing | Linh hoạt với phrasing lạ | Thêm 1 call LLM, khó deterministic, khó debug khi route sai |
| Rule-based keyword + risk flag | Nhanh, dễ kiểm thử, route_reason minh bạch | Có thể miss intent nếu từ khóa không phủ đủ |

**Phương án đã chọn và lý do:**
Nhóm chọn rule-based cho vòng lặp đầu vì mục tiêu chính của lab là orchestration + observability. Với rule-based, mọi route đều để lại dấu vết giải thích rõ và tái lập được. Điều này phù hợp Sprint 1-2 khi cần làm ổn định graph trước, sau đó mới cân nhắc nâng cấp classifier.

**Bằng chứng từ trace/code:**

```text
run_20260414_153616.json
route_reason: "task contains policy/access keyword"
workers_called: ["policy_tool_worker", "retrieval_worker", "synthesis_worker"]

run_20260414_153619.json
route_reason: "unknown error code + risk_high → human review"
workers_called: ["human_review", "retrieval_worker", "synthesis_worker"]
```

Hai trace trên cho thấy lý do route đọc được ngay, giúp xác định nhanh khi nào supervisor chọn policy flow và khi nào đẩy HITL.

---

## 3. Kết quả grading questions

**Trạng thái hiện tại:** tại thời điểm viết report nhóm chưa chốt `grading_questions.json` final run để tính điểm raw chính thức 96-point rubric. Nhóm dùng 4 trace kiểm thử đại diện trong `artifacts/traces` để tự đánh giá trước grading.

**Tổng điểm raw ước tính:** chưa khóa chính thức (N/A).  
**Proxy quality từ 4 trace test:**
- Avg confidence: 0.75 (0.9, 0.9, 0.9, 0.3)
- Avg latency: 2,656 ms
- MCP usage rate: 1/4 = 25%
- HITL trigger rate: 1/4 = 25%

**Câu xử lý tốt nhất (trên test run):**
- Tương đương q13 (Level 3 + P1 khẩn cấp) qua trace `run_20260414_153618.json`.
- Điểm mạnh: route đúng sang policy_tool, có gọi MCP `check_access_permission`, và synthesis trả quy trình nhiều bước có nguồn `access_control_sop.txt`.

**Câu fail/partial điển hình:**
- Trường hợp mã lỗi không có trong KB (`run_20260414_153619.json`) trả abstain đúng hướng nhưng `supervisor_route` cuối cùng bị ghi đè thành `retrieval_worker` sau khi đi qua `human_review`.  
Root cause: trạng thái route sau HITL chưa giữ được “route gốc”, gây nhiễu khi phân tích routing distribution.

**gq07 (abstain):** chiến lược của nhóm là ưu tiên “không đủ thông tin” thay vì đoán. Logic này đã thể hiện ở query lỗi lạ với confidence 0.3 và answer abstain.

**gq09 (multi-hop):** nhóm đã có khung gọi 2 worker trong các câu khó (policy_tool + retrieval + synthesis). Tuy nhiên cần chạy đúng bộ grading để xác nhận full/partial theo rubric 16 điểm.

---

## 4. So sánh Day 08 vs Day 09 — Quan sát của nhóm

**Metric thay đổi rõ nhất:** khả năng debug theo tuyến xử lý. Day 09 có `route_reason`, `workers_called`, `mcp_tools_used`, `history`, nên truy lỗi theo từng node thay vì đọc cả pipeline.

**Số liệu Day 09 từ 4 trace gần nhất:**
- Avg latency: 2,656 ms
- Avg confidence: 0.75
- Route observed: retrieval flow, policy flow, human_review flow

**Day 08 baseline:** nhóm chưa đóng gói số đo chuẩn trong cùng phiên chạy, nên chưa điền delta số học chính xác. Dù vậy, về mặt thao tác debug, Day 09 giảm đáng kể thời gian khoanh vùng lỗi do trace có cấu trúc.

**Điều bất ngờ nhất:** câu query policy có thể nhanh hơn truy vấn retrieval thuần khi cache/embedding đã nóng (1,804 ms so với 7,027 ms ở trace đầu). Điều này cho thấy warm-up và thứ tự chạy ảnh hưởng mạnh tới latency.

**Trường hợp multi-agent chưa giúp:** với câu quá ngắn/đơn giản (fact retrieval), thêm nhiều node có thể tạo overhead orchestration mà không tăng chất lượng answer tương ứng.

---

## 5. Phân công và đánh giá nhóm

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Bùi Trọng Anh | `graph.py`, supervisor routing, `eval_trace.py`, tổng hợp docs/report nhóm | 1, 4 |
| Nguyễn Bằng Anh | `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py`, alignment contracts | 2 |
| Đỗ Thị Thùy Trang | `mcp_server.py`, tích hợp call tool trong policy flow, schema tool | 3 |

**Điều nhóm làm tốt:** giao module tách biệt theo sprint nên ít xung đột merge; trace được lưu đều, có đủ evidence để viết report theo rubric.

**Điểm chưa tốt:** thiếu một lượt freeze tiêu chuẩn trace field trước khi chạy nhiều test, dẫn đến inconsistency nhỏ ở `supervisor_route` sau HITL.

**Nếu làm lại:** nhóm sẽ khóa “trace contract” sớm hơn (schema cố định + script validate), rồi mới mở rộng logic worker để giảm rework lúc cuối buổi.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì?

Nhóm sẽ ưu tiên 2 việc: (1) thêm evaluator tự động chấm raw theo `grading_criteria` để biết ngay câu nào full/partial/zero; (2) sửa flow HITL để tách `initial_supervisor_route` và `effective_route` nhằm tránh ghi đè route khi qua `human_review`. Cả hai cải tiến đều xuất phát từ trace thực tế: đã thấy route-history rõ nhưng thống kê route cuối còn nhiễu trong case ERR khẩn cấp.
