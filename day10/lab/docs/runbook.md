# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

- User / Agent trả lời "14 ngày làm việc" cho câu hỏi về refund window.
- Agent trả lời "10 ngày phép năm" cho nhân viên dưới 3 năm kinh nghiệm.
- Freshness check báo FAIL (dữ liệu quá 24h).

---

## Detection

- **Metric**: `quarantine_records` tăng bất thường (có thể do format nguồn thay đổi).
- **Expectation Fail**: `expectation[refund_no_stale_14d_window] FAIL` báo hiệu pipeline halt do dữ liệu bẩn.
- **Eval**: `hits_forbidden=yes` trong `artifacts/eval/before_after_eval.csv`.
- **Freshness**: Log pipeline báo `freshness_check=FAIL`.

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | Xem `latest_exported_at` có bị stale không. |
| 2 | Mở `artifacts/quarantine/*.csv` | Kiểm tra lý do `reason` (sai format ngày, version cũ). |
| 3 | Chạy `python eval_retrieval.py` | Xác nhận xem model có bị "mồi" bởi dữ liệu stale trong top-k không. |
| 4 | Kiểm tra log pipeline | Xem bước nào bị Halt hoặc Warn. |

---

## Mitigation

1.  **Rerun pipeline**: Nếu là lỗi tạm thời do file bẩn, fix file raw và rerun.
2.  **Rollback embed**: Nếu data mới làm hỏng vector db, quay lại bản manifest "tốt" gần nhất.
3.  **Update SLA**: Nếu dữ liệu thực tế chậm hơn SLA (do ngày lễ), điều chỉnh `FRESHNESS_SLA_HOURS` trong `.env`.
4.  **Bypass (Sprint 3 demo only)**: Sử dụng `--skip-validate` nếu muốn ignore Halt (không khuyến khích trên production).

---

## Prevention

1.  **Thêm Expectation**: Cài đặt thêm các rule kiểm tra PII (Email) và Terminology để nâng cao chất lượng.
2.  **Alerting**: Tích hợp Slack alert khi `freshness_check=FAIL` hoặc pipeline Halt.
3.  **Data Contract Enforcement**: Yêu cầu team nguồn tuân thủ đúng format ISO cho `effective_date`.
