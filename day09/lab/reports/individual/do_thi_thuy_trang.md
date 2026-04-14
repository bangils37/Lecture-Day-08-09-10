# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Đỗ Thị Thùy Trang  
**Vai trò trong nhóm:** MCP Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ  

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi phụ trách việc phát triển và tích hợp **MCP Server (Model Context Protocol)** - thành phần giúp Agent kết nối với các hệ thống dữ liệu động bên ngoài.
- File chính: [mcp_server.py](file:///d:/VinUni_AIThucChien/Lecture-Day-08-09-10/day09/lab/mcp_server.py).
- Tôi đã hiện thực hóa 3 công cụ (tools) quan trọng: `search_kb`, `get_ticket_info` (Jira mock), và `check_access_permission`.
- Tôi cũng phụ trách việc tích hợp các tool này vào `policy_tool_worker.py` của Bằng Anh.

Công việc của tôi mở rộng khả năng của RAG. Thay vì chỉ tìm kiếm file tĩnh, nhờ có MCP, Agent có thể kiểm tra xem một ticket cụ thể đang ở trạng thái nào hoặc khách hàng có quyền truy cập Level 3 hay không một cách thực tế.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Thiết kế interface **`dispatch_tool`** trung tâm để xử lý mọi yêu cầu gọi công cụ.

**Lý do:**
Ban đầu, tôi dự định viết các hàm công cụ rời rạc. Tuy nhiên, tôi nhận thấy nếu để Worker Agent gọi thẳng hàm logic sẽ rất khó để:
1.  **Trace log**: Chúng ta cần ghi lại chính xác tên tool, input/output vào `AgentState` để Trace Owner (Anh) có thể phân tích.
2.  **Xử lý lỗi**: Nếu một tool bị lỗi (ví dụ không tìm thấy ticket ID), ta cần trả về mã lỗi JSON thay vì để chương trình crash.

Tôi quyết định tạo một dispatcher trung tâm:
`def dispatch_tool(self, tool_name: str, arguments: Dict) -> Dict:`
Hàm này sẽ chịu trách nhiệm ánh xạ tên tool (string) vào hàm thực thi tương ứng, thực hiện validate tham số và bọc kết quả vào một cấu trúc JSON thống nhất.

**Bằng chứng:**
Trong `mcp_server.py`:
```python
def dispatch_tool(self, tool_name: str, arguments: Dict) -> Dict:
    # Logic validate and route tool call
    ...
```
Trace [run_20260414_143408.json] cho thấy `mcp_tools_used` được ghi lại chi tiết: tool `check_access_permission` đã được gọi với input `{level: 3}` và trả về danh sách `Line Manager, IT Security` một cách minh bạch.

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** **Worker gọi Tool với sai định dạng tham số dẫn đến kết quả trả về rỗng.**

**Symptom:** Trong câu hỏi về ticket P1-LATEST, Policy Worker gọi tool `get_ticket_info` nhưng luôn nhận về lỗi "Ticket not found", dù trong data mock đã có ticket này.

**Root cause:** 
Policy Worker trích xuất ticket ID từ query đôi khi có dấu ngoặc hoặc khoảng trắng dư thừa. Trong khi tool `get_ticket_info` của tôi yêu cầu so khớp chính xác (exact match) chuỗi ID.

**Cách sửa:**
- Tôi đã thêm bước **Sanitize Input** ngay tại MCP Server. Trước khi search, ID sẽ được `.strip().upper()`.
- Tôi cũng cập nhật logic search để nếu không tìm thấy exact match, tool sẽ thử dùng regex để tìm các ID tương tự trong database mock.

**Bằng chứng:** Sau khi sửa, các câu hỏi về thông tin ticket (như q11) đã trả về đúng trạng thái "In Progress" thay vì báo lỗi không tìm thấy.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tổ chức code MCP sạch sẽ và theo chuẩn module. Các tools tôi viết có tính tái sử dụng cao và dễ dàng debug thông qua logs.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Tôi chưa triển khai được cơ chế **Authentication** thật cho MCP server, hiện tại mới chỉ là mock data trả về trực tiếp.

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu MCP của tôi không chạy ổn định, Policy Worker sẽ không có dữ liệu để ra quyết định, dẫn đến Agent chỉ có thể trả lời các câu hỏi từ tài liệu tĩnh, làm mất đi tính "thông minh" của hệ thống Multi-agent.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ implement thêm tool **`send_notification`** để Agent có thể thực sự thực hiện hành động (Action-oriented) như gửi email báo cáo escalation cho Line Manager khi phát hiện sự cố P1 quá hạn xử lý.

---
*Lưu tại: `reports/individual/do_thi_thuy_trang.md`*
