# Báo Cáo Cá Nhân — Lab Day 10

**Họ và tên:** Bùi Trọng Anh  
**MSSV:** AICB-P1-002 (Giả định)  
**Vai trò:** Ingestion / Monitoring / Docs Owner  
**Ngày:** 2026-04-15  

---

## 1. Phần phụ trách cụ thể

Trong bài Lab Day 10, tôi đảm nhận vai trò **Ingestion Owner** và **Monitoring Owner**. Công việc chính của tôi bao gồm:
- Thiết lập pipeline cơ sở (`etl_pipeline.py`) và xử lý luồng dữ liệu thô từ CSV.
- Triển khai hệ thống logging và tạo file manifest (`manifest_<run_id>.json`) sau mỗi lần chạy pipeline để phục vụ cho observability.
- Phụ trách module **Monitoring** với `monitoring/freshness_check.py`, kiểm tra tính tươi mới của dữ liệu so với SLA 24h.
- Quản lý và hoàn thiện các tài liệu kiến trúc, data contract và runbook cho nhóm.

## 2. Một quyết định kỹ thuật tiêu biểu

Tôi đã quyết định sử dụng cấu trúc **Manifest file** làm trung tâm cho việc theo dõi trạng thái pipeline thay vì chỉ dựa vào log. 
**Lý do**: File manifest chứa đầy đủ các metadata quan trọng (`run_id`, `latest_exported_at`, `cleaned_records`, `status`) dưới định dạng JSON, giúp các hệ thống khác (như `freshness_check`) có thể đọc và xử lý một cách dễ dàng và chính xác mà không cần parse log thô. Điều này tạo nền tảng cho việc mở rộng observability và tự động hóa cảnh báo trong tương lai.

## 3. Một sự cố / anomaly đã xử lý

**Phát hiện**: Khi chạy pipeline trên Windows, tôi gặp lỗi `UnicodeEncodeError` khi in các ký tự đặc biệt (như mũi tên `→`) ra console, làm pipeline bị dừng đột ngột.
**Fix**: Tôi đã thực hiện chuẩn hóa lại các chuỗi in ra log, thay thế các ký tự unicode phức tạp bằng các ký tự ASCII an toàn hơn (ví dụ: `→` thành `->`) và đảm bảo các file được mở với encoding `utf-8`.
**Evidence**: Sau khi fix, pipeline chạy mượt mà và in được đầy đủ thông tin `WARN: expectation failed but --skip-validate -> continuing embed (demo mode).` mà không gây crash.

## 4. Bằng chứng Before / After

Trích xuất từ log `freshness_check`:
```json
{"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 119.182, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}
```
Dựa vào số liệu này, tôi đã cấu hình lại hệ thống để phát hiện dữ liệu cũ và cập nhật vào Runbook quy trình xử lý khi `freshness_check=FAIL`.

## 5. Cải tiến trong 2 giờ tới

Nếu có thêm 2 giờ, tôi sẽ triển khai **Freshness Check ở 2 Boundary** (Ingest và Publish). Hiện tại chúng tôi mới chỉ đo độ trễ từ nguồn đến lúc publish. Việc đo thêm thời gian từ lúc file raw được tạo đến lúc ingest sẽ giúp xác định chính xác điểm nghẽn (bottleneck) nằm ở khâu export dữ liệu hay ở khâu xử lý pipeline, từ đó tối ưu hóa được SLA cho toàn hệ thống.
