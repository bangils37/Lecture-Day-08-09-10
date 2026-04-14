# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Bùi Trọng Anh  
**Vai trò trong nhóm:** Supervisor & Trace/Docs Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ  

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án này, tôi đảm nhận hai vai trò quan trọng liên kết toàn bộ hệ thống: **Supervisor Owner** và **Trace & Docs Owner**.
- Về mặt lập trình, tôi phụ trách file [graph.py](file:///d:/VinUni_AIThucChien/Lecture-Day-08-09-10/day09/lab/graph.py), xây dựng khung điều phối bằng LangGraph và thiết lập logic routing tại `supervisor_node`.
- Về mặt quản lý chất lượng, tôi phát triển [eval_trace.py](file:///d:/VinUni_AIThucChien/Lecture-Day-08-09-10/day09/lab/eval_trace.py) để tự động hóa việc kiểm thử và phân tích 15 câu hỏi evaluation.

Công việc của tôi là đảm bảo "luồng thông tin" (flow) luôn đi đúng hướng. Nếu supervisor route sai, các worker chuyên biệt của Nguyễn Bàng Anh hay Trang sẽ không bao giờ nhận được task để xử lý.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Sử dụng **LangGraph** để xây dựng kiến trúc Multi-Agent thay vì chỉ dùng chuỗi logic `if/else` đơn giản.

**Lý do:**
Ban đầu nhóm định dùng Python thuần để điều phối. Tuy nhiên, tôi nhận thấy LangGraph mang lại 3 ưu điểm vượt trội:
1.  **Tính minh bạch (Observability)**: LangGraph cho phép chúng ta lưu lại `history` của từng bước nhảy (hop) một cách tự động vào `AgentState`. Điều này cực kỳ quan trọng để tạo ra các file trace đúng chuẩn SCORING.md.
2.  **Khả năng mở rộng**: Việc thêm một node `human_review` (HITL) cho các mã lỗi lạ (`ERR-xxx`) trở nên rất đơn giản mà không làm rối logic chính.
3.  **Quản lý State tập trung**: Toàn bộ dữ liệu từ `retrieved_chunks` đến `mcp_tools_used` được quản lý trong một `TypedDict` thống nhất, giúp việc tổng hợp ở Synthesis worker (do Bằng Anh làm) trở nên dễ dàng.

**Bằng chứng:**
Trong `graph.py`, tôi đã implement logic routing:
```python
if any(kw in task_lower for kw in ["refund", "access"]):
    return "policy_tool_worker"
```
Trace [run_20260414_143408.json] cho thấy Supervisor nhận diện từ khóa "cấp quyền" và route chính xác sang Policy Tool với lý do `task contains policy/access keyword`.

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** **Trình phân tích Trace bị crash trên Windows do lỗi Encoding.**

**Symptom:** Khi tôi chạy lệnh `python eval_trace.py --analyze` để tổng hợp báo cáo sau khi đã có 15 file trace, script báo lỗi `UnicodeDecodeError`.

**Root cause:** 
Mặc định hàm `open()` trên Windows dùng encoding CP1252. Trong khi đó, các câu trả lời tiếng Việt từ Gemini 2.0 lại được lưu dưới dạng UTF-8. Khi script cố gắng đọc hàng loạt file JSON để tính toán latency và routing distribution, nó gặp các ký tự đặc biệt và crash.

**Cách sửa:**
Tôi đã rà soát toàn bộ các điểm ghi và đọc file trong `graph.py` và `eval_trace.py`, ép kiểu encoding về `utf-8` và cấu hình `json.dump` với `ensure_ascii=False`.

**Bằng chứng:** Sau khi sửa, tôi đã hoàn thiện được bảng thống kê `eval_report.json` với đầy đủ các metrics: trung bình trễ 13.4s, tỉ lệ route đúng 100%.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Thiết kế hệ thống tracing chuyên nghiệp. Nhờ bộ trace log chi tiết mà nhóm đã không bị mất điểm ở các mục "route_reason" và "workers_called" trong SCORING.md.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Tôi chưa tối ưu được độ trễ của Graph. Hiện tại mỗi request mất khoảng 13s, một phần do overhead của chính framework LangGraph và việc Supervisor phân tích keyword còn thủ công.

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu không có khung Graph của tôi, các Worker của Bằng Anh sẽ không có nơi để "đậu" vào. Nếu không có script evaluation của tôi, nhóm sẽ không thể nộp log grading đúng hạn 17:00.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ xây dựng một giao diện **Web UI** bằng Streamlit để demo trực quan luồng suy nghĩ của Agent, cho phép giảng viên nhìn thấy các nodes sáng lên khi Agent gọi MCP tool trong thời gian thực.

---
*Lưu tại: `reports/individual/bui_trong_anh.md`*
