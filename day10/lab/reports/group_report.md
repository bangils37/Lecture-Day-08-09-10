# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Team AI Thuc Chien - Group Day 10  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Bùi Trọng Anh | Ingestion / Monitoring / Docs | 26ai.anhbt@vinuni.edu.vn |
| Đỗ Thị Thùy Trang | Cleaning & Quality Owner | 26ai.trangdtt@vinuni.edu.vn |
| Nguyễn Bằng Anh| Embed & Idempotency Owner | 26ai.anhnb@vinuni.edu.vn |

**Ngày nộp:** 2026-04-15  
**Repo:** https://github.com/bangils37/Lecture-Day-08-09-10.git

---

## 1. Pipeline tổng quan (150–200 từ)

Pipeline của chúng tôi mô phỏng quá trình xử lý dữ liệu từ các nguồn raw (CSV export từ DB/API) để đưa vào Vector Store phục vụ cho RAG Agent. Quy trình gồm 4 bước chính: Ingest -> Transform -> Quality -> Publish. Dữ liệu đầu vào được đọc từ `data/raw/policy_export_dirty.csv`, đi qua các cleaning rules để loại bỏ các records lỗi (sai format ngày, version cũ, doc_id lạ). Sau đó, bộ expectation suite sẽ kiểm tra tính toàn vẹn của dữ liệu và dừng pipeline (halt) nếu phát hiện lỗi nghiêm trọng (như stale refund window). Cuối cùng, dữ liệu được embed vào Chroma DB một cách idempotent (upsert theo chunk_id và prune các record cũ).

**Lệnh chạy một dòng:**
```bash
python etl_pipeline.py run --run-id final-report-run --raw data/raw/policy_export_dirty.csv
```

---

## 2. Cleaning & expectation (150–200 từ)

Nhóm đã kế thừa 6 baseline rules và bổ sung thêm 3 rules mới cùng 2 expectations mới để tăng cường tính bảo mật và chuẩn hóa dữ liệu IT. Các rules mới bao gồm: Standardize IT terms (wifi -> Wi-Fi), Mask PII Email (masking email cá nhân), và Ensure ending period (chuẩn hóa câu kết thúc bằng dấu chấm).

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới | Trước (Baseline) | Sau / khi inject | Chứng cứ (log / CSV / commit) |
|-------------------------|------------------|-------------------|-------------------------------|
| Rule 7: IT Terms | wifi (lowercase) | Wi-Fi (standard) | cleaned_sprint2-run-1.csv |
| Rule 8: Mask PII | admin@vinuni.edu.vn | [EMAIL] | cleaned_sprint2-run-1.csv |
| Expectation 7: No PII | 0 violations | 1 violation (halt) | expectation[no_pii_email] FAIL |
| Expectation 8: IT Terms | 0 violations | 1 violation (warn) | expectation[it_standard_terms] WARN |

**Rule chính (baseline + mở rộng):**
- Baseline: Normalization of effective_date, HR stale policy versioning, refund window fix (14 -> 7 days).
- Mở rộng: PII Email Masking, IT terminology standardization, chunk text ending period.
- **Distinction Achievement**: Chúng tôi đã chuyển đổi logic **Rule Versioning** từ hard-coded (một ngày cố định trong code) sang **dynamic configuration**. Cutoff date cho chính sách HR được đọc từ biến môi trường `HR_LEAVE_POLICY_CUTOFF` (mặc định 2026-01-01), cho phép linh hoạt thay đổi chính sách mà không cần sửa đổi mã nguồn.

**Ví dụ 1 lần expectation fail:**
Khi chạy inject data với một email thật trong `chunk_text`, expectation `no_pii_email` đã báo FAIL (halt). Chúng tôi đã xử lý bằng cách thêm rule Mask PII trước bước validation để đảm bảo email luôn được che chắn trước khi embed.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

**Kịch bản inject:**
Chúng tôi đã sử dụng tham số `--no-refund-fix --skip-validate` trên bộ dữ liệu dirty để mô phỏng trường hợp pipeline bị lỗi hoặc cố ý bypass các bước kiểm tra chất lượng. Trong kịch bản này, một chunk chứa thông tin "14 ngày làm việc" vẫn được đưa vào Vector Store.

**Kết quả định lượng:**
- **Trước (Inject Bad)**: Câu hỏi `q_refund_window` trả về `hits_forbidden=yes`. Dù top-1 có thể đúng, nhưng trong top-3 vẫn tồn tại chunk lỗi "14 ngày", gây rủi ro Agent trả lời sai nếu model bị mồi bởi context bẩn.
- **Sau (Cleaned)**: Sau khi chạy pipeline chuẩn, `hits_forbidden=no`. Chunk 14 ngày đã được fix thành 7 ngày, giúp kết quả retrieval sạch hoàn toàn và Agent luôn trả lời đúng SLA hiện hành.

---

## 4. Freshness & monitoring (100–150 từ)

Chúng tôi chọn SLA là 24 giờ cho các tài liệu policy. Freshness được đo tại bước publish dựa trên trường `exported_at` của record mới nhất.
- **FAIL**: Khi dữ liệu cũ hơn 24h so với thời điểm run.
- **PASS**: Khi dữ liệu được cập nhật trong vòng 24h.
Trên dữ liệu lab, hệ thống báo FAIL vì dữ liệu export từ ngày 2026-04-10, điều này giúp chúng tôi nhận diện dữ liệu đang bị "stale" và cần yêu cầu export mới từ hệ thống nguồn.

---

## 5. Liên hệ Day 09 (50–100 từ)

Dữ liệu sau khi embed vào collection `day10_kb` có thể được Agent ở Day 09 sử dụng trực tiếp thông qua retrieval. Việc chuẩn hóa format ngày và fix các lỗi versioning giúp Agent không bị nhầm lẫn giữa các phiên bản chính sách khác nhau (như số ngày phép năm 10 vs 12).

---

## 6. Rủi ro còn lại & việc chưa làm

- Cần thêm rule cho các loại PII khác như số điện thoại hoặc mã nhân viên.
- SLA freshness hiện tại mới chỉ đo ở điểm publish, chưa đo ở điểm ingest (delay từ nguồn đến pipeline).
- Chưa có hệ thống auto-retrain hoặc auto-alert qua Slack/Email.
