# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Bùi Trọng Anh  
**Vai trò trong nhóm:** Supervisor Owner + Trace & Docs Owner  
**Ngày nộp:** 2026-04-14  

---

## 1. Tôi phụ trách phần nào?

Phần tôi chịu trách nhiệm chính là orchestration và observability, cụ thể là file `graph.py` và `eval_trace.py`. Ở `graph.py`, tôi thiết kế `AgentState` để dữ liệu chạy xuyên suốt các node và xây `supervisor_node()` để quyết định route, thêm `route_reason`, `risk_high`, `needs_tool`, `hitl_triggered`. Tôi cũng dựng `human_review_node()` làm điểm chặn HITL cho các task có dấu hiệu rủi ro cao (ví dụ chứa `err-` + `khẩn cấp`).

Bên cạnh graph, tôi làm phần đánh giá ở `eval_trace.py`: chạy bộ câu hỏi, lưu trace, thống kê các metric như `routing_distribution`, `avg_confidence`, `avg_latency_ms`, `mcp_usage_rate`, `hitl_rate`. Việc này kết nối trực tiếp với phần workers của bạn Nguyễn Bằng Anh và phần MCP của bạn Trang vì dữ liệu từ worker/tool đều được thu lại ở trace để phân tích.

Cách phần của tôi kết nối với nhóm: supervisor phải route đúng thì worker mới chạy đúng nhiệm vụ; trace phải đủ trường thì nhóm mới chứng minh được logic kỹ thuật trong báo cáo. Nếu phần graph hoặc trace không ổn định, cả nhóm bị block ở bước debug và viết docs.

Bằng chứng rõ nhất là các trace `run_20260414_153616.json`, `run_20260414_153618.json`, `run_20260414_153619.json` đều có `route_reason` và `workers_called`, phản ánh đúng mục tiêu tôi đặt ra khi thiết kế state và history.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** tôi chọn routing rule-based bằng keyword + risk flag thay vì LLM classifier trong supervisor.

Ngay từ đầu tôi có hai hướng: (1) gọi thêm một LLM để phân loại intent rồi route; (2) dùng luật rõ ràng theo từ khóa domain (`refund`, `level 3`, `access`, `p1`, `err-`) và gắn `route_reason` cố định. Tôi chọn hướng (2) vì mục tiêu của lab này là khả năng kiểm soát và debug, không phải tối đa hóa độ thông minh của router bằng mọi giá.

Lý do cụ thể:
1. Deterministic: cùng một input thì route như nhau, dễ test unit và dễ so sánh trước/sau khi sửa.
2. Traceable: route luôn đi kèm lý do đọc được ngay, không có “black box classifier”.
3. Tiết kiệm call: không thêm một LLM hop chỉ để route trong bối cảnh thời gian lab hạn chế.

Trade-off tôi chấp nhận là phạm vi từ khóa có thể chưa phủ hết phrasing thực tế; có nguy cơ route chưa tối ưu cho câu diễn đạt lạ. Tôi chấp nhận trade-off này để đạt tính ổn định trước, rồi mới nâng cấp sau.

Bằng chứng từ trace:
- `run_20260414_153616.json`: `route_reason = "task contains policy/access keyword"`, route sang `policy_tool_worker`.
- `run_20260414_153618.json`: `route_reason = "task contains policy/access keyword | risk_high flagged"`, thể hiện đồng thời intent + risk.
- `run_20260414_153619.json`: `route_reason = "unknown error code + risk_high → human review"`, kích hoạt đúng nhánh HITL.

Với tôi, 3 trace này xác nhận quyết định routing rule-based đã tạo được hành vi nhất quán và có thể giải thích.

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** ban đầu trace khó dùng để debug vì chưa ghi rõ đường đi của pipeline theo từng node.

**Symptom:** khi câu trả lời chưa đúng, nhóm không biết bắt đầu kiểm tra từ đâu. Chỉ nhìn final answer thì không phân biệt được supervisor route sai hay worker xử lý sai.

**Root cause:** state ban đầu chưa có cấu trúc trace đủ chi tiết. Nếu chỉ có output cuối thì gần như quay lại mô hình monolith của Day 08 về mặt debug.

**Cách sửa của tôi:**
1. Bổ sung `history` và `workers_called` dạng append để ghi lại toàn bộ path.
2. Bổ sung trường quyết định của supervisor: `supervisor_route`, `route_reason`, `risk_high`, `needs_tool`.
3. Đảm bảo sau `run_graph()` có `latency_ms` và lưu trace theo `run_id`.

**Bằng chứng trước/sau:**
- Sau sửa, trace `run_20260414_153618.json` có đủ chuỗi:
  - `[supervisor] ...`
  - `[policy_tool_worker] ...`
  - `[retrieval_worker] ...`
  - `[synthesis_worker] ...`
  - `[graph] completed ...`
- Trong case lỗi lạ `run_20260414_153619.json`, tôi thấy rõ HITL đã kích hoạt (`hitl_triggered = true`) và route_reason liên quan `err-`.

Nhờ vậy, thời gian khoanh vùng lỗi giảm rõ: từ kiểu “đọc hết pipeline” sang “đọc trace rồi vào đúng node cần sửa”.

---

## 4. Tôi tự đánh giá đóng góp của mình

Điểm tôi làm tốt nhất là chuẩn hóa luồng orchestration và chuẩn trace để cả nhóm nói chuyện trên cùng một “ngôn ngữ dữ liệu”. Tôi cũng giữ nhịp tích hợp giữa code chạy được và docs/report có evidence, tránh tình trạng viết báo cáo cảm tính.

Điểm tôi làm chưa tốt là chưa khóa sớm semantics của một số field route sau nhánh HITL. Trong `run_20260414_153619.json`, `supervisor_route` cuối cùng bị ghi đè sang `retrieval_worker`, khiến thống kê distribution có thể bị nhiễu nếu không đọc kỹ history.

Nhóm phụ thuộc vào tôi ở phần orchestration và trace contract. Nếu phần này không ổn thì worker đúng cũng khó chứng minh.

Ngược lại, tôi phụ thuộc vào thành viên worker/MCP để supervisor có thể route vào các node thực sự hữu ích, không chỉ route đúng nhưng output nghèo nàn.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi sẽ sửa và chuẩn hóa route-state thành 2 trường tách biệt: `initial_supervisor_route` và `effective_execution_route`. Lý do là trace ở case ERR khẩn cấp cho thấy route ban đầu là `human_review` nhưng route cuối bị đè, làm giảm chất lượng phân tích routing metrics. Với thay đổi này, cả debug lẫn chấm điểm phần routing sẽ minh bạch hơn.
