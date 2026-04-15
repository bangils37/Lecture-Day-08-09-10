# Quality report — Lab Day 10 (nhóm)

**run_id:** clean-final-run  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (Baseline) | Sau (Final) | Ghi chú |
|--------|-----------------|-------------|---------|
| raw_records | 10 | 10 | policy_export_dirty.csv |
| cleaned_records | 6 | 6 | 4 records bị quarantine |
| quarantine_records | 4 | 4 | Do sai doc_id, sai date format, version cũ |
| Expectation halt? | No | No | Pipeline PASS |

---

## 2. Before / after retrieval (bắt buộc)

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước (Inject Bad):**  
`top1_preview`: Yêu cầu được gửi trong vòng 7 ngày làm việc...  
`hits_forbidden`: **yes** (vì trong top-k vẫn còn chunk 14 ngày)

**Sau (Cleaned):**  
`top1_preview`: Yêu cầu được gửi trong vòng 7 ngày làm việc...  
`hits_forbidden`: **no** (chunk 14 ngày đã được fix thành 7 ngày)

**Versioning HR:** `q_leave_version`  
**Trước:**  
`top1_preview`: (Có thể ra bản 10 ngày nếu không clean)  
**Sau:**  
`top1_preview`: Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026.  
`top1_doc_expected`: **yes**

---

## 3. Freshness & monitor

Kết quả `freshness_check=FAIL`.  
**Giải thích**: Dữ liệu mẫu `exported_at` là 2026-04-10, đã quá 24h so với thời điểm hiện tại. SLA 24h là hợp lý cho dữ liệu policy, nhưng do đây là dữ liệu lab tĩnh nên việc FAIL là dự kiến.

---

## 4. Corruption inject (Sprint 3)

Chúng tôi đã cố ý chạy pipeline với tham số `--no-refund-fix --skip-validate` trên file `policy_export_dirty.csv`.  
- **Kết quả**: Expectation `refund_no_stale_14d_window` báo **FAIL (halt)**.
- **Phát hiện**: Dù pipeline vẫn chạy tiếp nhờ `--skip-validate`, nhưng kết quả eval cho thấy `hits_forbidden=yes`, chứng minh rủi ro khi bỏ qua bước validation.

---

## 5. Hạn chế & việc chưa làm

- Chưa tích hợp Slack notification thực tế cho freshness alert.
- PII masking mới chỉ áp dụng cho Email, có thể mở rộng cho số điện thoại.
- Một số chunk text vẫn còn khá ngắn (trigger `warn`).
