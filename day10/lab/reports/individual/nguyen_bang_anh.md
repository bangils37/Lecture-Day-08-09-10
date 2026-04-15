# Báo Cáo Cá Nhân — Lab Day 10

**Họ và tên:** Nguyễn Bằng Anh  
**MSSV:** 2A202600136
**Vai trò:** Cleaning & Quality Owner  
**Ngày:** 2026-04-15  

---

## 1. Phần phụ trách cụ thể

Trong bài Lab Day 10, tôi chịu trách nhiệm chính về tầng **Transformation** và **Quality Assurance**. Các file và hàm tôi trực tiếp triển khai bao gồm:
- `transform/cleaning_rules.py`: Mở rộng 3 rules mới (Rule 7, 8, 9) để chuẩn hóa terminology, mask PII Email và chuẩn hóa dấu câu.
- `quality/expectations.py`: Mở rộng 2 expectations mới (E7, E8) để kiểm tra PII và thuật ngữ IT.
- Quản lý file `artifacts/quarantine/` và định nghĩa các logic phân loại records lỗi.

## 2. Một quyết định kỹ thuật tiêu biểu

Tôi đã quyết định đặt mức độ nghiêm trọng (**severity**) của expectation `no_pii_email` là **halt**. 
**Lý do**: Việc để lộ Email cá nhân trong Vector Store là một vi phạm nghiêm trọng về GDPR và chính sách bảo mật của VinUni. Nếu pipeline không thể mask được email, nó nên dừng lại ngay lập tức để Ingestion Owner kiểm tra lại nguồn dữ liệu hoặc logic regex, thay vì tiếp tục embed và phục vụ cho Agent (vì một khi đã embed, việc thu hồi dữ liệu bẩn sẽ khó khăn hơn). Quyết định này giúp bảo vệ hệ thống khỏi các rủi ro pháp lý ngay từ tầng dữ liệu.

## 3. Một sự cố / anomaly đã xử lý

**Phát hiện**: Trong quá trình chạy Sprint 2, tôi phát hiện một số chunk từ IT FAQ có chứa từ "wifi" viết thường, dẫn đến việc tìm kiếm không đồng nhất khi Agent sử dụng các query viết hoa/thường khác nhau.
**Fix**: Tôi đã thêm Rule 7 sử dụng `re.sub` với flag `IGNORECASE` để chuẩn hóa tất cả các biến thể của "wifi" thành "Wi-Fi". 
**Evidence**: Trước khi fix, record số 2 trong `policy_export_dirty.csv` chứa "wifi". Sau khi fix, trong file `cleaned_clean-final-run.csv`, nội dung đã được chuyển thành "Wi-Fi.".

## 4. Bằng chứng Before / After

Trích log từ file `artifacts/eval/before_after_eval_good.csv`:
```csv
question_id,question,top1_preview,hits_forbidden
q_refund_window,Khách hàng có bao nhiêu ngày...?,...7 ngày làm việc...,no
```
So với file `before_after_eval_bad.csv` (khi chưa fix refund window):
```csv
question_id,question,top1_preview,hits_forbidden
q_refund_window,Khách hàng có bao nhiêu ngày...?,...7 ngày làm việc...,yes
```

## 5. Cải tiến trong 2 giờ tới

Nếu có thêm 2 giờ, tôi sẽ tích hợp thư viện **Pydantic** để validate schema thay cho việc parse dictionary thủ công. Việc dùng Pydantic sẽ giúp bắt lỗi kiểu dữ liệu (e.g. `effective_date` không phải date object) một cách tự động và cung cấp thông báo lỗi chi tiết hơn cho từng field, giúp bước "Symptom -> Detection" trong Runbook trở nên nhanh chóng hơn.
