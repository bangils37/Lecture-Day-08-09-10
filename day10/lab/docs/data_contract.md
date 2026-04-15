# Data contract — Lab Day 10

> Phản ánh và đồng bộ với `contracts/data_contract.yaml`.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| policy_export_dirty.csv | CSV Reader | Sai format ngày, duplicate, version cũ | quarantine_records > 0 |
| it_helpdesk_faq | CSV Reader | Thiếu chunk_text, doc_id lạ | unknown_doc_id count |
| hr_leave_policy | CSV Reader | Version 2025 (10 ngày phép) | stale_hr_policy count |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Hash (doc_id + text + seq) |
| doc_id | string | Có | policy_refund_v4, sla_p1_2026... |
| chunk_text | string | Có | Nội dung chunk đã clean, mask PII, chuẩn hóa terminology |
| effective_date | date | Có | Định dạng ISO YYYY-MM-DD |
| exported_at | datetime | Có | Thời điểm export từ nguồn |

---

## 3. Quy tắc quarantine vs drop

Record bị flag vi phạm rules (sai ngày, version cũ, doc_id lạ) sẽ được ghi vào `artifacts/quarantine/`. Ingestion Owner (Bùi Trọng Anh) sẽ review file này hàng ngày. Nếu là record hợp lệ nhưng sai format, sẽ yêu cầu nguồn fix export. Nếu là record không cần thiết, sẽ giữ lại ở quarantine để audit.

---

## 4. Phiên bản & canonical

- **Source of truth**: File text tại `data/docs/`.
- **Refund Policy**: Bản v4 (7 ngày) là duy nhất được chấp nhận.
- **HR Policy**: Chỉ chấp nhận bản 2026 (effective_date >= 2026-01-01).
- **IT FAQ**: Yêu cầu terminology Wi-Fi và Portal viết đúng casing.
