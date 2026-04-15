# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Lab Group (Trang & Team)  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Trang | Ingestion / Raw Owner | trang@lab.local |
| Team | Cleaning & Quality Owner | team@lab.local |
| Team | Embed & Idempotency Owner | team@lab.local |
| Team | Monitoring / Docs Owner | team@lab.local |

**Ngày nộp:** 2026-04-15  
**Run ID (Sprint 2):** `sprint2`  
**Artifact path:** `artifacts/manifests/manifest_sprint2.json`

---

## 1. Pipeline tổng quan

**Luồng ETL:**
```
data/raw/policy_export_dirty.csv (10 records)
  ↓ [Load & Ingest]
  ↓ [Cleaning: 6 rules baseline + 3 new]
  ↓ [Validation: 8 expectations — 6 baseline + 2 new]
  ↓ [Embed Chroma (idempotent upsert)]
  ↓ PIPELINE_OK
artifacts/
  ├── cleaned/cleaned_sprint2.csv (6 records)
  ├── quarantine/quarantine_sprint2.csv (4 records)
  ├── manifests/manifest_sprint2.json (run metadata)
  └── logs/run_sprint2*.log (lifecycle events)
```

**Lệnh chạy:**
```bash
python etl_pipeline.py run --run-id sprint2
# Exit code: 0 (PIPELINE_OK)
```

**Metrics:**
- Raw: 10 → Cleaned: 6 → Quarantine: 4
- Expectations: 8/8 OK (0 halt failures)
- Chroma collection `day10_kb`: 6 chunks upserted

---

## 2. Cleaning Rules — 3 New Rules (Chống Trivial)

| Rule | Chi tiết | Metric Impact | Chứng minh |
|------|---------|-----------------|-----------|
| **R1: `invalid_exported_at_format`** | Validate exported_at phải ISO 8601 datetime (`YYYY-MM-DDTHH:MM:SS`). Quarantine nếu format sai. | Baseline data: 0 violations (tất cả `2026-04-10T08:00:00`). **Sẽ demo khi inject "2026-04-10 08:00:00"** → +1 quarantine expected | Demo trong Sprint 3 |
| **R2: `has_suspicious_keywords`** | Filter chunks chứa `[deprecated]`, `[todo]`, `[fixme]`, `[redacted]` → quarantine nếu tìm thấy. | Baseline: 0 violations (không có marker). **Sẽ demo khi inject "[deprecated] old version"** → +1 quarantine expected | Demo trong Sprint 3 |
| **R3: `normalize_chunk_text`** | Trim & collapse whitespace (múltiple spaces/newlines → 1 space). Prevent false negatives từ duplicate detection. | **Tác động đo được:** Row 1 & 2 có text giống nhau nhưng row 2 có spacing khác → sau normalize, được coi là duplicate, quarantine. Quarantine count không tăng (vì đã đo được trong dedupe logic) nhưng **reduce false positive**. | Row 2: duplicate_chunk_text (detected after normalize) ✓ |

**Baseline rules (6):** allowlist doc_id, normalize effective_date, stale HR policy, missing chunk_text, dedupe, fix refund 14→7

---

## 3. Quality Expectations — 2 New Expectations

| Expectation | Type | Result | Detail |
|-------------|------|--------|--------|
| **E7 (NEW): `no_exported_at_in_future`** | warn | PASS ✓ | future_records=0 (không có timestamp > now) |
| **E8 (NEW): `no_effective_date_far_future`** | warn | PASS ✓ | far_future_records=0 (không có date > +365 days) |
| E1–E6 (baseline) | 4 halt + 2 warn | ALL PASS ✓ | 0 violations |

**Tổng:** 8/8 OK, 0 halt failures

---

## 4. Before/After Evidence (Sprint 3)

*Pending injection corruption test. Will update with:*
- `artifacts/eval/eval_retrieval.csv` (baseline quality)
- Injected corruption + re-eval to show degradation
- Recovery after fix

---

## 5. Embedding Idempotency

**Strategy:** Upsert by `chunk_id` + prune stale vectors
- Chroma collection: `day10_kb` (persistent)
- Upsert count: 6 chunks
- Prune removed: 0 (no prior run to clean yet)

**Test plan (Sprint 3):** Run pipeline twice with same `run_id`, verify no vector duplication.

---

## 6. Risk & Next Steps

- [ ] Sprint 3: Inject corruption, measure eval degradation
- [ ] Sprint 3: Fill quality_report.md with run_id & interpretation
- [ ] Sprint 4: Complete architecture.md, runbook.md, individual reports

**Status:** Sprint 2 ✅ COMPLETE | Awaiting Sprint 3 injection test
