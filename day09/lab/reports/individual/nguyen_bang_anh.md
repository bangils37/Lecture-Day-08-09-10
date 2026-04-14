# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Bằng Anh  
**Vai trò trong nhóm:** Worker Owner  
**Ngày nộp:** 2026-04-14  

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách toàn bộ tầng worker trong lab day09, gồm 3 file chính: `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py`, đồng thời phối hợp để input/output khớp contract của pipeline. Mục tiêu của tôi là mỗi worker có thể test độc lập, sau đó cắm vào graph mà không thay đổi nhiều logic lõi.

Ở retrieval, tôi xây luồng embed query -> query ChromaDB -> chuẩn hóa dữ liệu thành list chunk có `text`, `source`, `score`, `metadata`. Tôi để fallback rõ ràng khi thiếu môi trường (ví dụ chưa có sentence-transformers) để pipeline không crash cứng.

Ở policy_tool, tôi viết rule-based policy analyzer cho các ngoại lệ quan trọng của refund/access như Flash Sale, digital product, activated product, và temporal note cho đơn trước 01/02/2026. Worker này cũng ghi `policy_result` và `mcp_tools_used` để trace downstream.

Ở synthesis, tôi xây context builder từ `retrieved_chunks` + `policy_result`, gọi LLM với prompt grounded, trích `sources` và ước tính `confidence` theo chất lượng evidence. Tôi chủ động thêm logic abstain: nếu không đủ context thì confidence giảm mạnh.

Phần của tôi kết nối với supervisor ở routing đầu vào và với MCP ở tool call trong policy flow. Nếu worker không trả schema ổn định, supervisor có route đúng cũng không cứu được output.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** tôi chọn mô hình worker “ưu tiên rule-based logic + structured output” trước khi tối ưu hóa bằng LLM reasoning sâu.

Khi làm `policy_tool.py`, tôi cân nhắc 2 cách:
1. Dùng LLM làm policy judge hoàn toàn.
2. Dùng rule-based cho các business rule cứng (Flash Sale, digital, activated, emergency access), sau đó để synthesis diễn đạt tự nhiên.

Tôi chọn cách (2) vì rule policy của bài khá rõ, và yêu cầu quan trọng là reproducibility. Nếu dùng LLM toàn phần ngay từ đầu, cùng một câu có thể ra khác nhau theo prompt và model state, khó so sánh trong trace. Với structured output, tôi đảm bảo trường `policy_applies`, `policy_name`, `exceptions_found` luôn có shape giống nhau.

Trade-off chấp nhận:
- Rule-based có thể thiếu mềm dẻo với câu hỏi mơ hồ hoặc phrasing mới.
- Cần bảo trì danh sách keyword/exception khi domain mở rộng.

Nhưng trong phạm vi lab, quyết định này giúp tôi kiểm soát lỗi tốt hơn và phối hợp dễ hơn với teammate viết supervisor/eval.

Bằng chứng hiệu quả:
- `run_20260414_153616.json`: `policy_result.policy_applies = false`, `exceptions_found` có `flash_sale_exception`.
- `run_20260414_153618.json`: `policy_result` nêu cả note “Level 3 không emergency bypass” và nhánh escalation khẩn cấp.

Hai case này cho thấy structured policy output có tác dụng trực tiếp lên answer cuối và confidence.

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** trước khi chỉnh worker chain, policy flow có thể thiếu context retrieval trong một số câu policy, dẫn đến answer thiên về suy đoán hoặc quá ngắn.

**Symptom:** khi route vào `policy_tool_worker` mà `retrieved_chunks` chưa có sẵn, policy logic chỉ dựa trên task text làm output thiếu evidence. Điều này làm synthesis khó trích nguồn rõ ràng.

**Root cause:** thứ tự thực thi policy và retrieval không đảm bảo mọi case đều có chunk trước khi phân tích policy.

**Cách sửa:**
1. Trong `policy_tool.run()`, nếu `chunks` rỗng và `needs_tool=True` thì gọi MCP `search_kb` để nạp context trước khi phân tích.
2. Giữ thiết kế graph cho phép policy flow đi qua retrieval và synthesis (`policy -> retrieval -> synthesis`) để tăng grounding.
3. Ghi rõ `mcp_tools_used` và worker history nhằm xác định lúc nào policy phân tích dựa trên context nào.

**Bằng chứng trước/sau:**
- Sau chỉnh, các trace policy như `run_20260414_153616.json` và `run_20260414_153618.json` đều có `retrieved_chunks` và `retrieved_sources` cụ thể.
- Output cuối có dẫn nguồn `policy_refund_v4.txt` hoặc `access_control_sop.txt`, thay vì trả lời trôi nổi không chứng cứ.

Nhờ sửa lỗi này, worker chain hoạt động ổn định hơn cho câu policy khó và giảm rủi ro hallucination.

---

## 4. Tôi tự đánh giá đóng góp của mình

Tôi làm tốt nhất ở việc tách rõ trách nhiệm từng worker và giữ output có cấu trúc. Điều đó giúp teammate dễ kết nối graph, trace, và report. Tôi cũng chủ động thiết kế fallback để worker không gãy toàn bộ pipeline khi thiếu dependency.

Điểm tôi còn yếu là phần chuẩn hóa score/confidence chưa thật chặt. Ví dụ hiện confidence ở nhiều trace còn cao giống nhau (0.9), chưa phản ánh hết độ khó từng câu.

Nhóm phụ thuộc vào tôi ở chỗ worker là phần xử lý nội dung cốt lõi. Nếu worker lỗi, toàn bộ graph chỉ còn là khung điều phối không tạo giá trị.

Ngược lại, tôi phụ thuộc vào supervisor logic và MCP integration để input vào worker đúng intent và có đầy đủ tool context khi cần.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi sẽ nâng cấp confidence scoring theo nhiều tín hiệu hơn (coverage nguồn, độ khớp criteria, số bước multi-hop) thay vì dựa chủ yếu vào retrieval score và abstain pattern. Lý do là các trace hiện tại có hiện tượng confidence 0.9 xuất hiện ở nhiều câu với độ khó khác nhau, làm metric chưa đủ phân biệt chất lượng thực tế.
