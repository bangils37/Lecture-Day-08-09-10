# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Đỗ Thị Thùy Trang  
**Vai trò trong nhóm:** MCP Owner  
**Ngày nộp:** 2026-04-14  

---

## 1. Tôi phụ trách phần nào?

Phần tôi phụ trách là lớp MCP integration, tập trung ở file `mcp_server.py` và điểm nối vào `workers/policy_tool.py`. Mục tiêu của tôi là chuyển mô hình gọi tool từ hard-code trực tiếp sang interface thống nhất kiểu MCP: discover tool schema, dispatch tool bằng tên + input, trả output có cấu trúc để worker ghi trace được.

Trong `mcp_server.py`, tôi define `TOOL_SCHEMAS` cho từng tool với input/output schema rõ ràng, rồi map `TOOL_REGISTRY` để `dispatch_tool()` xử lý chuẩn hóa call. Tôi implement 4 tool:
1. `search_kb(query, top_k)`
2. `get_ticket_info(ticket_id)`
3. `check_access_permission(access_level, requester_role, is_emergency)`
4. `create_ticket(priority, title, description)`

Tôi cũng thêm dữ liệu mock thực tế cho ticket/access rules để test Sprint 3 mà không phụ thuộc hạ tầng ngoài.

Ở phía worker, tôi phối hợp để policy worker gọi `_call_mcp_tool(...)` và ghi log vào `mcp_tools_used` gồm: `tool`, `input`, `output`, `timestamp`, `error`. Cấu trúc này rất quan trọng vì giảng viên chấm Day 09 không chỉ nhìn answer mà còn nhìn trace có thể hiện việc gọi tool thật hay không.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** tôi chọn thiết kế MCP theo hướng “schema-first + dispatch layer” thay vì gọi thẳng function tool rải rác trong worker.

Có 2 hướng triển khai:
1. Worker import trực tiếp từng function tool và gọi ad-hoc.
2. Tạo một lớp dispatch thống nhất nhận `tool_name` + `tool_input`, kèm schema để validate và log.

Tôi chọn hướng (2) vì các lý do:
- Dễ mở rộng: thêm tool mới chỉ cần thêm schema + registry, worker không cần sửa nhiều.
- Dễ trace: mọi tool call có format thống nhất, thuận tiện phân tích và chấm điểm.
- Dễ nâng cấp: sau lab có thể thay mock dispatcher bằng HTTP/MCP server thật mà không phá API của worker.

Trade-off là tốn công upfront để định nghĩa schema và xử lý lỗi đầu vào ngay từ đầu, nhưng đổi lại kiến trúc sạch hơn cho các sprint sau.

Bằng chứng là trace `run_20260414_153618.json` có object `mcp_tools_used` đầy đủ:
- `tool`: `check_access_permission`
- `input`: level 3, emergency true
- `output`: required approvers, emergency override, notes
- `timestamp`: có thời điểm gọi cụ thể

Đây là dấu hiệu hệ MCP integration hoạt động đúng trong flow thật, không chỉ mock tĩnh trên giấy.

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** mismatch tham số đầu vào khi gọi tool check access từ policy worker.

**Symptom:** tool-call có thể fail hoặc trả output không như mong đợi khi key input giữa worker và tool không đồng nhất (ví dụ worker dùng key ngắn/khác tên schema trong server).

**Root cause:** thời điểm đầu phần worker và phần MCP được phát triển song song, chưa có điểm kiểm tra contract chung nên key naming bị lệch.

**Cách sửa:**
1. Chuẩn hóa schema ở `TOOL_SCHEMAS` để rõ tên trường input chuẩn.
2. Trong `dispatch_tool()`, thêm bắt lỗi `TypeError` và trả về schema tương ứng để dễ debug ngay tại trace.
3. Đồng bộ lại phần gọi trong policy flow để input mapping khớp với tool implementation.

**Bằng chứng trước/sau:**
- Sau khi đồng bộ, trace `run_20260414_153618.json` ghi tool call thành công và trả `required_approvers` gồm `Line Manager`, `IT Admin`, `IT Security`.
- Không còn trạng thái tool-call rỗng hay crash toàn pipeline ở case access policy.

Việc sửa lỗi này giúp policy worker có dữ liệu thật từ tool thay vì chỉ dựa vào suy luận từ văn bản, đặc biệt hữu ích cho câu hỏi liên quan emergency access và approval chain.

---

## 4. Tôi tự đánh giá đóng góp của mình

Tôi làm tốt ở phần tạo giao diện tool nhất quán, giúp phần policy gọi MCP có cấu trúc và dễ theo dõi. Tôi cũng ưu tiên khả năng debug bằng cách ghi đầy đủ log tool-call thay vì chỉ lưu kết quả cuối.

Điểm tôi cần cải thiện là hoàn thiện hơn nhánh “server thật” (HTTP hoặc thư viện MCP chuẩn) để tách hẳn khỏi in-process mock. Hiện tại kiến trúc đã chuẩn bị sẵn, nhưng triển khai còn ở mức phù hợp lab.

Nhóm phụ thuộc vào tôi ở phần tool integration vì đây là yêu cầu cốt lõi của Sprint 3. Nếu MCP không hoạt động, flow policy sẽ mất lợi thế so với retrieval thuần.

Ngược lại, tôi phụ thuộc vào supervisor route đúng và worker policy gọi tool đúng thời điểm, nếu không thì tool tốt cũng không được dùng trong trace.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi sẽ chuyển từ in-process dispatch sang một MCP server chạy độc lập (FastAPI hoặc library MCP), giữ nguyên contract tool hiện tại. Lý do là trace đã cho thấy case access policy hưởng lợi rõ từ tool-call, nên bước tiếp theo hợp lý là làm transport thật để kiểm thử lỗi mạng, timeout, retry và quan sát được hành vi gần production hơn.
